import os, time, sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import requests
import mysql.connector as mysql
from dotenv import load_dotenv


def load_env():
    if getattr(sys, "frozen", False):
        dotenv_path = Path(sys.executable).with_name(".env")
    else:
        dotenv_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=dotenv_path)

load_env()

WC_BASE   = os.getenv("WC_BASE_URL","").rstrip("/")
WC_KEY    = os.getenv("WC_KEY")
WC_SECRET = os.getenv("WC_SECRET")

DB_CFG = dict(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT","3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    autocommit=True,
)
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS","3"))

def db():
    try:
        return mysql.connect(
            **DB_CFG,
            use_pure=True,
            auth_plugin="mysql_native_password" 
        )
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

def q_scalar(sql, params=None):
    with db() as conn:
        c = conn.cursor()
        c.execute(sql, params or ())
        row = c.fetchone()
        return row[0] if row else 0

def count_orders():
    return q_scalar("SELECT COUNT(*) FROM wc_orders")

def count_lines_total():
    return q_scalar("SELECT COUNT(*) FROM wc_order_lines")

def count_lines_by_type():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT line_type, COUNT(*) FROM wc_order_lines GROUP BY line_type")
        return {k: v for k, v in c.fetchall()}

def parse_gmt(s: str) -> datetime:
    s = (s or "").strip()
    if not s:
        return datetime.now(timezone.utc)
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_last_after() -> datetime:
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT last_after FROM wc_sync_state WHERE id=1")
        row = c.fetchone()
        if row and row[0]:
            return row[0].replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

def set_last_after(dt_aware_utc: datetime):
    dt_naive = dt_aware_utc.astimezone(timezone.utc).replace(tzinfo=None)
    with db() as conn:
        c = conn.cursor()
        c.execute("UPDATE wc_sync_state SET last_after=%s WHERE id=1", (dt_naive,))

def wc_get_orders(after_aware_utc: datetime):
    per_page = 100
    page = 1
    orders = []
    base = {
        "consumer_key": WC_KEY,
        "consumer_secret": WC_SECRET,
        "orderby": "date",
        "order": "asc",
        "status": "any",
        "per_page": per_page,
        "after": after_aware_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    while True:
        params = dict(base, page=page)
        r = requests.get(f"{WC_BASE}/wp-json/wc/v3/orders", params=params, timeout=60)
        r.raise_for_status()
        chunk = r.json()
        if not chunk:
            break
        orders.extend(chunk)
        if len(chunk) < per_page:
            break
        page += 1
        time.sleep(0.2)
    return orders

def upsert_order(o, created_aware_utc: datetime):
    sql = """INSERT INTO wc_orders
      (order_id, order_date, customer_name, status, currency, total_tax, shipping_total)
      VALUES (%s,%s,%s,%s,%s,%s,%s)
      ON DUPLICATE KEY UPDATE
       order_date=VALUES(order_date),
       customer_name=VALUES(customer_name),
       status=VALUES(status),
       currency=VALUES(currency),
       total_tax=VALUES(total_tax),
       shipping_total=VALUES(shipping_total)"""
    order_id = int(o["id"])
    created_naive = created_aware_utc.replace(tzinfo=None)

    billing = o.get("billing") or {}
    customer = f"{billing.get('first_name','').strip()} {billing.get('last_name','').strip()}".strip()
    status = o.get("status","")
    currency = o.get("currency","")

    try:
        shipping_total = Decimal(str(o.get("shipping_total","0")))
    except Exception:
        shipping_total = Decimal("0")
    if not shipping_total:
        shipping_total = sum(Decimal(str(sl.get("total","0"))) for sl in (o.get("shipping_lines") or []))

    total_tax = Decimal(str(o.get("total_tax","0")))

    with db() as conn:
        c = conn.cursor()
        c.execute(sql, (order_id, created_naive, customer, status, currency, total_tax, shipping_total))

def upsert_line(order_id, line_type, line_id, item_name, sku, qty, value_net):
    sql = """INSERT INTO wc_order_lines
      (order_id, line_type, line_id, item_name, sku, quantity, value_net)
      VALUES (%s,%s,%s,%s,%s,%s,%s)
      ON DUPLICATE KEY UPDATE
        item_name=VALUES(item_name),
        sku=VALUES(sku),
        quantity=VALUES(quantity),
        value_net=VALUES(value_net)"""
    with db() as conn:
        c = conn.cursor()
        c.execute(sql, (order_id, line_type, line_id, item_name, sku, qty, value_net))

def run():
    t0 = time.time()

    before_orders = count_orders()
    before_lines  = count_lines_total()
    before_bytype = count_lines_by_type()

    last_after_prev = get_last_after()
    newest = last_after_prev

    orders = wc_get_orders(last_after_prev)
    order_ids = []

    for o in orders:
        created_utc = parse_gmt(o.get("date_created_gmt") or o.get("date_created"))
        if created_utc > newest:
            newest = created_utc

        upsert_order(o, created_utc)
        order_ids.append(int(o["id"]))

        for li in (o.get("line_items") or []):
            upsert_line(
                order_id=int(o["id"]),
                line_type="PRODUCT",
                line_id=int(li["id"]),
                item_name=li.get("name",""),
                sku=li.get("sku",""),
                qty=Decimal(str(li.get("quantity",1))),
                value_net=Decimal(str(li.get("total","0")))
            )

        for sh in (o.get("shipping_lines") or []):
            upsert_line(
                order_id=int(o["id"]),
                line_type="SHIPPING",
                line_id=int(sh["id"]),
                item_name=(sh.get("method_title") or "Despacho"),
                sku="",
                qty=Decimal("1"),
                value_net=Decimal(str(sh.get("total","0")))
            )

        iva_total = Decimal(str(o.get("total_tax","0")))
        if iva_total != 0:
            upsert_line(
                order_id=int(o["id"]),
                line_type="IVA",
                line_id=0,
                item_name="IVA",
                sku="",
                qty=Decimal("1"),
                value_net=iva_total
            )

    if orders:
        set_last_after(newest + timedelta(seconds=1))
        watermark_new = newest + timedelta(seconds=1)
    else:
        watermark_new = last_after_prev

    after_orders = count_orders()
    after_lines  = count_lines_total()
    after_bytype = count_lines_by_type()

    delta_orders = after_orders - before_orders
    delta_lines  = after_lines  - before_lines
    types = set(before_bytype) | set(after_bytype)
    delta_bytype = {t: after_bytype.get(t,0) - before_bytype.get(t,0) for t in sorted(types)}

    elapsed = time.time() - t0

    print("=== Woo Sync Summary ===")
    print(f"After (prev)  : {last_after_prev.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Orders fetched: {len(orders)}")
    if order_ids:
        ids_list = ", ".join(str(x) for x in order_ids[:10])
        more = "" if len(order_ids) <= 10 else f" (+{len(order_ids)-10} más)"
        print(f"Order IDs     : {ids_list}{more}")
    print(f"New orders    : +{delta_orders}")
    print(f"New lines     : +{delta_lines}  (por tipo: {', '.join(f'{k}:+{v}' for k,v in delta_bytype.items())})")
    print(f"After (new)   : {watermark_new.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Elapsed       : {elapsed:.2f}s")
    print("========================")

if __name__ == "__main__":
    run()