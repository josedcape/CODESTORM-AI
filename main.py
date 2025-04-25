
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import logging
import json
from dotenv import load_dotenv
import openai
import requests
import traceback
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set session secret
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Get API keys from environment
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# Initialize API clients with error handling
openai_client = None
if openai_api_key:
    try:
        openai.api_key = openai_api_key
        openai_client = openai.OpenAI()
        logging.info("OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {str(e)}")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for the application."""
    try:
        # Check API configurations
        apis = {
            "openai": "ok" if os.environ.get('OPENAI_API_KEY') else "not configured",
            "anthropic": "ok" if os.environ.get('ANTHROPIC_API_KEY') else "not configured",
            "gemini": "ok" if os.environ.get('GEMINI_API_KEY') else "not configured"
        }

        return jsonify({
            "status": "ok",
            "timestamp": time.time(),
            "version": "1.0.0",
            "apis": apis
        })
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Process chat messages using the selected model."""
    try:
        data = request.json
        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'architect')
        model = data.get('model', 'openai')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Simple test response
        response = f"Respuesta simulada del asistente ({model}/{agent_id}): He recibido tu mensaje '{user_message[:30]}...'"
        
        # Intentar usar OpenAI si está disponible
        if model == 'openai' and openai_client:
            try:
                completion = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un asistente útil especializado en desarrollo de software."},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7
                )
                response = completion.choices[0].message.content
            except Exception as e:
                logging.error(f"Error with OpenAI API: {str(e)}")
                response = f"Error al procesar con OpenAI: {str(e)}"
        
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in handle_chat: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'response': f"Error inesperado: {str(e)}"
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Fallback endpoint for content generation."""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
            
        # Simple fallback response
        response = f"Respuesta generada para: {message[:50]}..."
        
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        logging.error(f"Error in generate endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
