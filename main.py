from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import os
import json
import uuid
import datetime
import time
import random
from datetime import datetime
from dotenv import load_dotenv
import threading
import logging
import openai
import google.generativeai as genai
import subprocess
import shutil
from pathlib import Path
import traceback
import re
import threading
from constructor_routes import constructor_bp
from xterm_terminal import xterm_bp, init_xterm_blueprint

# Configurar logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

# Inicializar app Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
from flask_cors import CORS
CORS(app)
from flask_socketio import SocketIO, emit
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading',
                    ping_timeout=60, ping_interval=25, logger=True, engineio_logger=True)

# Register constructor blueprint
try:
    app.register_blueprint(constructor_bp)
    logging.info("Constructor blueprint registered successfully")

    # Asegurar que los directorios necesarios para el constructor existan
    os.makedirs('user_workspaces/projects', exist_ok=True)

    # Precargar estado del constructor
    from constructor_routes import project_status

    # Reiniciar cualquier proyecto que se haya quedado en progreso
    try:
        for proj_dir in os.listdir('user_workspaces/projects'):
            if proj_dir.startswith('app_'):
                proj_id = proj_dir
                if proj_id not in project_status:
                    logging.info(f"Preloading project status for {proj_id}")
                    project_status[proj_id] = {
                        'status': 'completed',
                        'progress': 100,
                        'current_stage': 'Proyecto completado exitosamente',
                        'console_messages': [
                            {'time': time.time(), 'message': 'Proyecto recuperado del sistema de archivos'}
                        ],
                        'start_time': time.time() - 3600,
                        'completion_time': time.time() - 60
                    }
    except Exception as load_err:
        logging.warning(f"Error preloading project statuses: {str(load_err)}")

except Exception as e:
    logging.error(f"Error registering constructor blueprint: {str(e)}")

# Recargar variables de entorno para asegurar que tenemos las últimas
load_dotenv(override=True)

# Función para obtener y validar clave API
def get_and_validate_api_key(env_var_name, service_name, validation_func=None):
    api_key = os.getenv(env_var_name)
    if not api_key:
        logging.warning(f"{service_name} API key no configurada - funcionalidades de {service_name} estarán deshabilitadas")
        return None

    # Si no hay función de validación, simplemente retornar la clave
    if not validation_func:
        logging.info(f"{service_name} API key configurada: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else '***'}")
        return api_key

    try:
        # Validar la clave API usando la función proporcionada
        is_valid = validation_func(api_key)
        if is_valid:
            logging.info(f"{service_name} API key verificada y configurada: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else '***'}")
            return api_key
        else:
            logging.error(f"La clave de {service_name} no es válida.")
            return None
    except Exception as e:
        logging.error(f"Error al validar la clave de {service_name}: {str(e)}")
        logging.warning(f"La clave de {service_name} no pudo ser validada o el servicio no está disponible")
        return None

# Validadores para cada API
def validate_openai_key(key):
    if not key:
        return False
    try:
        openai.api_key = key
        client = openai.OpenAI(api_key=key)
        _ = client.models.list()
        return True
    except Exception as e:
        logging.error(f"Error al validar OpenAI API: {str(e)}")
        return False

def validate_anthropic_key(key):
    if not key:
        return False
    try:
        # Importar solo si la clave está configurada
        import anthropic
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        _ = client.models.list()
        return True
    except Exception as e:
        logging.error(f"Error al validar Anthropic API: {str(e)}")
        return False

def validate_gemini_key(key):
    if not key:
        return False
    try:
        genai.configure(api_key=key)
        models = genai.list_models()
        _ = list(models)  # Forzar evaluación
        return True
    except Exception as e:
        logging.error(f"Error al validar Gemini API: {str(e)}")
        return False

# Configurar claves API desde variables de entorno
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Validar las claves API
openai_valid = validate_openai_key(openai_api_key) if openai_api_key else False
anthropic_valid = validate_anthropic_key(anthropic_api_key) if anthropic_api_key else False
gemini_valid = validate_gemini_key(gemini_api_key) if gemini_api_key else False

# Almacenar las claves API en la configuración de la aplicación para acceso global
app.config['API_KEYS'] = {
    'openai': openai_api_key if openai_valid else None,
    'anthropic': anthropic_api_key if anthropic_valid else None,
    'gemini': gemini_api_key if gemini_valid else None
}

# Mensaje informativo sobre el estado de las APIs
if not any([openai_api_key, anthropic_api_key, gemini_api_key]):
    logging.error("¡ADVERTENCIA! Ninguna API está configurada. El sistema funcionará en modo degradado.")
    print("=" * 80)
    print("⚠️  NINGUNA API DE IA ESTÁ CONFIGURADA")
    print("El sistema funcionará en modo degradado con plantillas predefinidas.")
    print("Para habilitar la generación de código real, configure al menos una de las siguientes claves API:")
    print("- OPENAI_API_KEY")
    print("- ANTHROPIC_API_KEY")
    print("- GEMINI_API_KEY")
    print("=" * 80)
else:
    apis_configuradas = []
    if openai_valid:
        apis_configuradas.append("OpenAI")
    if anthropic_valid:
        apis_configuradas.append("Anthropic")
    if gemini_valid:
        apis_configuradas.append("Gemini")

    print("=" * 80)
    print(f"✅ APIs configuradas: {', '.join(apis_configuradas)}")
    print("El sistema generará código real utilizando los modelos de IA disponibles.")
    print("=" * 80)

