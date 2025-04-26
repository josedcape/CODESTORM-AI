"""
Codestorm Assistant - Aplicación principal simplificada
Este archivo crea un blueprint de Flask con las rutas básicas para el asistente.
"""
import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from flask import Blueprint, render_template, jsonify, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

# Importaciones para las APIs
import openai
import anthropic
from anthropic import Anthropic
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crear el blueprint de Flask
app = Blueprint('codestorm', __name__,
               static_folder="static",
               template_folder="templates",
               url_prefix='')  # Importante: url_prefix vacío para que las rutas sean accesibles desde la raíz

# Inicializar clientes de API
try:
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key:
        # Configurar globalmente la API key de OpenAI
        openai.api_key = openai_api_key
        logger.info("OpenAI API configurada correctamente")
except Exception as e:
    logger.error(f"Error al configurar OpenAI API: {str(e)}")

try:
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        # No inicializamos el cliente aquí, lo haremos cuando se necesite
        logger.info("Anthropic API key disponible")
except Exception as e:
    logger.error(f"Error al configurar Anthropic API: {str(e)}")

try:
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        logger.info("Gemini API configurada correctamente")
except Exception as e:
    logger.error(f"Error al configurar Gemini API: {str(e)}")

# Funciones auxiliares para el manejo de archivos y directorios
def get_user_workspace(user_id='default'):
    """Obtiene o crea un espacio de trabajo para el usuario."""
    workspace_dir = os.path.join(os.getcwd(), 'user_workspaces', user_id)
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir

def list_files(directory='.', user_id='default'):
    """Lista archivos y directorios en una ruta especificada."""
    workspace = get_user_workspace(user_id)
    target_dir = os.path.join(workspace, directory)

    if not os.path.exists(target_dir):
        return []

    try:
        entries = []
        for entry in os.listdir(target_dir):
            entry_path = os.path.join(target_dir, entry)
            entry_type = 'directory' if os.path.isdir(entry_path) else 'file'

            if entry_type == 'file':
                file_size = os.path.getsize(entry_path)
                file_extension = os.path.splitext(entry)[1].lower()[1:] if '.' in entry else ''

                entries.append({
                    'name': entry,
                    'type': entry_type,
                    'path': os.path.join(directory, entry) if directory != '.' else entry,
                    'size': file_size,
                    'extension': file_extension
                })
            else:
                entries.append({
                    'name': entry,
                    'type': entry_type,
                    'path': os.path.join(directory, entry) if directory != '.' else entry
                })

        return entries
    except Exception as e:
        logger.error(f"Error al listar archivos: {str(e)}")
        return []

# Rutas principales
@app.route('/')
def index():
    """Ruta principal que sirve la página index.html."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Ruta al panel de control."""
    return render_template('dashboard.html')

@app.route('/chat')
def chat():
    """Ruta a la página de chat."""
    agent_id = request.args.get('agent', 'general')
    return render_template('chat.html', agent_id=agent_id)

