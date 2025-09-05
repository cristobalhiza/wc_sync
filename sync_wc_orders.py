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

# Diccionario para traducir códigos de comunas a nombres legibles
COMUNA_MAP = {
    "CL-RM": "Santiago",
    'CL_100': 'Algarrobo', 'CL_101': 'Alhué', 'CL_102': 'Alto Biobío', 'CL_103': 'Alto del Carmen',
    'CL_104': 'Alto Hospicio', 'CL_105': 'Ancud', 'CL_106': 'Andacollo', 'CL_107': 'Angol',
    'CL_108': 'Antártica', 'CL_109': 'Antofagasta', 'CL_110': 'Antuco', 'CL_111': 'Arauco',
    'CL_112': 'Arica', 'CL_113': 'Aysén', 'CL_114': 'Buin', 'CL_115': 'Bulnes', 'CL_116': 'Cabildo',
    'CL_117': 'Cabo de Hornos', 'CL_118': 'Cabrero', 'CL_119': 'Calama', 'CL_120': 'Calbuco',
    'CL_121': 'Caldera', 'CL_122': 'Calera de Tango', 'CL_123': 'Calle Larga', 'CL_124': 'Camarones',
    'CL_125': 'Camiña', 'CL_126': 'Canela', 'CL_127': 'Cañete', 'CL_128': 'Carahue', 'CL_129': 'Cartagena',
    'CL_130': 'Casablanca', 'CL_131': 'Castro', 'CL_132': 'Catemu', 'CL_133': 'Cauquenes',
    'CL_134': 'Cerrillos', 'CL_135': 'Cerro Navia', 'CL_136': 'Chaitén', 'CL_137': 'Chanco',
    'CL_138': 'Chañaral', 'CL_139': 'Chépica', 'CL_140': 'Chiguayante', 'CL_141': 'Chile Chico',
    'CL_142': 'Chillán', 'CL_143': 'Chillán Viejo', 'CL_144': 'Chimbarongo', 'CL_145': 'Cholchol',
    'CL_146': 'Chonchi', 'CL_147': 'Cisnes', 'CL_148': 'Cobquecura', 'CL_149': 'Cochamó',
    'CL_150': 'Cochrane', 'CL_151': 'Codegua', 'CL_152': 'Coelemu', 'CL_153': 'Coihueco',
    'CL_154': 'Coinco', 'CL_155': 'Colbún', 'CL_156': 'Colchane', 'CL_157': 'Colina',
    'CL_158': 'Collipulli', 'CL_159': 'Coltauco', 'CL_160': 'Combarbalá', 'CL_161': 'Concepción',
    'CL_162': 'Conchalí', 'CL_163': 'Concón', 'CL_164': 'Constitución', 'CL_165': 'Contulmo',
    'CL_166': 'Copiapó', 'CL_167': 'Coquimbo', 'CL_168': 'Coronel', 'CL_169': 'Corral',
    'CL_170': 'Coyhaique', 'CL_171': 'Cunco', 'CL_172': 'Curacautín', 'CL_173': 'Curacaví',
    'CL_174': 'Curaco de Vélez', 'CL_175': 'Curanilahue', 'CL_176': 'Curarrehue', 'CL_177': 'Curepto',
    'CL_178': 'Curicó', 'CL_179': 'Dalcahue', 'CL_180': 'Diego de Almagro', 'CL_181': 'Doñihue',
    'CL_182': 'El Bosque', 'CL_183': 'El Carmen', 'CL_184': 'El Monte', 'CL_185': 'El Quisco',
    'CL_186': 'El Tabo', 'CL_187': 'Empedrado', 'CL_188': 'Ercilla', 'CL_189': 'Estación Central',
    'CL_190': 'Florida', 'CL_191': 'Freire', 'CL_192': 'Freirina', 'CL_193': 'Fresia',
    'CL_194': 'Frutillar', 'CL_195': 'Futaleufú', 'CL_196': 'Futrono', 'CL_197': 'Galvarino',
    'CL_198': 'General Lagos', 'CL_199': 'Gorbea', 'CL_200': 'Graneros', 'CL_201': 'Guaitecas',
    'CL_202': 'Hijuelas', 'CL_203': 'Hualaihué', 'CL_204': 'Hualañé', 'CL_205': 'Hualpén',
    'CL_206': 'Hualqui', 'CL_207': 'Huara', 'CL_208': 'Huasco', 'CL_209': 'Huechuraba',
    'CL_210': 'Illapel', 'CL_211': 'Independencia', 'CL_212': 'Iquique', 'CL_213': 'Isla de Maipo',
    'CL_214': 'Isla de Pascua', 'CL_215': 'Juan Fernández', 'CL_216': 'La Calera', 'CL_217': 'La Cisterna',
    'CL_218': 'La Cruz', 'CL_219': 'La Estrella', 'CL_220': 'La Florida', 'CL_221': 'La Granja',
    'CL_222': 'La Higuera', 'CL_223': 'La Ligua', 'CL_224': 'La Pintana', 'CL_225': 'La Reina',
    'CL_226': 'La Serena', 'CL_227': 'La Unión', 'CL_228': 'Lago Ranco', 'CL_229': 'Lago Verde',
    'CL_230': 'Laguna Blanca', 'CL_231': 'Laja', 'CL_232': 'Lampa', 'CL_233': 'Lanco',
    'CL_234': 'Las Cabras', 'CL_235': 'Las Condes', 'CL_236': 'Lautaro', 'CL_237': 'Lebu',
    'CL_238': 'Licantén', 'CL_239': 'Limache', 'CL_240': 'Linares', 'CL_241': 'Litueche',
    'CL_242': 'Llanquihue', 'CL_243': 'Llay Llay', 'CL_244': 'Lo Barnechea', 'CL_245': 'Lo Espejo',
    'CL_246': 'Lo Prado', 'CL_247': 'Lolol', 'CL_248': 'Loncoche', 'CL_249': 'Longaví',
    'CL_250': 'Lonquimay', 'CL_251': 'Los Álamos', 'CL_252': 'Los Andes', 'CL_253': 'Los Ángeles',
    'CL_254': 'Los Lagos', 'CL_255': 'Los Muermos', 'CL_256': 'Los Sauces', 'CL_257': 'Los Vilos',
    'CL_258': 'Lota', 'CL_259': 'Lumaco', 'CL_260': 'Machalí', 'CL_261': 'Macul', 'CL_262': 'Máfil',
    'CL_263': 'Maipú', 'CL_264': 'Malloa', 'CL_265': 'Marchihue', 'CL_266': 'María Elena',
    'CL_267': 'María Pinto', 'CL_268': 'Mariquina', 'CL_269': 'Maule', 'CL_270': 'Maullín',
    'CL_271': 'Mejillones', 'CL_272': 'Melipeuco', 'CL_273': 'Melipilla', 'CL_274': 'Molina',
    'CL_275': 'Monte Patria', 'CL_276': 'Mostazal', 'CL_277': 'Mulchén', 'CL_278': 'Nacimiento',
    'CL_279': 'Nancagua', 'CL_280': 'Natales', 'CL_281': 'Navidad', 'CL_282': 'Negrete',
    'CL_283': 'Ninhue', 'CL_284': 'Nogales', 'CL_285': 'Nueva Imperial', 'CL_286': 'Ñiquén',
    'CL_287': 'Ñuñoa', 'CL_288': 'O\'Higgins', 'CL_289': 'Olivar', 'CL_290': 'Ollagüe',
    'CL_291': 'Olmué', 'CL_292': 'Osorno', 'CL_293': 'Ovalle', 'CL_294': 'Padre Hurtado',
    'CL_295': 'Padre las Casas', 'CL_296': 'Paihuano', 'CL_297': 'Paillaco', 'CL_298': 'Paine',
    'CL_299': 'Palena', 'CL_300': 'Palmilla', 'CL_301': 'Panguipulli', 'CL_302': 'Panquehue',
    'CL_303': 'Papudo', 'CL_304': 'Paredones', 'CL_305': 'Parral', 'CL_306': 'Pedro Aguirre Cerda',
    'CL_307': 'Pelarco', 'CL_308': 'Pelluhue', 'CL_309': 'Pemuco', 'CL_310': 'Pencahue',
    'CL_311': 'Penco', 'CL_312': 'Peñaflor', 'CL_313': 'Peñalolén', 'CL_314': 'Peralillo',
    'CL_315': 'Perquenco', 'CL_316': 'Petorca', 'CL_317': 'Peumo', 'CL_318': 'Pica',
    'CL_319': 'Pichidegua', 'CL_320': 'Pichilemu', 'CL_321': 'Pinto', 'CL_322': 'Pirque',
    'CL_323': 'Pitrufquén', 'CL_324': 'Placilla', 'CL_325': 'Portezuelo', 'CL_326': 'Porvenir',
    'CL_327': 'Pozo Almonte', 'CL_328': 'Primavera', 'CL_329': 'Providencia', 'CL_330': 'Puchuncaví',
    'CL_331': 'Pucón', 'CL_332': 'Pudahuel', 'CL_333': 'Puente Alto', 'CL_334': 'Puerto Montt',
    'CL_335': 'Puerto Octay', 'CL_336': 'Puerto Varas', 'CL_337': 'Pumanque', 'CL_338': 'Punitaqui',
    'CL_339': 'Punta Arenas', 'CL_340': 'Puqueldón', 'CL_341': 'Purén', 'CL_342': 'Purranque',
    'CL_343': 'Putaendo', 'CL_344': 'Putre', 'CL_345': 'Puyehue', 'CL_346': 'Queilén',
    'CL_347': 'Quellón', 'CL_348': 'Quemchi', 'CL_349': 'Quilaco', 'CL_350': 'Quilicura',
    'CL_351': 'Quilleco', 'CL_352': 'Quillón', 'CL_353': 'Quillota', 'CL_354': 'Quilpué',
    'CL_355': 'Quinchao', 'CL_356': 'Quinta de Tilcoco', 'CL_357': 'Quinta Normal',
    'CL_358': 'Quintero', 'CL_359': 'Quirihue', 'CL_360': 'Rancagua', 'CL_361': 'Ránquil',
    'CL_362': 'Rauco', 'CL_363': 'Recoleta', 'CL_364': 'Renaico', 'CL_365': 'Renca',
    'CL_366': 'Rengo', 'CL_367': 'Requínoa', 'CL_368': 'Retiro', 'CL_369': 'Rinconada',
    'CL_370': 'Río Bueno', 'CL_371': 'Río Claro', 'CL_372': 'Río Hurtado', 'CL_373': 'Río Ibáñez',
    'CL_374': 'Río Negro', 'CL_375': 'Río Verde', 'CL_376': 'Romeral', 'CL_377': 'Saavedra',
    'CL_378': 'Sagrada Familia', 'CL_379': 'Salamanca', 'CL_380': 'San Antonio', 'CL_381': 'San Bernardo',
    'CL_382': 'San Carlos', 'CL_383': 'San Clemente', 'CL_384': 'San Esteban', 'CL_385': 'San Fabián',
    'CL_386': 'San Felipe', 'CL_387': 'San Fernando', 'CL_388': 'San Gregorio', 'CL_389': 'San Ignacio',
    'CL_390': 'San Javier', 'CL_391': 'San Joaquín', 'CL_392': 'San José de Maipo',
    'CL_393': 'San Juan de la Costa', 'CL_394': 'San Miguel', 'CL_395': 'San Nicolás',
    'CL_396': 'San Pablo', 'CL_397': 'San Pedro', 'CL_398': 'San Pedro de Atacama',
    'CL_399': 'San Pedro de la Paz', 'CL_400': 'San Rafael', 'CL_401': 'San Ramón',
    'CL_402': 'San Rosendo', 'CL_403': 'San Vicente', 'CL_404': 'Santa Bárbara', 'CL_405': 'Santa Cruz',
    'CL_406': 'Santa Juana', 'CL_407': 'Santa María', 'CL_408': 'Santiago', 'CL_409': 'Santo Domingo',
    'CL_410': 'Sierra Gorda', 'CL_411': 'Talagante', 'CL_412': 'Talca', 'CL_413': 'Talcahuano',
    'CL_414': 'Taltal', 'CL_415': 'Temuco', 'CL_416': 'Teno', 'CL_417': 'Teodoro Schmidt',
    'CL_418': 'Tierra Amarilla', 'CL_419': 'Tiltil', 'CL_420': 'Timaukel', 'CL_421': 'Tirúa',
    'CL_422': 'Tocopilla', 'CL_423': 'Toltén', 'CL_424': 'Tomé', 'CL_425': 'Torres del Paine',
    'CL_426': 'Tortel', 'CL_427': 'Traiguén', 'CL_428': 'Treguaco', 'CL_429': 'Tucapel',
    'CL_430': 'Valdivia', 'CL_431': 'Vallenar', 'CL_432': 'Valparaíso', 'CL_433': 'Vichuquén',
    'CL_434': 'Victoria', 'CL_435': 'Vicuña', 'CL_436': 'Vilcún', 'CL_437': 'Villa Alegre',
    'CL_438': 'Villa Alemana', 'CL_439': 'Villarrica', 'CL_440': 'Viña del Mar', 'CL_441': 'Vitacura',
    'CL_442': 'Yerbas Buenas', 'CL_443': 'Yumbel', 'CL_444': 'Yungay', 'CL_445': 'Zapallar',
}

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