class FileSystemManager:
    def __init__(self, socketio):
        self.socketio = socketio

    def get_user_workspace(self, user_id='default'):
        """Obtener o crear un directorio de trabajo para el usuario."""
        workspace_path = Path("./user_workspaces") / user_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        return workspace_path

    def notify_terminals(self, user_id, data, exclude_terminal=None):
        """Notificar a todas las terminales de un usuario sobre la ejecución de comandos."""
        self.socketio.emit('command_result', data, room=user_id)

    def execute_command(self, command, user_id='default', notify=True, terminal_id=None):
        """Ejecuta un comando en el workspace del usuario."""
        try:
            workspace_dir = self.get_user_workspace(user_id)
            current_dir = os.getcwd()
            os.chdir(workspace_dir)

            logging.info(f"Ejecutando comando: '{command}' en workspace: {workspace_dir}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            os.chdir(current_dir)

            output = result.stdout if result.returncode == 0 else result.stderr
            success = result.returncode == 0

            if notify and terminal_id:
                self.notify_terminals(user_id, {
                    'output': output,
                    'success': success,
                    'command': command,
                    'terminal_id': terminal_id
                })

            file_modifying_commands = ['mkdir', 'touch', 'rm', 'cp', 'mv']
            if any(cmd in command.split() for cmd in file_modifying_commands):
                self.socketio.emit('file_system_changed', {
                    'user_id': user_id,
                    'command': command,
                    'timestamp': time.time()
                }, room=user_id)

            return {
                'output': output,
                'success': success,
                'command': command
            }

        except subprocess.TimeoutExpired:
            logging.error(f"Timeout al ejecutar comando: {command}")
            return {
                'output': 'Error: El comando tardó demasiado tiempo en ejecutarse',
                'success': False,
                'command': command
            }
        except Exception as e:
            logging.error(f"Error al ejecutar comando: {str(e)}")
            return {
                'output': f'Error: {str(e)}',
                'success': False,
                'command': command
            }

def process_natural_language_to_command(text):
    """Convierte lenguaje natural a comandos de terminal."""
    command_map = {
        "listar": "ls -la",
        "mostrar archivos": "ls -la",
        "mostrar directorio": "ls -la",
        "ver archivos": "ls -la",
        "fecha": "date",
        "hora": "date +%H:%M:%S",
        "calendario": "cal",
        "quien soy": "whoami",
        "donde estoy": "pwd",
        "limpiar": "clear",
        "sistema": "uname -a",
        "memoria": "free -h",
        "espacio": "df -h",
        "procesos": "ps aux"
    }

    text_lower = text.lower()

    for key, cmd in command_map.items():
        if key in text_lower:
            return cmd

    if "crear" in text_lower and "carpeta" in text_lower:
        folder_name = text_lower.split("carpeta")[-1].strip()
        if folder_name:
            return f"mkdir -p {folder_name}"

    elif "crear" in text_lower and "archivo" in text_lower:
        file_name = text_lower.split("archivo")[-1].strip()
        if file_name:
            return f"touch {file_name}"

    elif "eliminar" in text_lower or "borrar" in text_lower:
        target = text_lower.replace("eliminar", "").replace("borrar", "").strip()
        if target:
            return f"rm -rf {target}"

    return text

def get_user_workspace(user_id='default'):
    """Obtener o crear un directorio de trabajo para el usuario."""
    workspace_path = Path("./user_workspaces") / user_id
    workspace_path.mkdir(parents=True, exist_ok=True)
    return workspace_path

@app.route('/api/file/content', methods=['GET'])
def get_file_content():
    """Obtener el contenido de un archivo."""
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo'
            }), 400

        # Obtener workspace del usuario
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Crear ruta completa y verificar seguridad
        target_path = os.path.join(workspace_path, file_path)
        if not os.path.normpath(target_path).startswith(os.path.normpath(workspace_path)):
            return jsonify({
                'success': False,
                'error': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
            }), 403

        # Verificar que el archivo existe
        if not os.path.exists(target_path) or os.path.isdir(target_path):
            return jsonify({
                'success': False,
                'error': 'El archivo no existe o es un directorio'
            }), 404

        # Leer contenido del archivo
        with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'content': content,
            'file_path': file_path
        })

    except Exception as e:
        logging.error(f"Error al obtener contenido del archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/save', methods=['POST'])
def save_file_content():
    """Guardar cambios en un archivo."""
    try:
        data = request.json
        if not data or 'file_path' not in data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo y contenido'
            }), 400

        file_path = data['file_path']
        content = data['content']

        # Obtener workspace del usuario
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Crear ruta completa y verificar seguridad
        target_path = os.path.join(workspace_path, file_path)
        if not os.path.normpath(target_path).startswith(os.path.normpath(workspace_path)):
            return jsonify({
                'success': False,
                'error': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
            }), 403

        # Crear directorios si no existen
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Escribir contenido al archivo
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Notificar cambio si es posible
        try:
            socketio.emit('file_change', {
                'type': 'update',
                'file_path': file_path,
                'user_id': user_id,
                'timestamp': time.time()
            }, room=user_id)
        except Exception as notify_error:
            logging.warning(f"Error al notificar cambio de archivo: {str(notify_error)}")

        return jsonify({
            'success': True,
            'message': 'Archivo guardado correctamente',
            'file_path': file_path
        })

    except Exception as e:
        logging.error(f"Error al guardar archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/session', methods=['GET'])
def session_info():
    """Return session information for the current user."""
    user_id = session.get('user_id', 'default')
    file_system_manager = FileSystemManager(socketio)
    workspace = file_system_manager.get_user_workspace(user_id)

    return jsonify({
        'user_id': user_id,
        'workspace': str(workspace),
        'status': 'active'
    })

def watch_workspace_files():
    """Observa cambios en los archivos del workspace y notifica a los clientes."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class WorkspaceHandler(FileSystemEventHandler):
            def on_any_event(self, event):
                try:
                    if event.src_path.endswith('~') or '/.' in event.src_path:
                        return

                    event_type = 'modified'
                    if event.event_type == 'created':
                        event_type = 'create'
                    elif event.event_type == 'deleted':
                        event_type = 'delete'
                    elif event.event_type == 'moved':
                        event_type = 'move'

                    workspace_dir = os.path.abspath('./user_workspaces')
                    rel_path = os.path.relpath(event.src_path, workspace_dir)

                    parts = rel_path.split(os.sep)
                    user_id = parts[0] if len(parts) > 0 else 'default'

                    socketio.emit('file_change', {
                        'type': event_type,
                        'file': {'path': rel_path},
                        'user_id': user_id,
                        'timestamp': time.time()
                    }, room=user_id)

                    socketio.emit('file_sync', {
                        'refresh': True,
                        'user_id': user_id,
                        'timestamp': time.time()
                    }, room=user_id)

                    logging.debug(f"Cambio detectado: {event_type} - {rel_path}")

                except Exception as e:
                    logging.error(f"Error en manejador de eventos de archivos: {str(e)}")

        workspace_dir = os.path.abspath('./user_workspaces')
        os.makedirs(workspace_dir, exist_ok=True)

        event_handler = WorkspaceHandler()
        observer = Observer()
        observer.schedule(event_handler, workspace_dir, recursive=True)
        observer.start()

        logging.info(f"Observador de archivos iniciado para: {workspace_dir}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    except ImportError:
        logging.warning("No se pudo importar watchdog. El observador de archivos no estará disponible.")
    except Exception as e:
        logging.error(f"Error en observador de archivos: {str(e)}")

def handle_chat_internal(request_data):
    """Procesa solicitudes de chat y devuelve respuestas."""
    try:
        user_message = request_data.get('message', '')
        agent_id = request_data.get('agent_id', 'general')
        model_choice = request_data.get('model', 'gemini')
        context = request_data.get('context', [])

        if not user_message:
            return {'error': 'No se proporcionó un mensaje', 'response': None}

        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar a los usuarios con tareas de programación, desde la corrección de errores hasta la implementación de funcionalidades completas.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas a los usuarios a tomar decisiones sobre la estructura del código, patrones de diseño y selección de tecnologías.",
            'advanced': "Eres un Agente Avanzado de Software con experiencia en integraciones complejas y funcionalidades avanzadas. Puedes asesorar sobre tecnologías emergentes, optimización de rendimiento y soluciones a problemas técnicos sofisticados.",
            'general': "Eres un asistente de desarrollo de software experto y útil. Respondes preguntas y ayudas con tareas de programación de manera clara y concisa."
        }

        system_prompt = agent_prompts.get(agent_id, agent_prompts['general'])

        formatted_context = []
        for msg in context:
            role = msg.get('role', 'user')
            if role not in ['user', 'assistant', 'system']:
                role = 'user'
            formatted_context.append({
                "role": role,
                "content": msg.get('content', '')
            })

        if model_choice == 'openai':
            if app.config['API_KEYS'].get('openai'):
                try:
                    messages = [{"role": "system", "content": system_prompt}]
                    for msg in formatted_context:
                        messages.append({"role": msg['role'], "content": msg['content']})
                    messages.append({"role": "user", "content": user_message})

                    openai_model = "gpt-4o"

                    openai_client = openai.OpenAI(api_key=app.config['API_KEYS'].get('openai'))
                    completion = openai_client.chat.completions.create(
                        model=openai_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    response = completion.choices[0].message.content
                    logging.info(f"Respuesta generada con OpenAI ({openai_model}): {response[:100]}...")

                    return {'response': response, 'error': None}
                except Exception as e:
                    logging.error(f"Error con API de OpenAI: {str(e)}")
                    return {'response': f"Error con OpenAI API: {str(e)}", 'error': None}
            else:
                return {'response': f"El modelo 'openai' no está disponible en este momento. Por favor configura una clave API en el panel de Secrets o selecciona otro modelo.", 'error': None}

        elif model_choice == 'anthropic':
            if app.config['API_KEYS'].get('anthropic'):
                try:
                    import anthropic
                    from anthropic import Anthropic

                    client = Anthropic(api_key=app.config['API_KEYS'].get('anthropic'))

                    messages = []
                    for msg in formatted_context:
                        messages.append({"role": msg['role'], "content": msg['content']})
                    messages.append({"role": "user", "content": user_message})

                    completion = client.messages.create(
                        model="claude-3-5-sonnet-latest",
                        messages=messages,
                        max_tokens=2000,
                        temperature=0.7,
                        system=system_prompt
                    )

                    response = completion.content[0].text
                    logging.info(f"Respuesta generada con Anthropic: {response[:100]}...")

                    return {'response': response, 'error': None}
                except Exception as e:
                    logging.error(f"Error con API de Anthropic: {str(e)}")
                    return {'response': f"Error con Anthropic API: {str(e)}", 'error': None}
            else:
                return {'response': f"El modelo 'anthropic' no está disponible en este momento. Por favor configura una clave API en el panel de Secrets o selecciona otro modelo.", 'error': None}

        elif model_choice == 'gemini':
            if app.config['API_KEYS'].get('gemini'):
                try:
                    # Make sure Gemini is configured properly
                    genai.configure(api_key=app.config['API_KEYS'].get('gemini'))

                    model = genai.GenerativeModel('gemini-1.5-pro')

                    full_prompt = system_prompt + "\n\n"
                    for msg in formatted_context:
                        role_prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                        full_prompt += role_prefix + msg['content'] + "\n\n"
                    full_prompt += "Usuario: " + user_message + "\n\nAsistente: "

                    gemini_response = model.generate_content(full_prompt)
                    response = gemini_response.text
                    logging.info(f"Respuesta generada con Gemini: {response[:100]}...")

                    return {'response': response, 'error': None}
                except Exception as e:
                    logging.error(f"Error con API de Gemini: {str(e)}")
                    return {'response': f"Error con Gemini API: {str(e)}", 'error': None}
            else:
                return {'response': f"El modelo 'gemini' no está disponible en este momento. Por favor configura una clave API en el panel de Secrets o selecciona otro modelo.", 'error': None}
        else:
            available_models = []
            if app.config['API_KEYS'].get('openai'):
                available_models.append("'openai'")
            if app.config['API_KEYS'].get('anthropic'):
                available_models.append("'anthropic'")
            if app.config['API_KEYS'].get('gemini'):
                available_models.append("'gemini'")

            if available_models:
                available_models_text = ", ".join(available_models)
                message = f"El modelo '{model_choice}' no está soportado. Por favor, selecciona uno de los siguientes modelos disponibles: {available_models_text}."
            else:
                message = "No hay modelos disponibles en este momento. Por favor configura al menos una API key en el panel de Secrets (OpenAI, Anthropic o Gemini)."

            logging.warning(f"Modelo no disponible: {model_choice}")
            return {
                'response': message,
                'error': None,
                'available_models': available_models
            }

    except Exception as e:
        logging.error(f"Error general en handle_chat_internal: {str(e)}")
        return {'error': str(e), 'response': None}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def simple_health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')




@app.route('/api/process_code', methods=['POST'])
def process_code():
    """API para procesar y corregir código."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        code = data.get('code', '')
        language = data.get('language', 'python')
        instructions = data.get('instructions', 'Corrige errores y optimiza el código')
        model = data.get('model', 'openai')

        if not code:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó código para procesar'
            }), 400

        result = None

        # Procesar con el modelo seleccionado
        if model == 'openai' and app.config['API_KEYS'].get('openai'):
            try:
                client = openai.OpenAI(api_key=app.config['API_KEYS'].get('openai'))
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un experto programador especializado en corregir código."},
                        {"role": "user", "content": f"""Corrige el siguiente código en {language} según las instrucciones proporcionadas.

                CÓDIGO:
                ```{language}
                {code}
                ```

                INSTRUCCIONES:
                {instructions}

                Responde en formato JSON con las siguientes claves:
                - correctedCode: el código corregido completo
                - changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'
                - explanation: una explicación detallada de los cambios
                """}
                    ],
                    temperature=0.1
                )

                response_text = response.choices[0].message.content.strip()
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    # Intenta extraer JSON de la respuesta si está envuelto en bloques de código
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1).strip())
                        except json.JSONDecodeError:
                            logging.error(f"Error al decodificar JSON extraído de OpenAI: {json_match.group(1)[:500]}")
                            result = {
                                "correctedCode": code,
                                "changes": [{"description": "No se pudieron procesar los cambios correctamente", "lineNumbers": [1]}],
                                "explanation": "Error al procesar la respuesta de OpenAI."
                            }
                    else:
                        logging.error(f"No se encontró formato JSON en la respuesta de OpenAI: {response_text[:500]}")
                        result = {
                            "correctedCode": code,
                            "changes": [{"description": "No se encontró formato JSON en la respuesta", "lineNumbers": [1]}],
                            "explanation": "OpenAI no respondió en el formato esperado. Intente de nuevo o use otro modelo."
                        }

                logging.info("Código corregido con OpenAI")

            except Exception as e:
                logging.error(f"Error con API de OpenAI: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con OpenAI: {str(e)}'
                }), 500

        elif model == 'anthropic' and app.config['API_KEYS'].get('anthropic'):
            try:
                import anthropic
                from anthropic import Anthropic

                client = Anthropic(api_key=app.config['API_KEYS'].get('anthropic'))

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    messages=[
                        {"role": "system", "content": "Eres un experto programador especializado en corregir código."},
                        {"role": "user", "content": f"""Corrige el siguiente código en {language} según las instrucciones proporcionadas.

                CÓDIGO:
                ```{language}
                {code}
                ```

                INSTRUCCIONES:
                {instructions}

                Responde en formato JSON con las siguientes claves:
                - correctedCode: el código corregido completo
                - changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'
                - explanation: una explicación detallada de los cambios
                """}
                    ],
                    temperature=0.1
                )

                response_text = response.content[0].text.strip()
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    # Intenta extraer JSON de la respuesta si está envuelto en bloques de código
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1).strip())
                        except json.JSONDecodeError:
                            logging.error(f"Error al decodificar JSON extraído de Anthropic: {json_match.group(1)[:500]}")
                            result = {
                                "correctedCode": code,
                                "changes": [{"description": "No se pudieron procesar los cambios correctamente", "lineNumbers": [1]}],
                                "explanation": "Error al procesar la respuesta de Claude."
                            }
                    else:
                        logging.error(f"No se encontró formato JSON en la respuesta de Anthropic: {response_text[:500]}")
                        result = {
                            "correctedCode": code,
                            "changes": [{"description": "No se encontró formato JSON en la respuesta", "lineNumbers": [1]}],
                            "explanation": "Claude no respondió en el formato esperado. Intente de nuevo o use otro modelo."
                        }

                logging.info("Código corregido con Anthropic")

            except Exception as e:
                logging.error(f"Error con API de Anthropic: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con Anthropic: {str(e)}'
                }), 500

        elif model == 'gemini' and app.config['API_KEYS'].get('gemini'):
            try:
                # Asegúrate de que Gemini está configurado correctamente
                genai.configure(api_key=app.config['API_KEYS'].get('gemini'))

                gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config={
                        'temperature': 0.2,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 4096,
                    }
                )

                prompt = f"""Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas.

                CÓDIGO:
                ```{language}
                {code}
                ```

                INSTRUCCIONES:
                {instructions}

                Responde en formato JSON con las siguientes claves:
                - correctedCode: el código corregido completo
                - changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'
                - explanation: una explicación detallada de los cambios
                """

                response = gemini_model.generate_content(prompt)
                response_text = response.text

                # Intentar extraer JSON de la respuesta
                try:
                    # Primero intenta encontrar un bloque JSON
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(1).strip())
                    else:
                        # Si no hay bloque JSON, busca cualquier objeto JSON en la respuesta
                        json_match = re.search(r'({.*})', response_text, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group(0))
                        else:
                            logging.error(f"No se encontró formato JSON en la respuesta de Gemini: {response_text[:500]}")
                            result = {
                                "correctedCode": code,
                                "changes": [],
                                "explanation": "No se pudo procesar correctamente la respuesta del modelo."
                            }
                except json.JSONDecodeError as json_err:
                    logging.error(f"Error al decodificar JSON de Gemini: {str(json_err)}")
                    result = {
                        "correctedCode": code,
                        "changes": [],
                        "explanation": f"Error al procesar la respuesta JSON: {str(json_err)}"
                    }

                logging.info("Código corregido con Gemini")

            except Exception as e:
                logging.error(f"Error con API de Gemini: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con Gemini: {str(e)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Modelo {model} no soportado o API no configurada'
            }), 400

        # Verificar que el resultado tenga la estructura esperada
        if not result:
            return jsonify({
                'success': False,
                'error': 'No se pudo obtener una respuesta válida del modelo'
            }), 500

        if 'correctedCode' not in result:
            result['correctedCode'] = code
            result['changes'] = [{"description": "No se pudo procesar la corrección", "lineNumbers": [1]}]
            result['explanation'] = "El modelo no devolvió código corregido en el formato esperado."
            logging.warning(f"Respuesta sin código corregido: {str(result)[:200]}")

        return jsonify({
            'success': True,
            'corrected_code': result.get('correctedCode', ''),
            'changes': result.get('changes', []),
            'explanation': result.get('explanation', 'No se proporcionó explicación.')
        })

    except Exception as e:
        logging.error(f"Error al procesar la solicitud de código: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Error al procesar la solicitud: {str(e)}'
        }), 500


