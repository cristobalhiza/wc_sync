# setup_database.py
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_connection():
    """Crea una conexión a la base de datos MySQL."""
    conn = None
    try:
        load_dotenv()
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE')
        )
        if conn.is_connected():
            logging.info("Conexión a MySQL establecida exitosamente.")
            return conn
    except Error as e:
        logging.error(f"Error al conectar a MySQL: {e}")
        return None

def setup_tables(conn):
    """Crea las tablas necesarias si no existen."""
    cursor = conn.cursor()
    try:
        # Crear tabla de clientes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255),
            apellido VARCHAR(255),
            email VARCHAR(255) NOT NULL UNIQUE,
            telefono VARCHAR(50),
            direccion VARCHAR(500),
            ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)
        logging.info("Tabla 'clientes' verificada/creada exitosamente.")

        # Crear tabla de sincronización
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ultima_sincronizacion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_tabla VARCHAR(255) NOT NULL UNIQUE,
            ultimo_sync TIMESTAMP
        ) ENGINE=InnoDB;
        """)
        logging.info("Tabla 'ultima_sincronizacion' verificada/creada exitosamente.")

        # Insertar registro inicial para la tabla de clientes si no existe
        cursor.execute("""
        INSERT INTO ultima_sincronizacion (nombre_tabla, ultimo_sync)
        VALUES ('clientes', '1970-01-01 00:00:01')
        ON DUPLICATE KEY UPDATE nombre_tabla=nombre_tabla;
        """)
        logging.info("Registro de sincronización para 'clientes' verificado/insertado.")
        
        conn.commit()

    except Error as e:
        logging.error(f"Error al crear/verificar las tablas: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    """Función principal para ejecutar la configuración."""
    logging.info("Iniciando configuración de la base de datos...")
    conn = create_connection()
    if conn:
        setup_tables(conn)
        conn.close()
        logging.info("Conexión a MySQL cerrada.")
    logging.info("Configuración de la base de datos finalizada.")

if __name__ == "__main__":
    main()
