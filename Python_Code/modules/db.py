import mysql.connector
import logging
import json

class MariaDB:
    """
    A class for interacting with a MariaDB database.
    """
    def __init__(self, config, log_level=logging.INFO):
        """
        Initializes the MariaDB object with the database configuration and log level.

        Args:
            config (dict): A dictionary containing the database connection configuration.
            log_level (int): The logging level (default: logging.INFO).
        """
        self.config = config
        self.logger = self.setup_logger(log_level)
        self.connection = None
        self.cursor = None

    def setup_logger(self, log_level):
        """
        Sets up the logger for the module.

        Args:
            log_level (int): The logging level.

        Returns:
            logging.Logger: The configured logger.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        handler = logging.StreamHandler()  # Logging to console
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def connect(self):
        """
        Connects to the MariaDB database.
        """
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            self.logger.info("Connected to MariaDB database.")
        except mysql.connector.Error as err:
            self.logger.error(f"Failed to connect to the database: {err}")
            self.connection = None
            self.cursor = None

    def disconnect(self):
        """
        Disconnects from the MariaDB database.
        """
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.logger.info("Disconnected from MariaDB database.")

    def execute_query(self, query, params=None):
        """
        Executes a query on the database.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters to pass to the query. Defaults to None.

        Returns:
            list: The result of the query, or None if an error occurred.
        """
        try:
            self.connect()  # Connect before each query for safety
            self.cursor.execute(query, params)
            if query.lower().startswith("select"):
                result = self.cursor.fetchall()
            else:
                result = None
            self.connection.commit()
            return result
        except mysql.connector.Error as err:
            self.logger.error(f"Error executing query: {err}")
            return None
        finally:
            self.disconnect()  # Disconnect after each query

    def get_actions(self):
        """
        Retrieves all active actions from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents an action.
        """
        query = "SELECT id, name, description, file, execution_type, expected_outputs, status FROM actions WHERE status = 'active'"  # Changed column names here
        result = self.execute_query(query)
        if result:
            actions = []
            for row in result:
                action = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "file": row[3],
                    "execution_type": row[4],
                    "expected_outputs": json.loads(row[5]) if row[5] else [],
                    "status": row[6]
                }
                actions.append(action)
            return actions
        else:
            return []

    def add_action(self, name, description, file, execution_type, expected_outputs): # Name needs to stay the same, its used in gui.py
        """
        Adds a new action to the database.

        Args:
            name (str): The name of the action.
            description (str): The description of the action.
            file (str): The file associated with the action.
            execution_type (str): The execution type of the action.
            expected_outputs (list): A list of expected outputs for the action.
        """
        query = """
            INSERT INTO actions (name, description, file, execution_type, expected_outputs, status)  -- Changed column names here
            VALUES (%s, %s, %s, %s, %s, 'active')
        """
        params = (name, description, file, execution_type, json.dumps(expected_outputs))
        self.execute_query(query, params)

    def update_action_status(self, action_id, status):
        """
        Updates the status of an action in the database.

        Args:
            action_id (int): The ID of the action to update.
            status (str): The new status of the action.
        """
        query = "UPDATE actions SET status = %s WHERE id = %s" # Changed column names here
        params = (status, action_id)
        self.execute_query(query, params)
    
    def create_table_if_not_exists(self):
        # Usage example (requires a correctly configured database)
        import sys
        sys.path.append("..")
        from core.config_loader import ConfigLoader

        config_loader = ConfigLoader(config_path="core/config.json")
        db_config = config_loader.get_db_config()
        log_level = config_loader.get_log_level()

        print(db_config.get("db_config", {}).get("database"))

        if not db_config or db_config.get("db_config", {}).get("database") == "":
            print("Database configuration is not set in the configuration file.")
        else:
            db = MariaDB(db_config, log_level=logging.DEBUG)  # logging.DEBUG for detailed logging
            print("Checking if table actions exist in the DB, if not it will be created now.")

            # Creating a table if it does not exist
            create_table_query = """
                CREATE TABLE IF NOT EXISTS actions (  -- Changed table name to english
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),  -- Changed column name
                    description TEXT,   -- Changed column name
                    file VARCHAR(255),    -- Changed column name
                    execution_type ENUM('python', 'cmd', 'powershell'),  -- Changed column name
                    expected_outputs TEXT,   -- Changed column name
                    status ENUM('active', 'replaced', 'faulty') DEFAULT 'active',   -- Changed column name
                    replaced_by_action INT,  -- Changed column name
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (replaced_by_action) REFERENCES actions(id) -- Changed column and table name here
                )
            """
            db.execute_query(create_table_query)

            # Test getting actions
            actions = db.get_actions()
            print("List of actions:", actions)

            # Test adding an action
            #db.add_action("test_akce", "Toto je testovací akce", "test_akce.py", "python", ["vystup1", "vystup2"])

            # Test updating action status
            #if actions:
            #    db.update_action_status(actions[0]["id"], "nahrazená")


if __name__ == '__main__':
    # Usage example (requires a correctly configured database)
    import sys
    sys.path.append("..")
    from core.config_loader import ConfigLoader

    config_loader = ConfigLoader(config_path="../core/config.json")
    db_config = config_loader.get_db_config()
    log_level = config_loader.get_log_level()

    if not db_config:
        print("Database configuration is not set in the configuration file.")
    else:
        db = MariaDB(db_config, log_level=logging.DEBUG)  # logging.DEBUG for detailed logging

        # Creating a table if it does not exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS actions (  -- Changed table name to english
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),  -- Changed column name
                description TEXT,   -- Changed column name
                file VARCHAR(255),    -- Changed column name
                execution_type ENUM('python', 'cmd', 'powershell'),  -- Changed column name
                expected_outputs TEXT,   -- Changed column name
                status ENUM('active', 'replaced', 'faulty') DEFAULT 'active',   -- Changed column name
                replaced_by_action INT,  -- Changed column name
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (replaced_by_action) REFERENCES actions(id) -- Changed column and table name here
            )
        """
        db.execute_query(create_table_query)
        db.connection.commit()

        # Test getting actions
        actions = db.get_actions()
        print("List of actions:", actions)

        # Test adding an action
        #db.add_action("test_akce", "Toto je testovací akce", "test_akce.py", "python", ["vystup1", "vystup2"])

        # Test updating action status
        #if actions:
        #    db.update_action_status(actions[0]["id"], "nahrazená")