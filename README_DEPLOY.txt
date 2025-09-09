# --- README: Instrucciones de Despliegue y Compilaci	ilde{}^{n} --- 

Sigue estos pasos para configurar el entorno de desarrollo y compilar el archivo `cultivarte_wc_sync.exe` desde cero.

## Prerrequisitos

-   Python 3.8 o superior instalado. Aseg	ilde{}^{n}rate de marcar la opci	ilde{}^{n} "Add Python to PATH" durante la instalaci	ilde{}^{n} .
-   Acceso a la base de datos MySQL.
-   Credenciales de la API de WooCommerce (Consumer Key y Consumer Secret).

## Paso 1: Configurar el Archivo de Entorno (.env)

1.  En la carpeta del proyecto, busca el archivo `.env.example`.
2.  Haz una copia de este archivo y ren	ilde{}^{n}mbrala a `.env`.
3.  Abre el archivo `.env` con un editor de texto y rellena **todos** los valores con tus credenciales reales. Por ejemplo:

    ```ini
    # Configuraci	ilde{}^{n} de la Base de Datos (usada por ambos scripts)
    DB_HOST=tu_servidor_mysql.com
    DB_USER=tu_usuario_bd
    DB_PASS=tu_contrase	ilde{}^{n}a_bd
    DB_NAME=tu_nombre_bd
    DB_PORT=3306

    # Configuraci	ilde{}^{n} de WooCommerce (usada por sync_wc_orders.py)
    WC_BASE_URL="https://tu-tienda.com"
    WC_KEY="ck_xxxxxxxxxxxx"
    WC_SECRET="cs_xxxxxxxxxxxx"
    LOOKBACK_DAYS=3

    # Configuraci	ilde{}^{n} del Archivo Excel (usada por sync_clientes.py)
    EXCEL_FILE_PATH="C:\\Ruta\\Completa\\A\\Tu\\Pedidos CultivArte.xlsx"
    EXCEL_SHEET_NAME="Clientes Web"
    ```
    **IMPORTANTE**: En la ruta del archivo Excel, usa doble barra invertida (`\\`) como se muestra en el ejemplo.

## Paso 2: Instalar Dependencias

1.  Abre una terminal (PowerShell o CMD) en la carpeta del proyecto (`C:\wc_sync`).
2.  **Crea y activa un entorno virtual**. Esto a	ilde{}^{n}sla las dependencias del proyecto:
    ```bash
    # Crear el entorno
    python -m venv .venv

    # Activar el entorno (en PowerShell)
    .\.venv\Scripts\Activate.ps1
    ```
3.  Instala todas las librer	ilde{}^{n}as necesarias con un solo comando:
    ```bash
    pip install -r requirements.txt
    ```

## Paso 3: Preparar la Base de Datos

1.  Aseg	ilde{}^{n}rate de que el entorno virtual est	ilde{}^{n} activo.
2.  Ejecuta el script de configuraci	ilde{}^{n} de la base de datos **una sola vez**:
    ```bash
    python setup_database.py
    ```
    Este comando crear	ilde{}^{n} las tablas `clientes`, `ultima_sincronizacion`, `wc_orders`, `wc_customers`, etc., si no existen.

## Paso 4: Compilar el Ejecutable (.exe)

1.  Con el entorno virtual a	ilde{}^{n}n activo, ejecuta el siguiente comando en una sola l	ilde{}^{n}nea para construir el archivo `.exe`:
    ```bash
    pyinstaller --onefile --windowed --name cultivarte_wc_sync --hidden-import=mysql.connector.locales.eng.client_error --hidden-import=mysql.connector.locales.eng.numbers --hidden-import=mysql.connector.plugins.mysql_native_password --hidden-import=mysql.connector.plugins.caching_sha2_password main.py
    ```
2.  Una vez finalizado el proceso, encontrar	ilde{}^{n}s el ejecutable en una nueva carpeta llamada `dist`. El archivo se llamar	ilde{}^{n} `cultivarte_wc_sync.exe`.

## Paso 5: Despliegue Final

1.  Copia el archivo `cultivarte_wc_sync.exe` desde la carpeta `dist` a la carpeta principal del proyecto (`C:\wc_sync`).
2.  Aseg	ilde{}^{n}rate de que el archivo `.env` que configuraste en el Paso 1 est	ilde{}^{n} en la misma carpeta que el `.exe`.
3.  
    **¡Listo!** Ahora puedes ejecutar el `.exe` directamente o programarlo como una Tarea Programada de Windows.