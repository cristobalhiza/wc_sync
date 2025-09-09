# main.py
import logging
import sync_clientes
import sync_wc_orders

def setup_global_logging():
    """
    Configura un sistema de logging centralizado que registrará 
    los eventos de todos los scripts en un único archivo y en la consola.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("sync_general.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """
    Script orquestador principal para ejecutar todos los procesos de sincronización.
    """
    setup_global_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("======================================================")
    logger.info("= INICIO DEL PROCESO DE SINCRONIZACIÓN GENERAL       =")
    logger.info("======================================================")

    try:
        logger.info("--- Iniciando Módulo 1: Sincronización de Clientes (Excel <-> BD) ---")
        # Llamamos a la función principal del script de clientes
        sync_clientes.main()
        logger.info("--- Módulo 1: Sincronización de Clientes finalizada exitosamente ---")
    except Exception as e:
        logger.error(f"*** ERROR CRÍTICO en el módulo de sincronización de clientes: {e} ***")
        # Se podría decidir si continuar o detener todo el proceso. Por ahora, continuamos.

    logger.info("-" * 50)

    try:
        logger.info("--- Iniciando Módulo 2: Sincronización de Pedidos (WooCommerce -> BD) ---")
        # Llamamos a la función principal del script de pedidos
        sync_wc_orders.run()
        logger.info("--- Módulo 2: Sincronización de Pedidos finalizada exitosamente ---")
    except Exception as e:
        logger.error(f"*** ERROR CRÍTICO en el módulo de sincronización de pedidos: {e} ***")

    logger.info("======================================================")
    logger.info("= FIN DEL PROCESO DE SINCRONIZACIÓN GENERAL          =")
    logger.info("======================================================")


if __name__ == "__main__":
    main()
