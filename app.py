# Flask application for Codestorm-Assistant
import os
import json
import logging
import subprocess
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import anthropic

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

if not openai_api_key:
    logging.warning("OPENAI_API_KEY not found. OpenAI features will not work.")
else:
    logging.info("OpenAI API key configured successfully.")

# Initialize API clients
openai_client = openai.OpenAI(api_key=openai_api_key)

# Initialize Anthropic client if key exists
anthropic_client = None
if anthropic_api_key:
    anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    logging.info("Anthropic API key configured successfully.")
else:
    logging.warning("ANTHROPIC_API_KEY not found. Anthropic features will not work.")

# Set session secret
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/process_instructions', methods=['POST'])
def process_instructions():
    """Process natural language instructions and convert to terminal commands."""
    try:
        data = request.json
        user_input = data.get('instruction', '')
        model_choice = data.get('model', 'openai')  # Default to OpenAI
        
        if not user_input:
            return jsonify({'error': 'No instruction provided'}), 400
        
        terminal_command = ""
        
        # Use selected model to generate command
        if model_choice == 'openai':
            if not openai_api_key:
                return jsonify({'error': 'OpenAI API key not configured'}), 500
                
            # Use OpenAI to generate terminal command
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that converts natural language instructions into terminal commands. Only output the exact command without explanations."},
                    {"role": "user", "content": f"Convert this instruction to a terminal command: {user_input}"}
                ],
                max_tokens=100
            )
            
            terminal_command = response.choices[0].message.content.strip()
            
        elif model_choice == 'anthropic':
            if not anthropic_client:
                return jsonify({'error': 'Anthropic API key not configured'}), 500
                
            # Use Anthropic to generate terminal command
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024.
                max_tokens=100,
                messages=[
                    {"role": "user", "content": f"Convert this instruction to a terminal command without any explanation: {user_input}"}
                ],
                system="You are a helpful assistant that converts natural language instructions into terminal commands. Only output the exact command without explanations."
            )
            
            terminal_command = response.content[0].text.strip()
            
        elif model_choice == 'gemini':
            return jsonify({'error': 'Gemini integration not implemented yet'}), 501
        else:
            return jsonify({'error': 'Invalid model selection'}), 400
            
        logging.debug(f"Generated command using {model_choice}: {terminal_command}")
        
        return jsonify({'command': terminal_command})
    except Exception as e:
        logging.error(f"Error processing instructions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_command', methods=['POST'])
def execute_command():
    """Execute a terminal command and return the output."""
    try:
        data = request.json
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Execute the command
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        result = {
            'stdout': stdout,
            'stderr': stderr,
            'exitCode': process.returncode
        }
        
        logging.debug(f"Command execution result: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error executing command: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_files', methods=['POST'])
def list_files():
    """List files in the specified directory."""
    try:
        data = request.json
        directory = data.get('directory', '.')
        
        # Execute ls command to list files
        process = subprocess.Popen(
            f"ls -la {directory}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return jsonify({'error': stderr}), 400
            
        # Parse the output to get file list
        lines = stdout.strip().split('\n')
        files = []
        
        # Skip the first line which contains the total count
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 9:
                file_type = 'directory' if parts[0].startswith('d') else 'file'
                file_name = ' '.join(parts[8:])
                files.append({
                    'name': file_name,
                    'type': file_type,
                    'permissions': parts[0],
                    'size': parts[4],
                    'modified': f"{parts[5]} {parts[6]} {parts[7]}"
                })
        
        return jsonify({'files': files})
    except Exception as e:
        logging.error(f"Error listing files: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
