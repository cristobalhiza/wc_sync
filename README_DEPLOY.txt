====================================================
README – Sincronización WooCommerce → MySQL → Excel
====================================================

¿QUÉ HACE?
----------
• Baja los pedidos nuevos de WooCommerce y los guarda en la base MySQL del hosting.
• Expone una vista para Excel: vw_excel_feed_full (1 fila por línea de producto, 1 por Despacho, 1 por IVA).
• Excel solo tiene que actualizar para ver los pedidos.

CONTENIDO DE LA CARPETA C:\wc_sync
----------------------------------
• wc_sync.exe           → ejecutable que hace la sincronización
• .env                  → credenciales y ajustes (editar si cambian)
• run_sync.bat          → ejecuta el EXE y deja registro en sync.log
• README.txt            → este archivo
• (opcional) Pedidos.xlsx → archivo de Excel con la conexión ya armada

REQUISITOS EN LA OFICINA (UNA SOLA VEZ)
---------------------------------------
1) Autorizar IP pública de la oficina en el hosting:
   - Hostinger → Remote MySQL → Add IP (buscar en Google “what is my ip”).
2) Instalar el driver MySQL para Excel:
   - Comprobar si Excel es 64 o 32 bits (Archivo → Cuenta → Acerca de Excel).
   - Instalar “MySQL Connector/ODBC 8.x” del mismo bitness.
3) (Opcional) Crear DSN ODBC “WC_Export”:
   - ODBC (64 o 32 bits según Excel) → DSN de sistema → Agregar → MySQL ODBC 8 Unicode.
   - Server: <HOST_MYSQL_DEL_HOSTING> (NO “localhost”).
   - Port: 3306
   - User: u174573775_wc_export
   - Password: <tu_clave>
   - Database: u174573775_wc_export
   - Test → “Connection successful”.

PRIMERA CONFIGURACIÓN
---------------------
1) Copiar la carpeta completa C:\wc_sync (con wc_sync.exe y .env).
2) Abrir C:\wc_sync\.env y revisar:
   WC_BASE_URL=...
   WC_KEY=...
   WC_SECRET=...
   DB_HOST=<host mysql del hosting>
   DB_PORT=3306
   DB_USER=u174573775_wc_export
   DB_PASS=<tu_clave>
   DB_NAME=u174573775_wc_export
   LOOKBACK_DAYS=3
3) Probar manualmente:
   - Doble clic en run_sync.bat (o ejecutar wc_sync.exe).
   - Ver “Sync OK” en pantalla y/o revisar C:\wc_sync\sync.log.

CÓMO USAR (DÍA A DÍA)
---------------------
• Abrir el archivo de Excel (Pedidos.xlsx) y pulsar “Datos → Actualizar todo”.
• Si pide usuario/clave, usar las de MySQL (las del .env).
• La tabla mostrará campos: fecha_pedido, cliente, objeto, cantidad, valor_precio.
  (Puede ocultarse order_id, order_date, line_type, line_id si no se usan.)

PROGRAMAR ACTUALIZACIÓN AUTOMÁTICA
----------------------------------
1) Abrir “Programador de tareas” → Crear tarea básica → nombre: Woo Sync.
2) Desencadenador: Diario → Repetir cada 1 hora (duración: 1 día).
3) Acción: Iniciar un programa:
   - Programa: C:\wc_sync\run_sync.bat
   - Iniciar en: C:\wc_sync
4) Opciones avanzadas:
   - Ejecutar tanto si el usuario inició sesión como si no.
   - Ejecutar con los privilegios más altos.
   - Si se omite un inicio programado, ejecutar lo antes posible.
5) Excel: en la consulta, marcar “Actualizar al abrir” y (opcional) “cada 60 min”.

VER REGISTROS / LOGS
--------------------
• Archivo: C:\wc_sync\sync.log
• Ejemplo de salida:
  === Woo Sync Summary ===
  Orders fetched: 3
  New lines     : +8 (por tipo: IVA:+1, PRODUCT:+6, SHIPPING:+1)
  After (new)   : 2025-08-30 00:26:11 UTC
  ========================

RECUPERAR HISTÓRICO (SI FALTÓ ALGO)
-----------------------------------
1) En phpMyAdmin, ejecutar:
   UPDATE wc_sync_state SET last_after='AAAA-MM-DD 00:00:00';
2) Volver a correr run_sync.bat.
   (No se duplica gracias al “UPSERT”.)

TROUBLESHOOTING
---------------
• Excel/EXE dice “Access denied”:
  - La IP pública del PC no está autorizada en Remote MySQL.
  - Usuario/clave o host en .env incorrectos.

• Excel no muestra el conector MySQL:
  - Instalar MySQL Connector/ODBC 8.x del mismo bitness que Excel.
  - Alternativa: Datos → Desde ODBC y usar DSN “WC_Export”.

• No hay pedidos nuevos:
  - Es normal si no hubo ventas. El log mostrará “Orders fetched: 0”.