@app.route('/api/developer_assistant', methods=['POST'])
def developer_assistant():
    """API para procesar consultas específicas de desarrollo."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        query = data.get('query', '')
        context = data.get('context', [])
        model = data.get('model', 'openai')  # Modelo predeterminado

        if not query:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó una consulta'
            }), 400

        # Process using available API
        if model == 'openai' and app.config['API_KEYS'].get('openai'):
            try:
                client = openai.OpenAI(api_key=app.config['API_KEYS'].get('openai'))
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a development assistant expert helping with programming tasks."},
                        {"role": "user", "content": f"Context: {context}\n\nQuery: {query}"}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                response = completion.choices[0].message.content

                return jsonify({
                    'success': True,
                    'response': response,
                    'model_used': 'openai'
                })
            except Exception as e:
                logging.error(f"Error with OpenAI API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error with OpenAI API: {str(e)}'
                }), 500
        elif model == 'anthropic' and app.config['API_KEYS'].get('anthropic'):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=app.config['API_KEYS'].get('anthropic'))
                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=2000,
                    temperature=0.7,
                    system="You are a development assistant expert helping with programming tasks.",
                    messages=[{"role": "user", "content": f"Context: {context}\n\nQuery: {query}"}]
                )
                response = completion.content[0].text

                return jsonify({
                    'success': True,
                    'response': response,
                    'model_used': 'anthropic'
                })
            except Exception as e:
                logging.error(f"Error with Anthropic API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error with Anthropic API: {str(e)}'
                }), 500
        elif model == 'gemini' and app.config['API_KEYS'].get('gemini'):
            try:
                # Make sure Gemini is configured properly
                genai.configure(api_key=app.config['API_KEYS'].get('gemini'))

                gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                gemini_response = gemini_model.generate_content(f"Context: {context}\n\nQuery: {query}")
                response = gemini_response.text

                return jsonify({
                    'success': True,
                    'response': response,
                    'model_used': 'gemini'
                })
            except Exception as e:
                logging.error(f"Error with Gemini API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error with Gemini API: {str(e)}'
                }), 500
        else:
            # Default response if no API is available
            available_models = []
            if app.config['API_KEYS'].get('openai'):
                available_models.append('openai')
            if app.config['API_KEYS'].get('anthropic'):
                available_models.append('anthropic')
            if app.config['API_KEYS'].get('gemini'):
                available_models.append('gemini')

            if available_models:
                message = f"The model '{model}' is not available. Available models: {', '.join(available_models)}"
            else:
                message = "No AI models available. Please configure an API key in the Secrets panel."

            return jsonify({
                'success': False,
                'message': message,
                'available_models': available_models
            })

    except Exception as e:
        logging.error(f"Error in developer assistant: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Error processing request: {str(e)}'
        }), 500


@app.route('/api/process_natural', methods=['POST'])
def process_natural_command():
    """Process natural language input and return corresponding command."""
    try:
        data = request.json
        # Support both 'text' and 'instruction' for backward compatibility
        text = data.get('text', '') or data.get('instruction', '')
        model_choice = data.get('model', 'openai')
        user_id = data.get('user_id', 'default')

        if not text:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó texto'
            }), 400

        command = process_natural_language_to_command(text)

        if not command:
            return jsonify({
                'success': False,
                'error': 'No se pudo generar un comando para esa instrucción'
            }), 400

        # Execute command
        file_modifying_commands = ['mkdir', 'touch', 'rm', 'cp', 'mv', 'ls']
        is_file_command = any(cmd in command.split() for cmd in file_modifying_commands)

        try:
            workspace_dir = get_user_workspace(user_id)
            current_dir = os.getcwd()
            os.chdir(workspace_dir)

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            os.chdir(current_dir)

            command_output = result.stdout if result.returncode == 0 else result.stderr
            command_success = result.returncode == 0

        except Exception as cmd_error:
            logging.error(f"Error al ejecutar comando: {str(cmd_error)}")
            command_output = f"Error: {str(cmd_error)}"
            command_success = False

        # Notify websocket clients if file command
        if is_file_command:
            change_type = 'unknown'
            file_path = ''

            if 'mkdir' in command:
                change_type = 'create'
                file_path = command.split('mkdir ')[1].strip().replace('-p', '').strip()
            elif 'touch' in command:
                change_type = 'create'
                file_path = command.split('touch ')[1].strip()
            elif 'rm' in command:
                change_type = 'delete'
                parts = command.split('rm ')
                if len(parts) > 1:
                    file_path = parts[1].replace('-rf', '').strip()

            try:
                socketio.emit('file_change', {
                    'type': change_type,
                    'file': {'path': file_path},
                    'timestamp': time.time()
                }, room=user_id)

                socketio.emit('file_sync', {
                    'refresh': True,
                    'timestamp': time.time()
                }, room=user_id)

                socketio.emit('file_command', {
                    'command': command,
                    'type': change_type,
                    'file': file_path,
                    'timestamp': time.time()
                }, room=user_id)

                socketio.emit('command_executed', {
                    'command': command,
                    'output': command_output,
                    'success': command_success,
                    'timestamp': time.time()
                }, room=user_id)

                logging.info(f"Notificaciones de cambio enviadas: {change_type} - {file_path}")
            except Exception as ws_error:
                logging.error(f"Error al enviar notificación WebSocket: {str(ws_error)}")

        # Return the response in a consistent format
        return jsonify({
            'success': True,
            'command': command,
            'refresh_explorer': is_file_command,
            'output': command_output,
            'success': command_success
        })

    except Exception as e:
        logging.error(f"Error processing natural language: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Error al procesar instrucción: {str(e)}"
        }), 500


@app.route('/api/process_instructions', methods=['POST'])
def process_instructions():
    """Process natural language instructions and convert to terminal commands."""
    try:
        data = request.json
        instruction = data.get('message', '') or data.get('instruction', '')
        model_choice = data.get('model', 'openai')

        if not instruction:
            return jsonify({'error': 'No instruction provided'}), 400

        command_only = data.get('command_only', False)

        command_map = {
            "listar": "ls -la",
            "mostrar archivos": "ls -la",
            "mostrar directorio": "ls -la",
            "ver archivos": "ls -la",
            "archivos": "ls -la",
            "dir": "ls -la",
            "fecha": "date",
            "hora": "date +%H:%M:%S",
            "calendario": "cal",
            "quien soy": "whoami",
            "donde estoy": "pwd",
            "limpiar": "clear",
            "sistema": "uname -a",
            "memoria": "free -h",
            "espacio": "df -h",
            "procesos": "ps aux"
        }

        instruction_lower = instruction.lower()
        terminal_command = None
        missing_info = None

        for key, cmd in command_map.items():
            if key in instruction_lower:
                terminal_command = cmd
                break

        if not terminal_command:
            if "crear" in instruction_lower and "carpeta" in instruction_lower:
                folder_name = instruction_lower.split("carpeta")[-1].strip()
                if not folder_name:
                    missing_info = "Falta especificar el nombre de la carpeta"
                else:
                    terminal_command = f"mkdir -p {folder_name}"

            elif "crear" in instruction_lower and "archivo" in instruction_lower:
                file_name = instruction_lower.split("archivo")[-1].strip()
                if not file_name:
                    missing_info = "Falta especificar el nombre del archivo"
                else:
                    terminal_command = f"touch {file_name}"

            elif "eliminar" in instruction_lower or "borrar" in instruction_lower:
                target = instruction_lower.replace("eliminar", "").replace("borrar", "").strip()
                if not target:
                    missing_info = "Falta especificar qué elemento eliminar"
                else:
                    terminal_command = f"rm -rf {target}"

            else:
                terminal_command = "echo 'Comando no reconocido'"

        if terminal_command:
            logging.info(f"Instrucción: '{instruction}' → Comando: '{terminal_command}'")

        if missing_info:
            return jsonify({
                'error': missing_info,
                'needs_more_info': True
            })
        elif command_only:
            return jsonify({'command': terminal_command})
        else:
            return jsonify({
                'command': terminal_command,
                'original_instruction': instruction,
                'model_used': model_choice
            })

    except Exception as e:
        logging.error(f"Error generating command: {str(e)}")
        return jsonify({'error': f"Error generating command: {str(e)}"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for the application."""
    try:
        # Obtener el estado actual de las APIs desde la configuración
        api_keys = app.config.get('API_KEYS', {}) if hasattr(app, 'config') else {}

        apis = {
            "openai": "ok" if api_keys.get('openai') else "not configured",
            "anthropic": "ok" if api_keys.get('anthropic') else "not configured",
            "gemini": "ok" if api_keys.get('gemini') else "not configured"
        }

        # Verificar si hay al menos una API configurada
        any_api_available = any([key for key, value in api_keys.items() if value])

        # Registrar cada solicitud de verificación de salud
        logging.info(f"Verificación de salud solicitada en: {time.time()}")

        # Comprobar si sys está importado
        import sys

        response = {
            "status": "ok",
            "timestamp": time.time(),
            "version": "1.0.0",
            "apis": apis,
            "chat_api_available": any_api_available,
            "available_models": [key for key, value in api_keys.items() if value],
            "debug_info": {
                "python_version": sys.version,
                "endpoints_active": [
                    "/api/chat",
                    "/api/health",
                    "/api/files",
                    "/api/process_code"
                ]
            }
        }

        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500


