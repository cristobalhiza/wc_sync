# --- README: Información General del Proyecto CultivArte Sync ---

## 1. Propósito del Proyecto

Este conjunto de scripts proporciona una solución integral para sincronizar datos entre múltiples fuentes para CultivArte. Sus funciones principales son:

1.  **Sincronización Bidireccional de Clientes**: Mantiene los datos de clientes actualizados entre un archivo local de Excel ("Pedidos CultivArte.xlsx") y una tabla en una base de datos MySQL. La sincronización es incremental y se basa en una columna de `ultima_modificacion` para optimizar el rendimiento.

2.  **Sincronización de Pedidos de WooCommerce**: Descarga los pedidos nuevos o modificados desde una tienda WooCommerce y los guarda en la misma base de datos MySQL, actualizando también una tabla de clientes específica de WooCommerce.

## 2. Arquitectura Modular

El proyecto está dividido en módulos para facilitar su mantenimiento y escalabilidad:

-   `main.py`: Es el corazón del proyecto. Actúa como un orquestador que ejecuta los diferentes módulos de sincronización en el orden correcto. Este es el archivo que se compila para generar el `.exe` final.

-   `sync_clientes.py`: Contiene toda la lógica para la sincronización bidireccional de clientes entre Excel y MySQL.

-   `sync_wc_orders.py`: Contiene toda la lógica para conectarse a la API de WooCommerce, descargar pedidos y guardarlos en la base de datos.

-   `setup_database.py`: Un script de utilidad que se ejecuta una sola vez para preparar la base de datos, creando todas las tablas necesarias si no existen.

## 3. Archivos de Configuración y Soporte

-   `.env`: (Debe ser creado a partir de `.env.example`) Archivo crítico que almacena de forma segura todas las credenciales de la base de datos, las claves de la API de WooCommerce y las rutas a los archivos. **Este archivo NUNCA debe compartirse.**

-   `requirements.txt`: Lista todas las librerías de Python necesarias para que el proyecto funcione.

-   `sync_general.log`: Archivo de registro (log) que se genera automáticamente. Registra cada paso del proceso de sincronización, incluyendo éxitos, advertencias y errores. Es el primer lugar donde se debe mirar si algo falla.

-   `README_DEPLOY.txt`: Contiene las instrucciones paso a paso para configurar el proyecto en una nueva máquina y compilar el archivo `.exe`.

-   `README_TEST.txt`: Proporciona una guía detallada sobre cómo probar el archivo `.exe` para asegurar que funciona correctamente.
