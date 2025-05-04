from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import uuid
import datetime
from dotenv import load_dotenv
import threading
import time
import random
from datetime import datetime
from flask_cors import CORS
from flask_socketio import SocketIO, emit
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

# Configurar logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

# Inicializar app Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
CORS(app)
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

# Configurar claves API de forma segura (usando variables de entorno en producción)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

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
if not any([openai_valid, anthropic_valid, gemini_valid]):
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
            if app.config['API_KEYS']['openai']:
                try:
                    messages = [{"role": "system", "content": system_prompt}]
                    for msg in formatted_context:
                        messages.append({"role": msg['role'], "content": msg['content']})
                    messages.append({"role": "user", "content": user_message})

                    openai_model = "gpt-4o"

                    openai_client = openai.OpenAI(api_key=app.config['API_KEYS']['openai'])
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
            if app.config['API_KEYS']['anthropic']:
                try:
                    import anthropic
                    from anthropic import Anthropic

                    client = Anthropic(api_key=app.config['API_KEYS']['anthropic'])

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
            if app.config['API_KEYS']['gemini']:
                try:
                    # Make sure Gemini is configured properly
                    if not hasattr(genai, '_configured') or not genai._configured:
                        genai.configure(api_key=app.config['API_KEYS']['gemini'])

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
            if app.config['API_KEYS']['openai']:
                available_models.append("'openai'")
            if app.config['API_KEYS']['anthropic']:
                available_models.append("'anthropic'")
            if app.config['API_KEYS']['gemini']:
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

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint para manejar solicitudes de chat."""
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            logging.warning("No se recibieron datos JSON válidos")
            return jsonify({
                'error': 'Invalid JSON data',
                'response': 'Error: Los datos enviados no son JSON válido'
            }), 400

        logging.debug(f"Datos recibidos en /api/chat: {json.dumps(data)}")

        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'general')
        model_choice = data.get('model', 'openai')

        if not user_message:
            logging.warning("Solicitud sin mensaje")
            return jsonify({'error': 'No message provided', 'response': 'Error: No se proporcionó un mensaje.'}), 400

        logging.info(f"Mensaje procesado: {user_message} por agente {agent_id} usando {model_choice}")

        # Registro adicional para verificar que la solicitud está llegando correctamente
        print(f"Solicitud de chat recibida: Mensaje='{user_message}', Agente={agent_id}, Modelo={model_choice}")

        # Verificar qué APIs están disponibles
        available_apis = []
        if app.config['API_KEYS']['openai']:
            available_apis.append('openai')
        if app.config['API_KEYS']['anthropic']:
            available_apis.append('anthropic')
        if app.config['API_KEYS']['gemini']:
            available_apis.append('gemini')

        # Si no hay APIs configuradas, mostrar mensaje informativo
        if not available_apis:
            return jsonify({
                'success': False,
                'response': "No hay APIs configuradas. Por favor configure al menos una API key (OpenAI, Anthropic o Gemini) en el panel de Secrets.",
                'agent_id': agent_id,
                'model': model_choice,
                'available_models': []
            })

        # Si el modelo elegido no está disponible, usar el primero disponible
        if model_choice not in available_apis:
            fallback_model = available_apis[0] if available_apis else None
            if fallback_model:
                logging.warning(f"Modelo {model_choice} no disponible, usando {fallback_model}")
                model_choice = fallback_model
            else:
                return jsonify({
                    'success': False,
                    'error': f"El modelo '{model_choice}' no está configurado. Por favor configure una API key válida o seleccione otro modelo.",
                    'agent_id': agent_id,
                    'model': model_choice,
                    'available_models': available_apis
                })

        result = handle_chat_internal(data)

        if 'error' in result and result['error']:
            return jsonify({
                'success': False,
                'error': result['error'],
                'agent_id': agent_id,
                'model': model_choice,
                'available_models': available_apis
            })

        return jsonify({
            'success': True,
            'response': result['response'],
            'agent_id': agent_id,
            'model': model_choice,
            'available_models': available_apis,
            'is_demo': False
        })
    except Exception as e:
        logging.error(f"Error en API de chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/files')
def files():
    """Render the files explorer page."""
    return render_template('files.html')

@app.route('/code_corrector')
def code_corrector():
    """Ruta al corrector de código."""
    return render_template('code_corrector.html')

@app.route('/constructor')
def constructor():
    """Ruta al constructor de aplicaciones."""
    return render_template('constructor.html')

@app.route('/agente')
def agente():
    """Ruta a la página del agente."""
    return render_template('agente.html')

@app.route('/agent')
def agent_en():
    """Ruta alternativa para la página del agente."""
    return redirect('/agente')

@app.route('/preview')
def preview():
    """Render the preview page."""
    return render_template('preview.html')

@app.route('/terminal')
def terminal():
    """Render the Monaco terminal page."""
    os.makedirs('user_workspaces/default', exist_ok=True)
    readme_path = os.path.join('user_workspaces/default', 'README.md')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write('# Workspace\n\nEste es tu espacio de trabajo. Usa comandos o instrucciones en lenguaje natural para crear y modificar archivos.\n\nEjemplos:\n- "crea una carpeta llamada proyectos"\n- "mkdir proyectos"\n- "touch archivo.txt"')

    return render_template('monaco_terminal.html')

@app.route('/xterm_terminal')
def xterm_terminal_route():
    """Render the XTerm terminal page directly."""
    return render_template('xterm_terminal.html')

@app.route('/xterm/xterm_terminal')
def xterm_terminal_alt():
    """Ruta alternativa para acceder a la terminal XTerm."""
    return render_template('xterm_terminal.html')

@app.route('/monaco_terminal')
def monaco_terminal():
    """Redirect to terminal."""
    return redirect('/terminal')

@app.route('/api/process_code', methods=['POST'])
def process_code_endpoint():
    """Process code for corrections and improvements."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos JSON válidos'}), 400

        code = data.get('code', '')
        instructions = data.get('instructions', 'Corrige errores y mejora la calidad del código')
        language = data.get('language', 'python')
        model = data.get('model', 'openai')

        if not code:
            return jsonify({'success': False, 'error': 'No se proporcionó código para procesar'}), 400

        result = None

        if model == 'openai' and app.config['API_KEYS']['openai']:
            try:
                openai_client = openai.OpenAI(api_key=app.config['API_KEYS']['openai'])

                prompt = f"""Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas.

                CÓDIGO:
                ```{language}
                {code}
                ```

                INSTRUCCIONES:
                {instructions}

                Responde en formato JSON con las siguientes claves:
                -
- correctedCode: el código corregido completo
- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'
- explanation: una explicación detallada de los cambios
"""

                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un experto programador que corrige y optimiza código."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )

                result = json.loads(response.choices[0].message.content)
                logging.info("Código corregido con OpenAI")

            except Exception as e:
                logging.error(f"Error con API de OpenAI: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con OpenAI: {str(e)}'
                }), 500

        elif model == 'anthropic' and app.config['API_KEYS']['anthropic']:
            try:
                import anthropic
                from anthropic import Anthropic

                client = Anthropic(api_key=app.config['API_KEYS']['anthropic'])

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": f"""Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas.