@app.route('/api/files', methods=['GET'])
def list_files_api():
    """API para listar archivos del workspace del usuario."""
    try:
        directory = request.args.get('directory', '.')
        user_id = request.args.get('user_id', 'default')

        user_workspace = get_user_workspace(user_id)

        if directory == '.':
            full_directory = user_workspace
            relative_dir = '.'
        else:
            directory = directory.replace('..', '').strip('/')
            full_directory = os.path.join(user_workspace, directory)
            relative_dir = directory

        if not os.path.exists(full_directory):
            if directory == '.':
                os.makedirs(full_directory, exist_ok=True)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Directorio no encontrado'
                }), 404

        files = []
        try:
            for item in os.listdir(full_directory):
                item_path = os.path.join(full_directory, item)
                relative_path = os.path.join(relative_dir, item) if relative_dir != '.' else item

                extension = os.path.splitext(item)[1].lower()[1:] if os.path.isfile(item_path) and '.' in item else ''

                if os.path.isdir(item_path):
                    files.append({
                        'name': item,
                        'path': relative_path,
                        'type': 'directory',
                        'size': 0,
                        'modified': os.path.getmtime(item_path),
                        'extension': ''
                    })
                else:
                    file_size = os.path.getsize(item_path)
                    files.append({
                        'name': item,
                        'path': relative_path,
                        'type': 'file',
                        'size': file_size,
                        'modified': os.path.getmtime(item_path),
                        'extension': extension
                    })
        except Exception as e:
            logging.error(f"Error al listar archivos: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al listar archivos: {str(e)}'
            }), 500

        return jsonify({
            'success': True,
            'files': files,
            'directory': relative_dir
        })
    except Exception as e:
        logging.error(f"Error en endpoint de archivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/read', methods=['GET'])
def read_file():
    """API para leer el contenido de un archivo en el workspace del usuario."""
    try:
        file_path = request.args.get('file_path')
        user_id = request.args.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_workspace = get_user_workspace(user_id)

        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        if os.path.isdir(full_path):
            return jsonify({
                'success': False,
                'error': 'La ruta especificada es un directorio'
            }), 400

        try:
            binary_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'zip', 'pdf', 'doc', 'docx', 'xls', 'xlsx']
            file_ext = os.path.splitext(file_path)[1].lower()[1:] if '.' in file_path else ''

            if file_ext in binary_extensions:
                return jsonify({
                    'success': True,
                    'is_binary': True,
                    'file_path': file_path,
                    'file_url': f'/api/files/download?file_path={file_path}&user_id={user_id}'
                })

            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return jsonify({
                'success': True,
                'content': content,
                'file_path': file_path,
                'is_binary': False
            })
        except Exception as e:
            logging.error(f"Error al leer archivo: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al leer archivo: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error en endpoint de lectura de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/files/create', methods=['POST'])
def create_file():
    """API para crear un archivo o directorio en el workspace del usuario."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        file_path = data.get('file_path')
        content = data.get('content', '')
        is_directory = data.get('is_directory', False)
        user_id = data.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_workspace = get_user_workspace(user_id)

        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        if os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': f'Ya existe un{"a carpeta" if is_directory else " archivo"} con ese nombre'
            }), 400

        try:
            if is_directory:
                os.makedirs(full_path, exist_ok=True)
                message = f'Directorio {file_path} creado exitosamente'
            else:
                parent_dir = os.path.dirname(full_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                message = f'Archivo {file_path} creado exitosamente'

            return jsonify({
                'success': True,
                'message': message,
                'file_path': file_path,
                'is_directory': is_directory
            })
        except Exception as e:
            logging.error(f"Error al crear archivo/directorio: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al crear: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error en endpoint de creación: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/delete', methods=['DELETE'])
def delete_file():
    """API para eliminar un archivo o directorio del workspace del usuario."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        file_path = data.get('file_path')
        user_id = data.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_workspace = get_user_workspace(user_id)

        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo o directorio no encontrado'
            }), 404

        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                message = f'Directorio {file_path} eliminado exitosamente'
            else:
                os.remove(full_path)
                message = f'Archivo {file_path} eliminado exitosamente'

            return jsonify({
                'success': True,
                'message': message,
                'file_path': file_path,
                'is_directory': os.path.isdir(full_path)
            })
        except Exception as e:
            logging.error(f"Error al eliminar: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al eliminar: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error en endpoint de eliminación: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/files/download', methods=['GET'])
def download_file():
    """API para descargar un archivo desde el workspace del usuario."""
    try:
        file_path = request.args.get('file_path')
        user_id = request.args.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_workspace = get_user_workspace(user_id)

        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        return send_file(full_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        logging.error(f"Error al descargar archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error al descargar archivo: {str(e)}'
        }), 500


@app.route('/api/constructor/generate', methods=['POST'])
def generate_project():
    """API endpoint para iniciar la generación de un proyecto."""
    try:
        data = request.json
        description = data.get('description', '')

        if not description:
            return jsonify({
                'success': False,
                'error': 'Se requiere una descripción del proyecto'
            }), 400

        return jsonify({
            'success': True,
            'message': 'Generación de proyecto iniciada',
            'project_id': f"proj_{int(time.time())}",
            'estimated_time': '5-10 minutos'
        })

    except Exception as e:
        logging.error(f"Error al generar proyecto: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api_status')
def api_status_old():
    """Muestra el estado de las claves API configuradas."""
    openai_key = app.config['API_KEYS'].get('openai', 'No configurada')
    anthropic_key = app.config['API_KEYS'].get('anthropic', 'No configurada')
    gemini_key = app.config['API_KEYS'].get('gemini', 'No configurada')

    if openai_key != 'No configurada':
        openai_key = openai_key[:5] + "..." + openai_key[-5:] if len(openai_key) > 10 else "***configurada***"

    if anthropic_key != 'No configurada':
        anthropic_key = anthropic_key[:5] + "..." + anthropic_key[-5:] if len(anthropic_key) > 10 else "***configurada***"

    if gemini_key != 'No configurada':
        gemini_key = gemini_key[:5] + "..." + gemini_key[-5:] if len(gemini_key) > 10 else "***configurada***"

    return jsonify({
        'openai': openai_key,
        'anthropic': anthropic_key,
        'gemini': gemini_key,
        'message': 'Visita esta URL para verificar el estado de las APIs'
    })


@app.route('/api/status', methods=['GET'])
def api_status():
    """Endpoint para verificar el estado de la API."""
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'message': 'API funciona correctamente',
            'timestamp': time.time()
        })
    except Exception as e:
        logging.error(f"Error en verificación de estado: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': str(e)
        }), 500


