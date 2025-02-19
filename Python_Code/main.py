import logging
import sys
import os

# Adding the absolute path to the project to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from core.config_loader import ConfigLoader
from modules.api import GeminiAPI
from modules.db import MariaDB
from modules.gui import run_gui  # Importujeme run_gui


def main():
    # 1. Load configuration
    config_loader = ConfigLoader(config_path="core/config.json")  # Make sure the path is correct # Corrected path
    config = config_loader.get_config()

    # 2. Set up logging
    log_level = config_loader.get_log_level()
    logging.basicConfig(filename=config_loader.get_log_file(), level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Application started.")

    # 3. Initialize Gemini API
    try:
        api_key = config_loader.get_api_key()
        api_model = config_loader.get_api_model()
        if not api_key:
            logger.error("API key is not set in the configuration file.")
            return  # Exit the program if the API key is missing
        gemini_api = GeminiAPI(api_key, api_model, log_level=log_level)
        logger.info("Gemini API initialized.")
    except Exception as e:
        logger.exception("Error initializing Gemini API.")
        return

    # 4. Initialize database
    try:
        db_config = config_loader.get_db_config()
        if not db_config:
            logger.error("Database configuration is not set in the configuration file.")
            return  # Exit the program if the database configuration is missing
        db = MariaDB(db_config, log_level=log_level)
        try:
            db.create_table_if_not_exists()
        except Exception as e:
            logger.exception("Database not created.")

    except Exception as e:
        logger.exception("Error initializing database.")
        return

    # 5. Run GUI
    try:
        run_gui(gemini_api, db, config, log_level)  # Pass api, db, and config to the GUI
        logger.info("GUI started.")
    except Exception as e:
        logger.exception("Error starting GUI.")
        return

    logger.info("Application finished running.")


if __name__ == "__main__":
    main()