CÓDIGO:
```{language}
{code}
```

INSTRUCCIONES:
{instructions}

Responde en formato JSON con las siguientes claves:
- correctedCode: el código corregido completo
- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'
- explanation: una explicación detallada de los cambios"""}
                    ]
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

        elif model == 'gemini' and app.config['API_KEYS']['gemini']:
            try:
                # Asegúrate de que Gemini está configurado correctamente
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=app.config['API_KEYS']['gemini'])

                gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config={
                        'temperature': 0.2,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 4096,
                    }
                )

                prompt = f"""Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas{language}
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
                }, broadcast=True)

                socketio.emit('file_sync', {
                    'refresh': True,
                    'timestamp': time.time()
                }, broadcast=True)

                socketio.emit('file_command', {
                    'command': command,
                    'type': change_type,
                    'file': file_path,
                    'timestamp': time.time()
                }, broadcast=True)

                socketio.emit('command_executed', {
                    'command': command,
                    'output': command_output,
                    'success': command_success,
                    'timestamp': time.time()
                }, broadcast=True)

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
    """Procesa instrucciones en lenguaje natural utilizando el modelo especificado"""
    data = request.json
    if not data:
        return jsonify({"error": "Datos no proporcionados"}), 400

    instruction = data.get('instruction') or data.get('message', '')
    model = data.get('model', 'openai')
    agent_id = data.get('agent_id', 'developer')
    format_type = data.get('format', 'default')

    if not instruction:
        return jsonify({"error": "Instrucción no proporcionada"}), 400

    try:
        # Enviar a la IA para procesamiento
        result = handle_chat_internal({
            'message': instruction,
            'model': model,
            'agent_id': agent_id
        })

        response = result.get('response', '')

        # Formatear respuesta según el tipo solicitado
        if format_type == 'markdown':
            # Asegurar que la respuesta tenga formato markdown correcto
            response = ensure_markdown_format(response)

        # Procesar para extraer comandos si así se solicita
        if data.get('command_only', False):
            command = extract_command_from_response(response)
            return jsonify({"response": response, "command": command})

        return jsonify({"response": response})

    except Exception as e:
        app.logger.error(f"Error al procesar la instrucción: {str(e)}")
        return jsonify({"error": str(e)}), 500

def ensure_markdown_format(response):
    """Asegura que la respuesta tenga un formato markdown correcto y bien estructurado"""
    # Verificar si hay bloques de código y asegurarse de que estén bien formateados
    lines = response.split('\n')
    in_code_block = False
    language_specified = False
    formatted_lines = []

    for i, line in enumerate(lines):
        # Detectar inicio de bloque de código
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        # Si es el inicio de un bloque y no tiene lenguaje especificado
        if in_code_block and line.strip() == '```':
            language_specified = False
            # Intentar detectar el lenguaje por contexto
            if i > 0 and 'javascript' in lines[i - 1].lower():
                formatted_lines.append('```javascript')
            elif i > 0 and 'python' in lines[i - 1].lower():
                formatted_lines.append('```python')
            elif i > 0 and ('bash' in lines[i - 1].lower() or 'shell' in lines[i - 1].lower() or 'comando' in lines[i - 1].lower()):
                formatted_lines.append('```bash')
            elif i > 0 and 'html' in lines[i - 1].lower():
                formatted_lines.append('```html')
            elif i > 0 and 'css' in lines[i - 1].lower():
                formatted_lines.append('```css')
            else:
                formatted_lines.append('```plaintext')
        else:
            formatted_lines.append(line)

    # Asegurarse de que todos los bloques de código estén cerrados
    if in_code_block:
        formatted_lines.append('```')

    return '\n'.join(formatted_lines)

def extract_command_from_response(response):
    """Extrae comandos de terminal de la respuesta de la IA"""
    # Buscar comandos en bloques de código bash/shell
    bash_block = re.search(r'```(?:bash|shell)\s*(.*?)\s*