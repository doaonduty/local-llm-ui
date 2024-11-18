from flask import Flask, jsonify, request,Response, current_app
from langchain_ollama import ChatOllama
import subprocess
import logging

# Create a logger
logger = logging.getLogger(__name__)

# Set the logging level
logger.setLevel(logging.INFO)

# Create a file handler to log messages to a file
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)

# Create a formatter to format the log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

class FlaskApp:
    """
    Flask Application class for LocalLLMUI
    """
    def __init__(self):
        """
        Initializes the Flask application and loads the ChatOllama model
        """
        self.app = Flask(__name__)
        self.model = None
        self.app.config["LOG_LEVEL"]="INFO"
        self.load_model()
    

    def load_model(self):
        model_name = "hf.co/doaonduty/llama-3.1-8b-instruct-gguf"
        try:
            # Check if the model is present
            subprocess.check_output(["ollama", "list", model_name]).decode("utf-8")
            logger.info(f"Model {model_name} is present, loading it...")
            self.model = ChatOllama(model=model_name)
        except subprocess.CalledProcessError:
            # Model is not present, pull it
            logger.error(f"Model {model_name} is not present, pulling it...")
            subprocess.run(["ollama", "run", "model", model_name])
            self.model = ChatOllama(model=model_name)
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None

    def index(self):
        """
        Returns the HTML template for the index page
        """
        html = """
        <html>
        <head>
        <style>
        body {
            background-color: #2c3e50;
            font-family: Arial, sans-serif;
            color: #fff;
        }
        .container {
            width: 80%;
            margin: 40px auto;
            text-align: center;
        }
        .conversation-area {
            width: 100%;
            height: 500px;
            padding: 20px;
            border: 1px solid #337ab7;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            position: relative;
            background-color: #fff;
            color: #333;
        }
        #conversation {
            padding: 10px;
            font-size: 16px;
            border: none;
            border-radius: 10px;
            width: 100%;
            height: 500px;
            overflow-y: auto;
            background-color: #fff;
            text-align: left;
        }
        .input-area {
            width: 100%;
            padding: 20px;
            border: 1px solid #337ab7;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            align-items: center;
            display: flex;
            background-color: #fff;
        }
        .input-field {
            width: 75%;
            padding: 10px;
            border: 1px solid #337ab7;
            border-radius: 10px;
        }
        .dropdown {
            width: 15%;
            padding: 10px;
            border: 1px solid #337ab7;
            border-radius: 10px;
        }
        .button {
            width: 10%;
            margin-left: 10px;
            padding: 10px;
            border: 1px solid #8e44ad;
            border-radius: 10px;
            background-color: #8e44ad;
            color: #fff;
            cursor: pointer;
        }
        .button:hover {
            background-color: #7a288a;
        }
        .loader {
            border: 5px solid #f3f3f3; /* Light grey */
            border-top: 5px solid #337ab7; /* Blue */
            border-radius: 50%;
            width: 250px;
            height: 250px;
            position: absolute;
            top: 0%;
            left: 0%;
            transform: translate(-50%, -50%);
            z-index: 1;
        }

        </style>
        </head>
        <body>
        <div class="container">
            <h1 style="color: #fff;">Local LLM UI</h1>
            <div class="conversation-area">
                <div id="loader" style="display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1;"></div>
                <!-- <textarea id="conversation" style="width: 100%; height: 100%; resize: none;"></textarea> -->
                <div id="conversation" style="width: 100%; height: 500px; overflow-y: auto;"></div>
            </div>
            <div class="input-area">
                <input type="text" id="input" class="input-field" placeholder="Enter your question">
                <button id="send" class="button">Send</button>
            </div>
            <h4 style="text-align: center; margin-top: 10px; color: #fff;">
    
        </div>
        <script>
        const inputField = document.getElementById('input');
        const sendButton = document.getElementById('send');
        const conversationField = document.getElementById('conversation');
        const endpointSelect = document.getElementById('endpoint');

        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendButton.click();
            }
        });
        sendButton.addEventListener('click', async () => {
        console.log('Send button clicked');
        const userInput = inputField.value;
        console.log('User input:', userInput);
        
        const endpoint = 'chat'
        console.log('Endpoint:', endpoint);
        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        loader.innerHTML = '<img class="loader" src="https://c.tenor.com/fVGbvf-NwC8AAAAC/tenor.gif" />';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userInput }),
        });
        console.log('Response:', response);
        const data = await response.json();
        console.log('Data:', data);
        loader.style.display = 'none';
        
        const queryElement = document.createElement('p');
        queryElement.innerHTML = '<b>Query:</b> <i>' + userInput + '</i>';
        console.log('Appending response to conversationField...');
        conversationField.appendChild(queryElement);

        
        const responseElement = document.createElement('p');
        responseElement.innerHTML = '<b>Response:</b> <br> <i>' + data.response + '</i> <br>';
        
        conversationField.appendChild(responseElement);
        console.log('Response appended.');
        conversationField.scrollTop = conversationField.scrollHeight;
        inputField.value = '';
    });
        </script>
        </body>
        </html>
        """
        return html

    def chat_endpoint(self):
        """
        Handles POST requests to the /chat endpoint

        Returns a JSON response with the model's response to the user's input
        """
        if self.model is None:
            current_app.logger.error("Ollama model not loaded")
            return jsonify({'error': 'Ollama model not loaded'})

        try:
            user_input = request.json['message']
            current_app.logger.info(f"Received message: {user_input}")
            result = self.model.invoke(user_input)
            current_app.logger.info(f"Returned response: {result.content}")
            return jsonify({'response': result.content})
        except Exception as e:
            return jsonify({'error': str(e)})
          
    def run(self):
        """
        Runs the Flask application
        """
        if self.model is None:
            current_app.logger.error("Cannot start application without Ollama model. Exiting...")
            return
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/chat', view_func=self.chat_endpoint, methods=['POST'])
        self.app.run(debug=True)

class Main:
    """
    Main class for initializing and running the applicaiton
    """
    def __init__(self):
        self.flask_app = FlaskApp()

    def run(self):
        self.flask_app.run()

if __name__ == '__main__':
    main = Main()
    main.run()
