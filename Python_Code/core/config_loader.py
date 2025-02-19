import json
import os

class ConfigLoader:
    """
    Loads configuration from a JSON file.
    """
    def __init__(self, config_path="config.json"):
        """
        Initializes the ConfigLoader with the specified configuration file path.

        Args:
            config_path (str): The path to the configuration file (default: "config.json").
        """
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """
        Loads the configuration from the JSON file.

        Returns:
            dict: The configuration as a dictionary.  Returns an empty dictionary if the file is not found or parsing fails.
        """
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Configuration file '{self.config_path}' not found.")
            return {}  # Or raise, if it's a critical error
        except json.JSONDecodeError:
            print(f"Error parsing JSON in file '{self.config_path}'.")
            return {}  # Or raise

    def get_config(self):
        """
        Returns the loaded configuration.

        Returns:
            dict: The loaded configuration dictionary.
        """
        return self.config

    def get_api_key(self):
        """
        Returns the API key from the configuration.

        Returns:
            str: The API key, or None if not found.
        """
        return self.config.get("api", {}).get("key")

    def get_api_model(self):
        """
        Returns the API model from the configuration.

        Returns:
            str: The API model, or None if not found.
        """
        return self.config.get("api", {}).get("model")

    def get_db_config(self):
        """
        Returns the database configuration from the configuration.

        Returns:
            dict: The database configuration dictionary, or an empty dictionary if not found.
        """
        return self.config.get("db_config", {})

    def get_subprogram_dir(self):
        """
        Returns the path to the subprogram directory from the configuration.

        Returns:
            str: The path to the subprogram directory, or None if not found.
        """
        return self.config.get("paths", {}).get("subprogram_dir")

    def get_venv_name(self):
        """
        Returns the name of the virtual environment from the configuration.

        Returns:
            str: The name of the virtual environment, or None if not found.
        """
        return self.config.get("paths", {}).get("venv_name")

    def get_log_file(self):
        """
        Returns the path to the log file from the configuration.

        Returns:
            str: The path to the log file, or None if not found.
        """
        return self.config.get("log", {}).get("file")

    def get_log_level(self):
        """
        Returns the log level from the configuration.

        Returns:
            str: The log level, or None if not found.
        """
        return self.config.get("log", {}).get("level")

    def get_powershell_path(self):
        """
        Returns the path to PowerShell from the configuration.

        Returns:
            str: The path to PowerShell, or None if not found.
        """
        return self.config.get("shell", {}).get("powershell_path")


if __name__ == '__main__':
    # Usage example
    config_loader = ConfigLoader()
    config = config_loader.get_config()
    print("Loaded configuration:", config)
    print("API Key:", config_loader.get_api_key())
    print("Database configuration:", config_loader.get_db_config())