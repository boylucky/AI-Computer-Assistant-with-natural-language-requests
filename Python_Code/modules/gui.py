import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import simpledialog
import logging
import threading
import queue
import json
import os
import subprocess
import string
import re

class GUI:
    """
    A class for creating a graphical user interface (GUI) for interacting with the AI assistant.
    """
    def __init__(self, master, api, db, config, log_level=logging.INFO):
        """
        Initializes the GUI with the provided master window, API, database, configuration, and log level.

        Args:
            master (tk.Tk): The master window for the GUI.
            api: The API object for communicating with the Gemini API.
            db: The database object for interacting with the database.
            config (dict): A dictionary containing the configuration settings.
            log_level (int): The logging level (default: logging.INFO).
        """
        self.master = master
        master.title("AI Assistant")
        self.api = api
        self.db = db
        self.config = config
        self.log_level = log_level

        self.request_queue = queue.Queue()  # Queue for requests from the GUI

        # GUI components
        self.label = tk.Label(master, text="Enter request:")
        self.label.pack()

        self.request_entry = tk.Entry(master, width=50)
        self.request_entry.pack()

        self.send_button = tk.Button(master, text="Send", command=self.send_request)
        self.send_button.pack()

        # Initialize status_text BEFORE setup_logger
        self.status_text = scrolledtext.ScrolledText(master, width=60, height=20)
        self.status_text.pack()
        self.status_text.config(state=tk.DISABLED)  # Prevent user editing

        self.logger = self.setup_logger()  # Initialize logger after status_text

        # Start request processing thread
        self.running = True
        self.request_thread = threading.Thread(target=self.process_requests, daemon=True)
        self.request_thread.start()

    def setup_logger(self):
        """
        Sets up the logger for the GUI, logging to both the console and the status_text widget.

        Returns:
            logging.Logger: The configured logger.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        # Handler for logging to status_text
        text_handler = GUI.TextHandler(self.status_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)

        return logger

    def send_request(self):
        """
        Sends a request to the request queue.
        """
        request = self.request_entry.get()
        self.logger.info(f"Added request to queue: {request}")
        self.request_queue.put(request)

    def process_requests(self):
        """
        Processes requests from the queue in a separate thread.
        """
        while self.running:
            try:
                request = self.request_queue.get(timeout=1)  # Wait 1 second for a request
                self.logger.info(f"Processing request: {request}")
                self.process_request(request)  # Process the request
                self.request_queue.task_done()  # Mark the task as done
            except queue.Empty:
                pass  # No request, continue the loop
            except Exception as e:
                self.logger.exception(f"Error processing request: {e}")

    def process_request(self, request):
        """
        Processes a single request (communicates with the API, DB, etc.).

        Args:
            request (str): The request to process.
        """
        try:
            # 1. Check prefix
            if request.startswith("0 "):
                # One-time action execution
                request = request[2:].strip()  # Remove prefix "0 "
                self.execute_adhoc_action(request)
                return
            elif request.startswith("1 "):
                # Create a new action
                request = request[2:].strip()  # Remove prefix "1 "
                self.learn_new_action(request, request)
                return

            # 2. Get actions from the database
            #actions = self.db.get_actions()
            #self.logger.info(f"Loaded {len(actions)} actions from the database.")
            try:
                actions = self.db.get_actions()
                self.logger.info(f"Loaded {len(actions)} actions from the database.")
            except Exception as e:
                self.logger.error(f"Unable to get list of actions from database: {e}")
                actions = []  # Empty list of actions

            # 3. Build the prompt for the Gemini API
            # Build a list of available actions (ID and description)
            available_actions = "\n".join([f"{action['id']}: {action['description']}" for action in actions]) # Changed action['popis'] to action['description']
            prompt = f"User asks: {request}\nAvailable actions:\n{available_actions}\nAnswer with the ID of the action, a list of action IDs separated by commas, or the exact phrase 'ACTION_NOT_FOUND' if none of the available actions match the request."
            self.logger.debug(f"Prompt for Gemini API: {prompt}")

            # 4. Communicate with the Gemini API
            response = self.api.generate_content(prompt)
            if response:
                self.logger.info(f"Response from Gemini API: {response}")

                # 5. Parse the response from the Gemini API
                if response.strip() == "ACTION_NOT_FOUND":
                    self.learn_new_action(request, request)
                    return

                try:
                    # Try to parse the response as a list of action IDs separated by commas
                    action_ids = [int(id.strip()) for id in response.split(",")]
                except ValueError:
                    self.logger.error(f"Invalid response format from Gemini API: {response}")
                    self.display_result("Invalid response format from Gemini API.")
                    return

                # 6. Execute actions
                output = ""
                for action_id in action_ids:
                    # Find the action in the database
                    action = next((a for a in actions if a["id"] == action_id), None)
                    if not action:
                        self.logger.warning(f"Action with ID '{action_id}' not found in the database.")
                        self.display_result(f"Action with ID '{action_id}' not found in the database.")
                        return

                    # Run the action
                    output += self.execute_action(action) + "\n"

                # 7. Display the result
                self.display_result(output)
            else:
                self.logger.warning("Gemini API returned no response.")
                self.display_result("Gemini API returned no response.")

        except Exception as e:
            self.logger.exception(f"Error processing request: {e}")
            self.display_result(f"Error: {e}")

    def execute_adhoc_action(self, request):
        """
        Executes a one-time action without searching the database and without saving it.

        Args:
            request (str): The request to execute.
        """
        self.logger.info(f"Performing one-time action: {request}")

        # 1. Ask Gemini API what code to run
        prompt = f"User wants to perform a one-time action with request '{request}'. Return minimal code in python, cmd, or powershell that performs this action. Return JSON in format {{\"kod\": \"code\", \"typ\": \"python|cmd|powershell\"}}"
        response = self.api.generate_content(prompt)

        if response:
            self.logger.info(f"Response from Gemini API: {response}")

            # 2. Parse the response from the Gemini API
            try:
                # Remove text before JSON and apostrophes and newline characters
                response = response[response.find("{"):].replace("```json", "").replace("```", "").replace("\n", "").replace("\\'", "'")  # Remove text before JSON
                response_json = json.loads(response)
                code = response_json.get("kod")
                execution_type = response_json.get("typ")
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid response format from Gemini API: {response} - {e}")
                self.display_result("Invalid response format from Gemini API.")
                return

            # 3. Test the code
            output = self.test_new_action_code(code, execution_type)

            # 4. Display the result
            self.display_result(output)
        else:
            self.logger.warning("Gemini API returned no response.")
            self.display_result("Gemini API returned no response.")

    def learn_new_action(self, request, original_request):
        """
        Learns a new action.

        Args:
            request (str): The request to learn.
            original_request (str): The original request.
        """
        if messagebox.askyesno("Learning new action", f"Do you want to learn a new action?"):
            self.logger.info(f"Starting to learn a new action.")

            code = None
            execution_type = None
            description = None
            file_name = None
            output = "ERROR"  # Initialize output for the while loop
            max_attempts = 5  # Maximum number of attempts

            attempt = 0
            while "ERROR" in output and attempt < max_attempts:
                attempt += 1
                self.logger.info(f"Attempt no.: {attempt}")

                # 1. Ask Gemini API what code to run
                prompt = f"User wants to perform an action with request '{request}'. Return minimal code in python, cmd, or powershell that performs this action, a brief description of this action, and a suggestion for a file name to store the code (without extension). If you use python, return only the code to be executed, not the whole command. Return JSON in format {{\"kod\": \"code\", \"typ\": \"python|cmd|powershell\", \"popis\": \"action description\", \"nazev_souboru\": \"file_name\"}}. "
                if "Missing module:" in output:
                    parts = output.split(": ")
                    if len(parts) > 3:
                        module_name = parts[3]  # Extract module name from the error message
                        prompt += f"Previous attempt failed because the module '{module_name}' was missing. Modify the code to work without this module or add code to install this module."
                    else:
                        prompt += f"Previous attempt failed, but it was not possible to determine the name of the missing module. Try again."
                elif output != "ERROR":  # If we already have some error, then send it to Gemini API
                    prompt += f"Previous attempt failed with error: {output}. Correct the code."

                response = self.api.generate_content(prompt)

                if response:
                    self.logger.info(f"Response from Gemini API: {response}")

                    # 2. Parse the response from the Gemini API
                    try:
                        # Remove text before JSON and apostrophes and newline characters
                        response = response[response.find("{"):].replace("```json", "").replace("```", "").replace("\n", "").replace("\\'", "'")  # Remove text before JSON
                        response_json = json.loads(response)
                        code = response_json.get("kod")
                        execution_type = response_json.get("typ")
                        description = response_json.get("popis")  # Get action description
                        file_name = response_json.get("nazev_souboru")  # Get file name
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid response format from Gemini API: {response} - {e}")
                        self.display_result("Invalid response format from Gemini API.")
                        return

                    # 3. Test the code
                    output = self.test_new_action_code(code, execution_type)
                    self.logger.info(f"Testing output {output}")

                else:
                    self.logger.warning("Gemini API returned no response.")
                    self.display_result("Gemini API returned no response.")
                    return

            if "ERROR: Missing module:" in output:
                parts = output.split(": ")
                if len(parts) > 2:
                    module_name = parts[2]  # Extract module name from the error message
                    install_command = self.ask_gemini_for_install_command(module_name)
                    if install_command:
                        if self.install_missing_module(install_command):
                            # Reset output so that the loop repeats
                            output = "ERROR"
                            self.logger.info(f"Resetting output after successful installation of library {module_name}.")
                        else:
                            self.display_result(f"Failed to install module '{module_name}'.")
                            self.logger.error(f"Failed to install module '{module_name}'.")
                            return
                    else:
                        self.logger.warning("Failed to get command to install missing module.")
                        self.display_result("Failed to get command to install missing module.")
                        return
                else:
                    self.logger.warning("Failed to determine the name of the missing module.")
                    self.display_result("Failed to determine the name of the missing module.")
                    return

            if "ERROR" not in output:
                # 4. Save the action to the database
                self.save_new_action(request, description, code, execution_type, file_name)
            else:
                self.display_result(f"Learning action failed after {max_attempts} attempts.")
                self.logger.error(f"Learning action failed after {max_attempts} attempts.")

        else:
            self.logger.info(f"Learning action '{request}' canceled by user.")
            self.display_result("Learning action canceled.")

    def test_new_action_code(self, code, execution_type):
        """
        Tests the code of a new action.

        Args:
            code (str): The code to test.
            execution_type (str): The execution type of the code.

        Returns:
            str: The output of the code, or an error message if the code failed to execute.
        """
        try:
            if execution_type == "python":
                # Save the code to a temporary file
                with open("temp.py", "w", encoding="utf-8") as f:  # Added encoding="utf-8"
                    f.write("# -*- coding: utf-8 -*-\n" + code)  # Added encoding header
                command = ["python", "temp.py"]
            elif execution_type == "cmd":
                # Do not use a temporary file, run the code directly
                command = ["cmd", "/c", code]
            elif execution_type == "powershell":
                # Do not use a temporary file, run the code directly
                command = [self.config.get("shell").get("powershell_path"), "-Command", code]
            else:
                self.logger.error(f"Unknown execution type: {execution_type}")
                return f"ERROR: Unknown execution type: {execution_type}"

            self.logger.info(f"Testing code: {command}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            try:
                output = stdout.decode("utf-8")
            except UnicodeDecodeError:
                output = stdout.decode("latin-1")  # Try to decode as latin-1

            try:
                error = stderr.decode("utf-8")
            except UnicodeDecodeError:
                error = stderr.decode("latin-1")  # Try to decode as latin-1

            # Delete temporary file (only for python)
            if os.path.exists("temp.py"):
                os.remove("temp.py")

            if error:
                self.logger.error(f"Error testing code: {error}")
                if "ModuleNotFoundError" in error:
                    module_name = re.search(r"No module named '(\w+)'", error).group(1) if re.search(r"No module named '(\w+)'", error) else None
                    if module_name:
                        return f"ERROR: Missing module: {module_name}"
                return f"ERROR: {error}"
            else:
                self.logger.info(f"Output of testing code: {output}")
                return output

        except Exception as e:
            self.logger.exception(f"Error testing code: {e}")
            return f"ERROR: {e}"

    def ask_gemini_for_install_command(self, module_name):
        """
        Gets the command to install the module from the Gemini API.

        Args:
            module_name (str): The name of the module to install.

        Returns:
            str: The command to install the module, or None if the command could not be retrieved.
        """
        try:
            prompt = f"What is the correct command to install the Python module '{module_name}' using pip in a Windows PowerShell environment? Return JSON in format {{\"command\": \"command\"}}"
            response = self.api.generate_content(prompt)

            if response:
                self.logger.info(f"Response from Gemini API: {response}")

                try:
                    # Remove text before JSON and apostrophes and newline characters
                    response = response[response.find("{"):].replace("```json", "").replace("```", "").replace("\n", "").replace("\\'", "'")  # Remove text before JSON
                    response_json = json.loads(response)
                    command = response_json.get("command")
                    return command
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid response format from Gemini API: {response} - {e}")
                    self.display_result("Invalid response format from Gemini API.")
                    return None
            else:
                self.logger.warning("Gemini API returned no response.")
                self.display_result("Gemini API returned no response.")
                return None
        except Exception as e:
            self.logger.exception(f"Error getting command to install module: {e}")
            self.display_result("Error getting command to install module.")
            return None

    def install_missing_module(self, module_name):
        """
        Installs a missing module using pip.

        Args:
            module_name (str): The name of the module to install.

        Returns:
            bool: True if the module was installed successfully, False otherwise.
        """
        try:
            venv_name = self.config.get("paths").get("venv_name")
            powershell_path = self.config.get("shell").get("powershell_path")
            subprogram_dir = self.config.get("paths").get("subprogram_dir")

            # Build the command to run in PowerShell
            command = [
                powershell_path,
                "-ExecutionPolicy", "Bypass",  # Bypass script execution restrictions
                "-Command",
                f"""
                cd '{os.path.abspath(subprogram_dir)}';  # Go to the subdirectory directory
                . .\\{venv_name}\\Scripts\\Activate.ps1;  # Activate the virtual environment
                pip install {module_name};  # Install the module
                """
            ]

            self.logger.info(f"Installing missing module '{module_name}'...")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            output = stdout.decode("utf-8")
            error = stderr.decode("utf-8")

            if error:
                self.logger.error(f"Error installing module '{module_name}': {error}")
                self.display_result(f"Error installing module '{module_name}': {error}")
                return False
            else:
                self.logger.info(f"Module '{module_name}' installed successfully.")
                self.display_result(f"Module '{module_name}' installed successfully.")
                return True

        except Exception as e:
            self.logger.exception(f"Error installing module '{module_name}': {e}")
            self.display_result(f"Error installing module '{module_name}': {e}")
            return False

    def save_new_action(self, name, description, code, execution_type, file_name): # nazev stays the same to be consistent
        """
        Saves a new action to the database.

        Args:
            name (str): The name of the action.
            description (str): The description of the action.
            code (str): The code of the action.
            execution_type (str): The execution type of the action.
            file_name (str): The name of the file to save the code to.
        """
        try:
            # 1. Clean the file name
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            file_name = ''.join(c for c in file_name if c in valid_chars)  # Remove invalid characters
            file_name = file_name.replace(" ", "_")  # Replace spaces with underscores

            # 2. Resolve file name conflicts
            path = os.path.join(self.config.get("paths").get("subprogram_dir"), f"{file_name}.{execution_type}")
            i = 1
            while os.path.exists(path):
                file_name = f"{file_name}_{i}"
                path = os.path.join(self.config.get("paths").get("subprogram_dir"), f"{file_name}.{execution_type}")
                i += 1

            # 3. Save the code to a file
            if execution_type == "python":
                file = f"{file_name}.py"
            else:
                file = f"{file_name}.{execution_type}"
            with open(os.path.join(self.config.get("paths").get("subprogram_dir"), file), "w") as f:
                f.write(code)

            # 4. Save the action to the database
            try:
                self.db.add_action(name, description, file, execution_type, [])  # [] for expected_outputs
                self.logger.info(f"New action '{name}' saved to database and file '{file}'.")
                self.display_result(f"New action '{name}' saved.")
            except Exception as e:
                self.logger.error(f"Unable to save action to database but it is not a problem: {e}")
                self.display_result(f"Action '{name}' unable to save to database. But it is not a problem. File saved successfully.")


        except Exception as e:
            self.logger.exception(f"New action not saved: {e}")
            self.display_result(f"New action not saved: {e}")

    def execute_action(self, action):
        """
        Executes an external script.

        Args:
            action (dict): A dictionary containing the action details.

        Returns:
            str: The output of the script, or an error message if the script failed to execute.
        """
        name = action["name"] # Changed action["nazev"] to action["name"]
        file = action["file"] # Changed action["soubor"] to action["file"]
        execution_type = action["execution_type"] # Changed action["typ_vykonani"] to action["execution_type"]
        subprogram_dir = self.config.get("paths").get("subprogram_dir")  # Get subprogram_dir

        try:
            if execution_type == "python":
                script_path = os.path.join(subprogram_dir, file)
                command = ["python", script_path]
            elif execution_type == "cmd":
                script_path = os.path.join(subprogram_dir, file)
                command = ["cmd", "/c", script_path]
            elif execution_type == "powershell":
                script_path = os.path.join(subprogram_dir, file)
                command = [self.config.get("shell").get("powershell_path"), "-File", script_path]
            else:
                self.logger.error(f"Unknown execution type: {execution_type}")
                return f"Unknown execution type: {execution_type}"

            self.logger.info(f"Running: {command}")
            self.logger.info(f"Path to script: {script_path}")  # Output path to log

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            output = stdout.decode("utf-8")
            error = stderr.decode("utf-8")

            if error:
                self.logger.error(f"Error running script: {error}")
                return f"Error: {error}"
            else:
                self.logger.info(f"Script output: {output}")
                return output

        except FileNotFoundError:
            self.logger.error(f"File '{file}' not found.")
            return f"File '{file}' not found."
        except Exception as e:
            self.logger.exception(f"Error running script: {e}")
            return f"Error: {e}"

    def display_result(self, result):
        """
        Displays the result in the GUI text window.

        Args:
            result (str): The result to display.
        """
        self.status_text.config(state=tk.NORMAL)  # Enable editing
        self.status_text.insert(tk.END, result + "\n")
        self.status_text.config(state=tk.DISABLED)  # Disable editing
        self.status_text.see(tk.END)  # Automatically scroll to the end

    def close(self):
        """
        Closes the GUI and associated threads.
        """
        self.running = False  # Stop the thread
        self.request_thread.join()  # Wait for the thread to complete
        self.master.destroy()  # Close the window

    class TextHandler(logging.Handler):
        """
        Handler for logging to Tkinter Text widget.
        """
        def __init__(self, text):
            logging.Handler.__init__(self)
            self.text = text

        def emit(self, record):
            log_msg = self.format(record)
            self.text.config(state=tk.NORMAL)
            self.text.insert(tk.END, log_msg + "\n")
            self.text.config(state=tk.DISABLED)
            self.text.see(tk.END)

# Function to run the GUI (called from main.py)
def run_gui(api, db, config, log_level):
    root = tk.Tk()
    gui = GUI(root, api, db, config, log_level)
    root.protocol("WM_DELETE_WINDOW", gui.close)  # Handle window closing
    root.mainloop()