def crear_tabla_clientes():
    # Se añade la columna 'unidad' a la definición de la tabla
    sql = """CREATE TABLE IF NOT EXISTS wc_customers (
        email VARCHAR(255) PRIMARY KEY,
        id_cliente_wc INT,
        nombre VARCHAR(100),
        apellido VARCHAR(100),
        telefono VARCHAR(40),
        direccion VARCHAR(255),
        unidad VARCHAR(50),
        comuna VARCHAR(100),
        pais VARCHAR(60),
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )"""
    with db() as conn:
        c = conn.cursor()
        c.execute(sql)

def q_scalar(sql, params=None):
    with db() as conn:
        c = conn.cursor()
        c.execute(sql, params or ())
        row = c.fetchone()
        return row[0] if row else 0

def count_orders():
    return q_scalar("SELECT COUNT(*) FROM wc_orders")

def count_customers():
    return q_scalar("SELECT COUNT(*) FROM wc_customers")

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
        "status": "processing,completed",
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


def actualizar_o_insertar_cliente(o):
    billing = o.get("billing") or {}
    email = (billing.get("email") or "").strip()
    if not email:
        return

    direccion_calle = billing.get("address_1", "").strip()
    unidad = billing.get("address_2", "").strip()

    codigo_comuna = billing.get("state", "")
    nombre_comuna = COMUNA_MAP.get(codigo_comuna, codigo_comuna)

    sql = """INSERT INTO wc_customers
        (email, id_cliente_wc, nombre, apellido, telefono, direccion, unidad, comuna, pais)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        id_cliente_wc=VALUES(id_cliente_wc),
        nombre=VALUES(nombre),
        apellido=VALUES(apellido),
        telefono=VALUES(telefono),
        direccion=VALUES(direccion),
        unidad=VALUES(unidad),
        comuna=VALUES(comuna),
        pais=VALUES(pais)
    """
    params = (
        email,
        o.get("customer_id") or 0,
        billing.get("first_name",""),
        billing.get("last_name",""),
        billing.get("phone",""),
        direccion_calle,
        unidad,
        nombre_comuna,
        billing.get("country","")
    )
    with db() as conn:
        c = conn.cursor()
        c.execute(sql, params)


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

    crear_tabla_clientes()

    before_orders = count_orders()
    before_lines  = count_lines_total()
    before_bytype = count_lines_by_type()
    before_customers = count_customers()

    last_after_prev = get_last_after()
    newest = last_after_prev

    orders = wc_get_orders(last_after_prev)
    order_ids = []

    for o in orders:
        created_utc = parse_gmt(o.get("date_created_gmt") or o.get("date_created"))
        if created_utc > newest:
            newest = created_utc

        upsert_order(o, created_utc)
        actualizar_o_insertar_cliente(o)
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
    after_customers = count_customers()

    delta_orders = after_orders - before_orders
    delta_lines  = after_lines  - before_lines
    delta_customers = after_customers - before_customers
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
    print(f"New clients   : +{delta_customers}")
    print(f"New lines     : +{delta_lines}  (por tipo: {', '.join(f'{k}:+{v}' for k,v in delta_bytype.items())})")
    print(f"After (new)   : {watermark_new.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Elapsed       : {elapsed:.2f}s")
    print("========================")

if __name__ == "__main__":
    run()