@socketio.on('connect')
def handle_connect():
    """Manejar conexión de cliente Socket.IO."""
    logging.info(f"Cliente Socket.IO conectado: {request.sid}")
    emit('server_info', {'status': 'connected', 'sid': request.sid})


@socketio.on('execute_command')
def handle_execute_command(data):
    """Ejecuta un comando en la terminal y devuelve el resultado."""
    command = data.get('command', '')
    user_id = data.get('user_id', 'default')
    terminal_id = data.get('terminal_id', request.sid)

    if not command:
        emit('command_error', {
            'error': 'No se proporcionó un comando',
            'terminal_id': terminal_id
        }, room=terminal_id)
        return

    file_system_manager = FileSystemManager(socketio)
    result = file_system_manager.execute_command(
        command=command,
        user_id=user_id,
        notify=True,
        terminal_id=terminal_id
    )

    emit('command_result', {
        'output': result.get('output', ''),
        'success': result.get('success', False),
        'command': command,
        'terminal_id': terminal_id
    }, room=terminal_id)

    socketio.emit('file_sync', {
        'refresh': True,
        'user_id': user_id,
        'command': command
    }, room=user_id)


@socketio.on('user_message')
def handle_user_message(data):
    """Manejar mensajes del usuario a través de Socket.IO."""
    try:
        logging.info(f"Mensaje recibido vía Socket.IO: {data}")
        user_message = data.get('message', '')
        agent_id = data.get('agent', 'developer')
        model = data.get('model', 'openai')
        document = data.get('document', '')
        terminal_id = data.get('terminal_id', '')

        if not user_message:
            emit('error', {'message': 'Mensaje vacío'})
            return

        logging.info(f"Procesando mensaje Socket.IO: '{user_message[:30]}...' usando agente {agent_id} y modelo {model}")

        request_data = {
            'message': user_message,
            'agent_id': agent_id,
            'model': model,
            'context': data.get('context', [])
        }

        try:
            if model == 'openai' and app.config['API_KEYS'].get('openai'):
                messages = [
                    {"role": "system", "content": f"Eres un asistente de {agent_id} experto y útil."},
                    {"role": "user", "content": user_message}
                ]

                client = openai.OpenAI(api_key=app.config['API_KEYS'].get('openai'))
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )

                response = completion.choices[0].message.content
                logging.info(f"Respuesta generada directamente con OpenAI: {response[:100]}...")

                emit('agent_response', {
                    'response': response,
                    'agent': agent_id,
                    'model': model,
                    'error': None
                })
                return
        except Exception as api_error:
            logging.warning(f"Error en API directa: {str(api_error)}, usando handle_chat_internal")

        # Si falla la API directa o no está configurada, usar handle_chat_internal
        result = handle_chat_internal(request_data)

        logging.info(f"Enviando respuesta Socket.IO: '{result.get('response', '')[:30]}...'")
        emit('agent_response', {
            'response': result.get('response', ''),
            'agent': agent_id,
            'model': model,
            'error': result.get('error', None),
            'terminal_id': terminal_id
        })

    except Exception as e:
        logging.error(f"Error en Socket.IO user_message: {str(e)}")
        logging.error(traceback.format_exc())
        emit('error', {'message': str(e)})


