import requests
import json
import logging

class GeminiAPI:
    """
    A class for interacting with the Gemini API.
    """
    def __init__(self, api_key, api_model, log_level=logging.INFO):
        """
        Initializes the GeminiAPI with the provided API key, model, and log level.

        Args:
            api_key (str): The API key for accessing the Gemini API.
            api_model (str): The model to use for generating content.
            log_level (int): The logging level (default: logging.INFO).
        """
        self.api_key = api_key
        self.api_model = api_model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.api_model}:generateContent?key={self.api_key}"
        self.headers = {'Content-Type': 'application/json'}
        self.logger = self.setup_logger(log_level)

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

    def generate_content(self, prompt, max_retries=3):
        """
        Sends a request to the Gemini API and returns the response.

        Args:
            prompt (str): The prompt to send to the API.
            max_retries (int): The maximum number of retries in case of failure (default: 3).

        Returns:
            str: The text response from the API, or None if the request fails after multiple retries or if the response is empty.
        """
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        json_data = json.dumps(data)

        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, data=json_data)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                response_json = response.json()
                # Extract the text response from JSON
                if 'candidates' in response_json and response_json['candidates']:
                    text_response = response_json['candidates'][0]['content']['parts'][0]['text']
                    return text_response
                else:
                    self.logger.warning(f"Empty response from Gemini API (attempt {attempt + 1}/{max_retries}).")
                    return None  # Or raise an exception if an empty response is not acceptable

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error communicating with Gemini API (attempt {attempt + 1}/{max_retries}): {e}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON response (attempt {attempt + 1}/{max_retries}): {e}")

        self.logger.error(f"Failed to get a response from Gemini API after {max_retries} attempts.")
        return None

if __name__ == '__main__':
    # Usage example (requires API key)
    import sys
    sys.path.append("..")  # Add the parent directory to the path for importing ConfigLoader
    from config_loader import ConfigLoader  # Corrected import

    #config_loader = ConfigLoader()
    config_loader = ConfigLoader(config_path="../config.json") # Corrected path and using standard name
    api_key = config_loader.get_api_key()
    api_model = config_loader.get_api_model()
    log_level = config_loader.get_log_level()

    if not api_key:
        print("API key is not set in the configuration file.")
    else:
        api = GeminiAPI(api_key, api_model, log_level=logging.DEBUG) # logging.DEBUG for detailed logging
        prompt = "What is the capital of the Czech Republic?"
        response = api.generate_content(prompt)

        if response:
            print("Response from Gemini API:", response)
        else:
            print("Failed to get a response from Gemini API.")