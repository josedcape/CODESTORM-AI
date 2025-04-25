
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

@app.route('/files')
def files():
    """Render the files explorer page."""
    return render_template('files.html')

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
        context = data.get('context', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Configuración de prompts según el agente seleccionado
        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar con tareas de programación, desde corrección de errores hasta implementación de funcionalidades completas.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas en decisiones sobre estructura de código, patrones de diseño y selección de tecnologías.",
            'advanced': "Eres un Especialista Avanzado experto en soluciones complejas e integraciones avanzadas. Puedes asesorar sobre tecnologías emergentes y soluciones sofisticadas.",
            'general': "Eres un Asistente General con conocimientos amplios de desarrollo de software y buenas prácticas."
        }
        
        # Seleccionar prompt adecuado según el agente o usar prompt por defecto
        system_prompt = agent_prompts.get(agent_id, "Eres un asistente especializado en desarrollo de software.")
        
        response = ""
        logging.info(f"Procesando mensaje con modelo: {model}")
        
        # Generar respuesta con OpenAI
        if model == 'openai' and openai_client:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                
                # Añadir mensajes de contexto previo
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] in ['user', 'assistant', 'system']:
                            messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                
                # Añadir mensaje actual
                messages.append({"role": "user", "content": user_message})
                
                completion = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7
                )
                response = completion.choices[0].message.content
                logging.info("Respuesta generada con OpenAI")
            except Exception as e:
                logging.error(f"Error with OpenAI API: {str(e)}")
                response = f"Error al conectar con OpenAI: {str(e)}"
        
        # Generar respuesta con Gemini
        elif model == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                try:
                    import google.generativeai as genai
                except ImportError:
                    # Si el módulo no está instalado, intentamos instalarlo
                    logging.warning("Módulo google.generativeai no encontrado, intentando instalarlo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "google-generativeai"])
                    import google.generativeai as genai
                
                gemini_api_key = os.environ.get('GEMINI_API_KEY')
                genai.configure(api_key=gemini_api_key)
                
                # Configurar el modelo con opciones de generación
                gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                
                # Construir prompt con contexto
                # Formato de mensajes específico para mejor comprensión por parte de Gemini
                prompt = system_prompt + "\n\n"
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        role_prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                        prompt += role_prefix + msg['content'] + "\n\n"
                
                prompt += "Usuario: " + user_message + "\n\n" + "Asistente (responde usando markdown con código formateado):"
                
                logging.debug(f"Enviando prompt a Gemini: {prompt[:200]}...")
                gemini_response = gemini_model.generate_content(prompt)
                response = gemini_response.text
                logging.info(f"Respuesta generada con Gemini: {response[:100]}...")
            except ImportError as ie:
                logging.error(f"Error al importar módulos para Gemini: {str(ie)}")
                response = f"Error: No se pudo importar el módulo google.generativeai. Por favor, ejecuta 'pip install google-generativeai' e inténtalo de nuevo."
            except Exception as e:
                logging.error(f"Error with Gemini API: {str(e)}")
                logging.error(traceback.format_exc())
                response = f"Error al conectar con Gemini: {str(e)}"
                
        # Generar respuesta con Anthropic
        elif model == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                try:
                    import anthropic
                except ImportError:
                    # Si el módulo no está instalado, lo instalamos
                    logging.warning("Módulo anthropic no encontrado, instalándolo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "anthropic"])
                    import anthropic
                
                client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
                messages = [{"role": "system", "content": system_prompt}]
                
                # Añadir mensajes de contexto
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] in ['user', 'assistant']:
                            messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                
                # Añadir mensaje actual
                messages.append({"role": "user", "content": user_message})
                
                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    messages=messages,
                    max_tokens=2000
                )
                response = completion.content[0].text
                logging.info("Respuesta generada con Anthropic")
            except Exception as e:
                logging.error(f"Error with Anthropic API: {str(e)}")
                response = f"Error al conectar con Anthropic: {str(e)}"
        
        # Si no hay modelo disponible
        else:
            response = "Lo siento, no hay un modelo de IA configurado disponible. Por favor, verifica las API keys en la configuración."
            logging.warning(f"No hay modelo disponible para: {model}")
        
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
