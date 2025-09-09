# --- README: Guía de Pruebas para cultivarte_wc_sync.exe ---

## Objetivo

Esta guía describe los pasos para verificar que el archivo `cultivate_wc_sync.exe` funciona correctamente después de haber sido compilado. Las pruebas se centran en confirmar que la ejecución se produce sin errores y que los datos se sincronizan como se espera.

## Prerrequisitos

-   El archivo `cultivarte_wc_sync.exe` se encuentra en la carpeta principal del proyecto.
-   El archivo `.env` está en la misma carpeta y configurado con las credenciales correctas.
-   Tienes acceso a la base de datos MySQL y al archivo de Excel para verificar los cambios.

---

### Prueba 1: Ejecución Inicial y Verificación del Log

**Propósito**: Asegurarse de que el programa se ejecuta sin fallos críticos y genera un archivo de log.

1.  **Limpieza**: Si existe un archivo llamado `sync_general.log` en la carpeta, bórralo para empezar con un registro limpio.
2.  **Ejecución**: Haz doble clic en `cultivarte_wc_sync.exe`. No aparecerá ninguna ventana (esto es normal debido a la opción `--windowed`).
3.  **Espera**: Dale al programa unos 30-60 segundos para que complete su primer ciclo de ejecución.
4.  **Verificación**:
    -   Comprueba que se ha creado un nuevo archivo `sync_general.log`.
    -   Abre el archivo de log. Deberías ver líneas de inicio y fin como las siguientes:
        ```
        INFO - INICIO DEL PROCESO DE SINCRONIZACIÓN GENERAL
        ... (mensajes de los módulos de clientes y pedidos) ...
        INFO - FIN DEL PROCESO DE SINCRONIZACIÓN GENERAL
        ```
    -   Revisa que no haya mensajes con nivel `ERROR` o `CRITICAL`.

**Resultado esperado**: El log se crea y no muestra errores críticos.

---

### Prueba 2: Sincronización de Excel a MySQL

**Propósito**: Verificar que un nuevo cliente añadido en Excel se inserta correctamente en la base de datos.

1.  **Preparación**: Abre el archivo Excel especificado en tu `.env`.
2.  **Añade un nuevo cliente**:
    -   Ve a la hoja "Clientes Web".
    -   Crea una nueva fila con datos de prueba. Asegúrate de usar un **email único** que no exista en la base de datos.
    -   En la columna `ultima_modificacion`, pon la fecha y hora actual.
3.  **Guarda y cierra** el archivo Excel.
4.  **Ejecuta** `cultivarte_wc_sync.exe` de nuevo.
5.  **Verificación**:
    -   Revisa el `sync_general.log`. Deberías encontrar una línea similar a: `INFO - MySQL INSERT: [el_email_nuevo@test.com]`.
    -   Conéctate a tu base de datos MySQL y comprueba que el nuevo registro existe en la tabla `clientes`.

**Resultado esperado**: El nuevo cliente de Excel aparece en la tabla `clientes` de MySQL.

---

### Prueba 3: Sincronización de MySQL a Excel

**Propósito**: Verificar que una actualización en la base de datos se refleja en el archivo Excel.

1.  **Preparación**: Conéctate a tu base de datos MySQL.
2.  **Actualiza un cliente**:
    -   Busca un cliente existente en la tabla `clientes`.
    -   Cambia el valor de una de sus columnas, por ejemplo, el `telefono`.
    -   Guarda el cambio. La columna `ultima_modificacion` debería actualizarse automáticamente a la hora actual.
3.  **Ejecuta** `cultivarte_wc_sync.exe`.
4.  **Verificación**:
    -   Revisa el `sync_general.log`. Deberías encontrar una línea como: `INFO - Excel UPDATE: [email_del_cliente_actualizado@test.com]`.
    -   Abre el archivo Excel. Comprueba que el teléfono del cliente que modificaste en la base de datos ahora muestra el nuevo valor.

**Resultado esperado**: El cambio hecho en MySQL se refleja en el archivo Excel.

---

Si todas estas pruebas se completan con éxito, el ejecutable está funcionando correctamente.
