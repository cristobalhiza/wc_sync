# sync_clientes.py
import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime
import logging

# --- 1. CONFIGURACIÓN INICIAL ---

def load_config():
    """Carga la configuración desde el archivo .env."""
    load_dotenv()
    config = {
        "db_host": os.getenv('DB_HOST'),
        "db_user": os.getenv('DB_USER'),
        "db_password": os.getenv('DB_PASSWORD'),
        "db_database": os.getenv('DB_DATABASE'),
        "excel_path": os.getenv('EXCEL_FILE_PATH'),
        "excel_sheet": os.getenv('EXCEL_SHEET_NAME')
    }
    # Validar que las variables esenciales no estén vacías
    for key, value in config.items():
        if not value:
            msg = f"Error: La variable de entorno '{key.upper()}' no está definida en el archivo .env"
            logging.error(msg)
            raise ValueError(msg)
    return config

def get_db_connection(config):
    """Establece y devuelve una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(
            host=config["db_host"],
            user=config["db_user"],
            password=config["db_password"],
            database=config["db_database"]
        )
        if conn.is_connected():
            logging.info("Conexión a MySQL establecida exitosamente.")
            return conn
    except Error as e:
        logging.error(f"Error al conectar a MySQL: {e}")
        return None

# --- 2. LECTURA DE DATOS (INCREMENTAL) ---

def get_last_sync_time(cursor):
    """Obtiene la fecha y hora de la última sincronización exitosa."""
    try:
        cursor.execute("SELECT ultimo_sync FROM ultima_sincronizacion WHERE nombre_tabla = 'clientes'")
        result = cursor.fetchone()
        if result:
            logging.info(f"Última sincronización registrada: {result[0]}")
            return result[0]
        else:
            # Devuelve una fecha muy antigua si no hay registro
            return datetime(1970, 1, 1)
    except Error as e:
        logging.error(f"Error al obtener la última fecha de sincronización: {e}")
        return None

def read_recent_mysql_data(cursor, last_sync_time):
    """Lee solo los registros de MySQL modificados desde la última sincronización."""
    try:
        query = "SELECT id, nombre, apellido, email, telefono, direccion, ultima_modificacion FROM clientes WHERE ultima_modificacion > %s"
        cursor.execute(query, (last_sync_time,))
        return pd.DataFrame(cursor.fetchall(), columns=[i[0] for i in cursor.description])
    except Error as e:
        logging.error(f"Error al leer datos de MySQL: {e}")
        return pd.DataFrame()

def read_recent_excel_data(config, last_sync_time):
    """Lee y filtra los datos de Excel modificados desde la última sincronización."""
    try:
        df = pd.read_excel(config["excel_path"], sheet_name=config["excel_sheet"])
        # Asegurarse de que las columnas de fecha estén en formato datetime
        df['ultima_modificacion'] = pd.to_datetime(df['ultima_modificacion'])
        
        # Filtrar registros recientes
        recent_df = df[df['ultima_modificacion'] > last_sync_time].copy()
        logging.info(f"Leídos {len(df)} registros de Excel. {len(recent_df)} son nuevos o modificados.")
        return df, recent_df
    except FileNotFoundError:
        logging.error(f"Archivo Excel no encontrado en la ruta: {config['excel_path']}")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        logging.error(f"Error al leer o procesar el archivo Excel: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. LÓGICA DE SINCRONIZACIÓN ---

def sync_excel_to_mysql(cursor, excel_recent_df):
    """Sincroniza los cambios de Excel a MySQL (Inserts y Updates)."""
    logging.info("--- Iniciando Sincronización: Excel -> MySQL ---")
    inserts = 0
    updates = 0
    
    for _, row in excel_recent_df.iterrows():
        try:
            # Verificar si el cliente existe
            cursor.execute("SELECT id FROM clientes WHERE email = %s", (row['email'],))
            result = cursor.fetchone()
            
            # Limpiar datos NaN que pueden venir de Excel
            row_data = row.where(pd.notnull(row), None).to_dict()

            if result:
                # UPDATE
                update_query = """
                UPDATE clientes SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, ultima_modificacion=%s
                WHERE email=%s
                """
                cursor.execute(update_query, (
                    row_data['nombre'], row_data['apellido'], row_data['telefono'], 
                    row_data['direccion'], row_data['ultima_modificacion'], row_data['email']
                ))
                updates += 1
                logging.info(f"MySQL UPDATE: {row_data['email']}")
            else:
                # INSERT
                insert_query = """
                INSERT INTO clientes (nombre, apellido, email, telefono, direccion, ultima_modificacion)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    row_data['nombre'], row_data['apellido'], row_data['email'], 
                    row_data['telefono'], row_data['direccion'], row_data['ultima_modificacion']
                ))
                inserts += 1
                logging.info(f"MySQL INSERT: {row_data['email']}")
        except Error as e:
            logging.error(f"Error al sincronizar la fila de Excel para {row.get('email', 'N/A')}: {e}")
            raise # Propagar el error para activar el rollback

    logging.info(f"Sincronización Excel -> MySQL completada. Registros insertados: {inserts}, actualizados: {updates}.")

