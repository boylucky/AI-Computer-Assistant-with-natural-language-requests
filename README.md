# AI-Computer-Assistant-with-natural-language-requests

AI Computer Assistant with natural language requests to perform actions on your computer

The AI Comp Assistant project is an experimental proof of concept. This assistant allows users to convey requests for actions to be performed on their computer using natural language input (a version also exists that converts speech to text). Examples include opening a web browser to a specific page, retrieving the computer name, checking for current security updates, creating a file with specific text, or any other task you can imagine. The program then communicates with the Google Gemini API to determine how to execute the requested action on the computer. Subsequently, it attempts to perform the action, and if successful, saves the execution steps to its local database, avoiding the need to re-query the API for the same action in the future.

Therefore, this is a tool that translates textual requests into real actions on your computer. The application is written in Python and is available for download, including all source code, for you to try. However, it's crucial to exercise extreme caution when entering requests. Testing the program is at your own risk. This is purely a demonstration and proof of concept of the possibilities of AI and future computer control without needing to know where settings are located or how to perform required actions.

The application is written in Python, and the code can be further modified and customized according to individual needs. This is solely a test version of the program. It utilizes a local MariaDB database to progressively store newly acquired knowledge about the actions it can perform. However, installing a database on your local computer is not required to test the program, as it functions even without one. Without a database, the program won't save learned actions and will always query Google's Gemini AI for the execution procedure.
You can download the complete Python code of the application and run it using main.py. Before doing so, you need to activate the Python virtual environment named myAssistant (which is also included in the downloadable file package, so no additional installation is required). Before the first launch, you need to set the necessary parameters in the config.json file located in the core directory. This mainly involves inserting the API key for the Google Gemini API, which you can obtain after logging in at aistudio.google.com. If you plan to use a local MariaDB (or other) database, you also need to set the connection parameters in config.json. In this case, the program will automatically create the table structure for storing learned actions.

I welcome your comments. This is a very basic proof of concept and not a finished, robust solution. It may be suitable inspiration for anyone interested in this idea. You can freely use the code for your own projects and expand it as you see fit.
Thank you for your time, and I look forward to your comments and hearing if anyone has tried the program. However, please be extremely careful when entering actions to avoid any unintended steps. Keep in mind that this is an experimental project intended for testing purposes and not for any real production deployment. It's a proof of concept of this idea.

# Once more: Testing the program is at your own risk.

![AI Computer Assistant](AI_comp_assistant.jpg)