if __name__ == '__main__':
    try:
        logging.info("Iniciando servidor CODESTORM Assistant...")

        if not app.config['API_KEYS'].get('openai'):
            logging.warning("OPENAI_API_KEY no configurada - funcionalidades de OpenAI estarán deshabilitadas")
        if not app.config['API_KEYS'].get('anthropic'):
            logging.warning("ANTHROPIC_API_KEY no configurada - funcionalidades de Anthropic estarán deshabilitadas")
        if not app.config['API_KEYS'].get('gemini'):
            logging.warning("GEMINI_API_KEY no configurada - funcionalidades de Gemini estarán deshabilitadas")

        if not any([app.config['API_KEYS'].get(k) for k in ['openai', 'anthropic', 'gemini']]):
            logging.error("¡ADVERTENCIA! Ninguna API está configurada. El sistema funcionará en modo degradado.")

        try:
            if 'watch_workspace_files' in globals():
                file_watcher_thread = threading.Thread(target=watch_workspace_files, daemon=True)
                file_watcher_thread.start()
                logging.info("Observador de archivos iniciado correctamente")
        except Exception as watcher_error:
            logging.warning(f"No se pudo iniciar el observador de archivos: {str(watcher_error)}")

        logging.info("Servidor listo para recibir conexiones en puerto 5000")

        try:
            init_xterm_blueprint(app, socketio)
            app.register_blueprint(xterm_bp, url_prefix='/xterm')
            logging.info("xterm blueprint registered successfully")
        except Exception as e:
            logging.error(f"Error registering xterm blueprint: {str(e)}")

        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logging.critical(f"Error fatal al iniciar el servidor: {str(e)}")
        logging.critical(traceback.format_exc())

