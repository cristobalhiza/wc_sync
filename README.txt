# Build Local del Sincronizador de WooCommerce

Esta guía explica cómo compilar el archivo `sync_wc_orders.py` en un ejecutable `.exe` autocontenido.

## 1. Archivo `requirements.txt`

Asegúrate de que el archivo `requirements.txt` en la raíz del proyecto contenga lo siguiente:

```text
requests
mysql-connector-python
python-dotenv
pyinstaller

2. Comando de Compilación (PowerShell)

Abre una terminal de PowerShell, navega a la carpeta del proyecto y ejecuta los siguientes comandos. El       ` (acento grave) se usa para dividir el comando en múltiples líneas para mayor legibilidad.
PowerShell

# Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Compilar con PyInstaller
pyinstaller --onefile --name cultivarte_wc_sync `
  --hidden-import=mysql.connector.locales.eng.client_error `
  --hidden-import=mysql.connector.locales.eng.numbers `
  --hidden-import=mysql.connector.plugins.mysql_native_password `
  --hidden-import=mysql.connector.plugins.caching_sha2_password `
  sync_wc_orders.py

El archivo final cultivarte_wc_sync.exe se encontrará en la carpeta dist.

3. Vista SQL para Excel (Referencia)

Esta es la vista que el script asume que existe en la base de datos para que Excel pueda consumir los datos de forma limpia.
SQL

CREATE OR REPLACE VIEW vw_excel_feed_full AS
SELECT
  o.order_id,
  o.order_date,
  DATE(o.order_date)                            AS fecha_pedido,
  o.customer_name                               AS cliente,
  CASE
    WHEN l.line_type='SHIPPING' THEN 'Despacho'
    WHEN l.line_type='IVA'      THEN 'IVA'
    ELSE l.item_name
  END                                           AS objeto,
  l.quantity                                    AS cantidad,
  CAST(ROUND(l.value_net, 0) AS SIGNED)         AS valor_precio
FROM wc_order_lines l
JOIN wc_orders o ON o.order_id = l.order_id;