# APIs para manejo de archivos
@app.route('/api/files', methods=['GET'])
def api_list_files():
    """API para listar archivos del workspace."""
    try:
        user_id = request.args.get('user_id', 'default')
        directory = request.args.get('directory', '.')

        files = list_files(directory, user_id)

        return jsonify({
            'success': True,
            'files': files,
            'directory': directory
        })
    except Exception as e:
        logger.error(f"Error al listar archivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/read', methods=['GET'])
def api_read_file():
    """API para leer el contenido de un archivo."""
    try:
        user_id = request.args.get('user_id', 'default')
        file_path = request.args.get('file_path')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo'
            }), 400

        workspace = get_user_workspace(user_id)
        full_path = os.path.join(workspace, file_path)

        # Verificar path traversal
        if not os.path.normpath(full_path).startswith(os.path.normpath(workspace)):
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400

        # Verificar que el archivo existe
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({
                'success': False,
                'error': 'El archivo no existe'
            }), 404

        # Leer el archivo
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'file_path': file_path,
            'content': content
        })
    except Exception as e:
        logger.error(f"Error al leer archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/create', methods=['POST'])
def api_create_file():
    """API para crear o actualizar un archivo."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        file_path = data.get('file_path')
        content = data.get('content', '')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo'
            }), 400

        workspace = get_user_workspace(user_id)
        full_path = os.path.join(workspace, file_path)

        # Verificar path traversal
        if not os.path.normpath(full_path).startswith(os.path.normpath(workspace)):
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400

        # Crear directorios si no existen
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Escribir contenido al archivo
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({
            'success': True,
            'file_path': file_path
        })
    except Exception as e:
        logger.error(f"Error al crear archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/delete', methods=['DELETE'])
def api_delete_file():
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo no especificada'
            }), 400

        file_path = data['file_path']
        user_id = request.args.get('user_id', 'default')
        workspace = get_user_workspace(user_id)
        full_path = os.path.join(workspace, file_path)

        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)

        return jsonify({
            'success': True,
            'message': 'Elemento eliminado correctamente'
        })

    except Exception as e:
        logger.error(f"Error al eliminar archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API para ejecución de comandos
@app.route('/api/execute', methods=['POST'])
def api_execute_command():
    """API para ejecutar comandos directamente."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        command = data.get('command')

        if not command:
            return jsonify({
                'success': False,
                'error': 'Se requiere un comando'
            }), 400

        workspace = get_user_workspace(user_id)

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workspace
        )

        stdout, stderr = process.communicate(timeout=30)
        status = process.returncode

        result = {
            'success': True,
            'command': command,
            'stdout': stdout.decode('utf-8', errors='replace'),
            'stderr': stderr.decode('utf-8', errors='replace'),
            'status': status
        }

        return jsonify(result)
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Tiempo de ejecución agotado (30s)'
        }), 504
    except Exception as e:
        logger.error(f"Error al ejecutar comando: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# APIs para chat y generación de contenido
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API para chat con agentes especializados."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        message = data.get('message')
        agent_id = data.get('agent_id', 'general')
        model_choice = data.get('model', 'openai')  # Opción de modelo a usar
        context = data.get('context', [])  # Historial de conversación

        if not message:
            return jsonify({
                'success': False,
                'error': 'Se requiere un mensaje'
            }), 400

        # Configurar prompt según el agente
        agent_prompts = {
            'developer': "Eres un Desarrollador Experto especializado en programación y resolución de problemas técnicos.",
            'architect': "Eres un Arquitecto de Software especializado en diseño de sistemas y patrones arquitectónicos.",
            'advanced': "Eres un Especialista Avanzado con amplio conocimiento en tecnologías emergentes y soluciones complejas.",
            'general': "Eres un Asistente General preparado para ayudar con cualquier consulta de desarrollo."
        }

        system_prompt = agent_prompts.get(agent_id, agent_prompts['general'])
        response = ""

        # Formateamos el contexto para que sea consistente
        formatted_context = []
        for msg in context:
            role = msg.get('role', 'user')
            if role not in ['user', 'assistant', 'system']:
                role = 'user'
            formatted_context.append({
                "role": role,
                "content": msg.get('content', '')
            })

        # Generar respuesta usando el modelo seleccionado
        if model_choice == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                # Usar Anthropic Claude con la forma correcta
                client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

                # Preparar mensajes en formato Anthropic
                messages = [{"role": "system", "content": system_prompt}]

                # Añadir mensajes de contexto
                for msg in formatted_context:
                    messages.append({"role": msg['role'], "content": msg['content']})

                # Añadir el mensaje actual del usuario
                messages.append({"role": "user", "content": message})

                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=messages
                )

                response = completion.content[0].text
            except Exception as e:
                logger.error(f"Error con API de Anthropic: {str(e)}")
                response = f"Lo siento, hubo un problema al procesar tu solicitud con Anthropic: {str(e)}"

        elif model_choice == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                # Verificar si Gemini ya está configurado
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

                model = genai.GenerativeModel('gemini-1.5-pro')

                # Construir el prompt con contexto para Gemini
                full_prompt = system_prompt + "\n\n"

                for msg in formatted_context:
                    prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                    full_prompt += prefix + msg['content'] + "\n\n"

                full_prompt += "Usuario: " + message + "\n\nAsistente:"

                gemini_response = model.generate_content(full_prompt)
                response = gemini_response.text
            except Exception as e:
                logger.error(f"Error con API de Gemini: {str(e)}")
                response = f"Lo siento, hubo un problema al procesar tu solicitud con Gemini: {str(e)}"

        else:
            # Usar OpenAI (por defecto)
            try:
                # Usar el cliente de OpenAI correctamente
                client = openai.OpenAI()  # Usa la API key configurada globalmente

                # Preparar mensajes para OpenAI
                messages = [{"role": "system", "content": system_prompt}]

                # Añadir mensajes de contexto
                for msg in formatted_context:
                    messages.append({"role": msg['role'], "content": msg['content']})

                # Añadir el mensaje actual del usuario
                messages.append({"role": "user", "content": message})

                completion = client.chat.completions.create(
                    model="gpt-4o",  # Modelo más reciente
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )

                response = completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Error con API de OpenAI: {str(e)}")
                # Fallback a respuesta simple en caso de error
                agent_name = {
                    'developer': "Desarrollador Experto",
                    'architect': "Arquitecto de Software",
                    'advanced': "Especialista Avanzado",
                    'general': "Asistente General"
                }.get(agent_id, "Asistente General")

                response = f"Soy {agent_name}. Lo siento, tuve un problema para procesar tu mensaje: '{message}'. ¿Podrías intentarlo de nuevo?"

        return jsonify({
            'success': True,
            'message': message,
            'response': response,
            'agent_id': agent_id
        })
    except Exception as e:
        logger.error(f"Error en el chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process-instruction', methods=['POST'])
def api_process_instruction():
    """API para procesar instrucciones en lenguaje natural."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        instruction = data.get('instruction')
        model_choice = data.get('model', 'openai')  # Modelo a usar

        if not instruction:
            return jsonify({
                'success': False,
                'error': 'Se requiere una instrucción'
            }), 400

        # Detectar si es un comando para ejecutar
        command_match = re.search(r'^ejecuta(?:r)?[:\s]+(.+)$', instruction, re.IGNORECASE)
        if command_match:
            command = command_match.group(1).strip()
            workspace = get_user_workspace(user_id)

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workspace
            )

            stdout, stderr = process.communicate(timeout=30)
            status = process.returncode

            return jsonify({
                'success': True,
                'action': 'execute_command',
                'command': command,
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace'),
                'status': status
            })

        # Detectar si es una instrucción para crear un archivo
        file_match = re.search(r'^crea(?:r)?[:\s]+([^\s]+)\s+(?:contenido|con)[:\s]+(.+)$', instruction, re.IGNORECASE | re.DOTALL)
        if file_match:
            file_path = file_match.group(1).strip()
            content = file_match.group(2).strip()

            # Limpiar comillas o triple comillas si están presentes
            if content.startswith('"""') and content.endswith('"""'):
                content = content[3:-3]
            elif content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            elif content.startswith("'") and content.endswith("'"):
                content = content[1:-1]

            workspace = get_user_workspace(user_id)
            full_path = os.path.join(workspace, file_path)

            # Crear directorios si no existen
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return jsonify({
                'success': True,
                'action': 'create_file',
                'file_path': file_path,
                'content': content
            })

        # Para cualquier otra instrucción, usar IA para interpretarla
        # Utilizamos el modelo seleccionado para procesar la instrucción
        instruction_response = ""

        if model_choice == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[
                        {"role": "system", "content": "Eres un asistente que ayuda a interpretar instrucciones y responder preguntas."},
                        {"role": "user", "content": f"Responde a la siguiente instrucción: {instruction}"}
                    ]
                )
                instruction_response = response.content[0].text
            except Exception as e:
                logger.error(f"Error al procesar instrucción con Anthropic: {str(e)}")
                instruction_response = f"No pude procesar tu instrucción: {str(e)}"

        elif model_choice == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"Eres un asistente que ayuda a interpretar instrucciones. Responde a lo siguiente: {instruction}"

                gemini_response = model.generate_content(prompt)
                instruction_response = gemini_response.text
            except Exception as e:
                logger.error(f"Error al procesar instrucción con Gemini: {str(e)}")
                instruction_response = f"No pude procesar tu instrucción: {str(e)}"

        else:
            # OpenAI por defecto
            try:
                client = openai.OpenAI()  # Usa la API key configurada globalmente

                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un asistente que ayuda a interpretar instrucciones y responder preguntas."},
                        {"role": "user", "content": instruction}
                    ],
                    temperature=0.5,
                    max_tokens=1000
                )

                instruction_response = completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Error al procesar instrucción con OpenAI: {str(e)}")
                instruction_response = f"No pude procesar tu instrucción: {str(e)}"

        # Devolver la respuesta procesada
        return jsonify({
            'success': True,
            'action': 'chat',
            'response': instruction_response
        })
    except Exception as e:
        logger.error(f"Error al procesar instrucción: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Servir archivos estáticos
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos desde el directorio static."""
    return send_from_directory('static', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check the health status of the application."""
    try:
        # Check API configurations
        apis = {
            "openai": "ok" if os.environ.get('OPENAI_API_KEY') else "not configured",
            "anthropic": "ok" if os.environ.get('ANTHROPIC_API_KEY') else "not configured",
            "gemini": "ok" if os.environ.get('GEMINI_API_KEY') else "not configured"
        }

        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "apis": apis
        })
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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

        try:
            client = openai.OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4",  # Corregido de gpt-4o a gpt-4
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            response = completion.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in content generation: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

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

# Fin del blueprint de Codestorm