def sync_mysql_to_excel(excel_full_df, mysql_recent_df):
    """Sincroniza los cambios de MySQL a Excel (Inserts y Updates)."""
    logging.info("--- Iniciando Sincronización: MySQL -> Excel ---")
    inserts = 0
    updates = 0
    
    # Crear una copia para evitar modificar el DataFrame original mientras se itera
    excel_df_updated = excel_full_df.copy()

    for _, row in mysql_recent_df.iterrows():
        # Buscar si el email existe en el DataFrame de Excel
        match_index = excel_df_updated.index[excel_df_updated['email'] == row['email']].tolist()

        if match_index:
            # UPDATE: Actualizar la fila existente en Excel
            idx = match_index[0]
            excel_df_updated.loc[idx, ['nombre', 'apellido', 'telefono', 'direccion', 'ultima_modificacion']] = \
                [row['nombre'], row['apellido'], row['telefono'], row['direccion'], row['ultima_modificacion']]
            updates += 1
            logging.info(f"Excel UPDATE: {row['email']}")
        else:
            # INSERT: Añadir nueva fila al DataFrame de Excel
            new_row_df = pd.DataFrame([row])
            excel_df_updated = pd.concat([excel_df_updated, new_row_df], ignore_index=True)
            inserts += 1
            logging.info(f"Excel INSERT: {row['email']}")
            
    logging.info(f"Sincronización MySQL -> Excel completada. Filas añadidas: {inserts}, actualizadas: {updates}.")
    return excel_df_updated

# --- 4. GUARDADO Y FINALIZACIÓN ---

def save_df_to_excel(df, config):
    """Guarda el DataFrame actualizado de vuelta al archivo Excel."""
    try:
        with pd.ExcelWriter(config["excel_path"], engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name=config["excel_sheet"], index=False)
        logging.info(f"Archivo Excel '{config['excel_path']}' guardado exitosamente.")
        return True
    except Exception as e:
        logging.error(f"No se pudo guardar el archivo Excel. Error: {e}")
        return False

def update_last_sync_time(cursor, new_sync_time):
    """Actualiza la marca de tiempo de la última sincronización en la BD."""
    try:
        cursor.execute(
            "UPDATE ultima_sincronizacion SET ultimo_sync = %s WHERE nombre_tabla = 'clientes'",
            (new_sync_time,)
        )
        logging.info(f"Marca de tiempo de sincronización actualizada a: {new_sync_time}")
    except Error as e:
        logging.error(f"Error al actualizar la marca de tiempo de sincronización: {e}")
        raise # Propagar para rollback

# --- FUNCIÓN PRINCIPAL ---

def main():
    """Orquesta todo el proceso de sincronización."""
    logging.info("================ INICIO DEL PROCESO DE SINCRONIZACIÓN DE CLIENTES ================")
    
    try:
        config = load_config()
    except ValueError:
        return # Termina si la configuración es inválida

    conn = get_db_connection(config)
    if not conn:
        return

    cursor = conn.cursor()
    
    try:
        # 1. Obtener la marca de tiempo para esta sincronización
        new_sync_time = datetime.now()
        last_sync_time = get_last_sync_time(cursor)
        if last_sync_time is None:
            raise Exception("No se pudo obtener la última fecha de sincronización.")

        # 2. Leer datos recientes de ambas fuentes
        excel_full_df, excel_recent_df = read_recent_excel_data(config, last_sync_time)
        mysql_recent_df = read_recent_mysql_data(cursor, last_sync_time)

        if excel_full_df.empty and not os.path.exists(config["excel_path"]):
             raise Exception("El archivo Excel no existe y no se puede continuar.")

        # 3. Iniciar transacción de base de datos
        conn.start_transaction()
        logging.info("Transacción de base de datos iniciada.")

        # 4. Sincronizar Excel -> MySQL
        sync_excel_to_mysql(cursor, excel_recent_df)
        
        # 5. Sincronizar MySQL -> Excel (en memoria)
        excel_df_after_sync = sync_mysql_to_excel(excel_full_df, mysql_recent_df)

        # 6. Actualizar la marca de tiempo en la BD
        update_last_sync_time(cursor, new_sync_time)

        # 7. Si todo en la BD fue exitoso, confirmar los cambios
        conn.commit()
        logging.info("Transacción de base de datos confirmada (COMMIT).")

        # 8. Guardar los cambios en el archivo Excel
        if not excel_full_df.equals(excel_df_after_sync):
            save_df_to_excel(excel_df_after_sync, config)
        else:
            logging.info("No hubo cambios de MySQL a Excel para guardar.")

    except Exception as e:
        logging.error(f"Ha ocurrido un error crítico durante la sincronización: {e}")
        logging.error("Revirtiendo cambios en la base de datos (ROLLBACK).")
        if conn.in_transaction:
            conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Conexión a MySQL cerrada.")
    
    logging.info("================ FIN DEL PROCESO DE SINCRONIZACIÓN DE CLIENTES ================\n")


if __name__ == "__main__":
    main()