• Decimales en valores:
  - La vista vw_excel_feed_full ya redondea a enteros. Aun así,
    en Excel formatear “Número” con 0 decimales (estético).

• Productos “descriptivos” con valor 0:
  - Es normal en packs/bundles. Si no quiere verse, usar una vista filtrada
    (consultar con quien implementó el sistema).

CAMBIAR CONTRASEÑA / MANTENIMIENTO
----------------------------------
• Cambiar clave en el hosting y en C:\wc_sync\.env (DB_PASS).
• Si se actualiza el EXE: reemplazar C:\wc_sync\wc_sync.exe.
• Si se cambia el host MySQL: actualizar DB_HOST en .env.
• Backups: el hosting suele incluir backups automáticos de la BD.

CONSULTA SQL QUE USA EXCEL (REFERENCIA)
---------------------------------------
SELECT
  o.order_id,
  o.order_date,
  DATE(o.order_date)                AS fecha_pedido,
  o.customer_name                   AS cliente,
  CASE
    WHEN l.line_type='SHIPPING' THEN 'Despacho'
    WHEN l.line_type='IVA'      THEN 'IVA'
    ELSE l.item_name
  END                               AS objeto,
  l.quantity                        AS cantidad,
  CAST(ROUND(l.value_net,0) AS SIGNED) AS valor_precio
FROM wc_order_lines l
JOIN wc_orders o ON o.order_id = l.order_id;

SOPORTE INTERNO
---------------
• Para revisar logs: C:\wc_sync\sync.log
• Para forzar una actualización: doble clic en C:\wc_sync\run_sync.bat
• Para problemas de conexión: verificar Remote MySQL (IP pública), host,
  usuario y contraseña en .env

Errores comunes y soluciones
Conexión MySQL

1045 Access denied
Causa: IP pública no autorizada en Remote MySQL, usuario/clave mal o host mal.
Solución: autoriza IP en Hostinger → Remote MySQL; revisa DB_HOST, DB_USER, DB_PASS en .env.

2003/Can’t connect / timeout
Causa: DB_HOST incorrecto, puerto bloqueado, DNS/firewall local.
Solución: usa el host exacto que da Hostinger (no “localhost” desde tu PC); verifica puerto 3306; prueba ping/nslookup.

Authentication plugin not supported
Causa: plugin no incluido.
Solución: recompilar con los --hidden-import y en db() usar
auth_plugin="mysql_native_password" (o caching_sha2_password).

Failed to execute script / Failed raising error (PyInstaller)
Causa: locales/plugins de mysql-connector faltan.
Solución: usa los --hidden-import que te di y/o use_pure=True en mysql.connect().

1062 Duplicate entry (no debería pasar)
Causa: claves de líneas repetidas (muy raro).
Solución: revisa que PRIMARY KEY (order_id, line_type, line_id) sea correcto y que line_id viene de Woo (lo es).

Zona horaria / datos duplicados por rango
Causa: watermark.
Solución: UPDATE wc_sync_state SET last_after='AAAA-MM-DD 00:00:00'; y re-ejecuta; no duplica por el UPSERT.

WooCommerce API

401/403
Causa: keys inválidas o permisos insuficientes.
Solución: crea nuevas keys “Read” en Woo → Ajustes → Avanzado → REST API; revisa WC_BASE_URL, WC_KEY, WC_SECRET.

429 Too Many Requests
Causa: rate limit.
Solución: deja el per_page=100 y el sleep(0.2) como está; si ocurre, sube a sleep(0.5).

SSL/Cert
Causa: certificados raros.
Solución: usualmente no aplica en Hostinger; si aparece, podemos forzar verify=False temporalmente (no recomendado).

Excel / ODBC

No aparece MySQL ODBC en ODBC Administrator
Causa: no instalado o bitness incorrecto.
Solución: instala MySQL Connector/ODBC 8.x del mismo bitness que Excel (64/32). Abre el ODBC que corresponda.

Pide credenciales todo el tiempo
Solución: guarda las credenciales en la conexión o usa DSN del Sistema.

No se actualiza
Solución: ejecuta run_sync.bat (ver sync.log) y luego Actualizar todo en Excel. Configura “Actualizar al abrir”.

Windows / Tareas

La tarea no corre
Causa: “Start in” vacío, falta de permisos, ruta mala.
Solución: en la tarea, “Programa” = C:\wc_sync\run_sync.bat, “Iniciar en” = C:\wc_sync, “Ejecutar con los privilegios más altos”.

SmartScreen/Antivirus bloquea EXE
Solución: clic derecho → Propiedades → Desbloquear; agrega exclusión en el antivirus para C:\wc_sync\.

Operativa

Valores con decimales
Solución: la vista vw_excel_feed_full ya usa ROUND(...,0). En Excel, formato Número 0 decimales.

Filas de producto con valor 0 (packs)
Solución: usa una vista alternativa que filtre esos productos (te pasé vw_excel_feed_final), o filtra en Excel.

FIN

