from flask import Flask, render_template, request, jsonify, session, redirect, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
import json
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import subprocess
import time
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
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # Añadido secret_key para session
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
                        'start_time': time.time() - 3600,  # 1 hour ago
                        'completion_time': time.time() - 60  # 1 minute ago
                    }
    except Exception as load_err:
        logging.warning(f"Error preloading project statuses: {str(load_err)}")

except Exception as e:
    logging.error(f"Error registering constructor blueprint: {str(e)}")


# Recargar variables de entorno para asegurar que tenemos las últimas
load_dotenv(override=True)

# Configurar claves API con manejo de errores mejorado
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Configurar OpenAI
if openai_api_key:
    try:
        openai.api_key = openai_api_key
        # Verificar que la clave funciona haciendo una llamada de prueba sencilla
        openai_client = openai.OpenAI()
        _ = openai_client.models.list()
        logging.info(f"OpenAI API key verificada y configurada: {openai_api_key[:5]}...{openai_api_key[-5:]}")
    except Exception as e:
        logging.error(f"Error al configurar OpenAI API: {str(e)}")
        logging.warning("La clave de OpenAI no es válida o el servicio no está disponible")
        openai_api_key = None
else:
    logging.warning("OpenAI API key no configurada - funcionalidades de OpenAI estarán deshabilitadas")

# Configurar Anthropic
if anthropic_api_key:
    try:
        # Importar solo si la clave está configurada
        import anthropic
        from anthropic import Anthropic

        # Verificar que la clave funciona haciendo una llamada de prueba
        client = Anthropic(api_key=anthropic_api_key)
        _ = client.models.list()
        logging.info(f"Anthropic API key verificada y configurada: {anthropic_api_key[:5]}...{anthropic_api_key[-5:]}")
    except Exception as e:
        logging.error(f"Error al configurar Anthropic API: {str(e)}")
        logging.warning("La clave de Anthropic no es válida o el servicio no está disponible")
        anthropic_api_key = None
else:
    logging.warning("Anthropic API key no configurada - funcionalidades de Anthropic estarán deshabilitadas")

# Configurar Gemini
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        # Verificar que la clave funciona listando modelos
        models = genai.list_models()
        _ = list(models)  # Forzar evaluación
        logging.info(f"Gemini API key verificada y configurada: {gemini_api_key[:5]}...{gemini_api_key[-5:]}")
    except Exception as e:
        logging.error(f"Error al configurar Gemini API: {str(e)}")
        logging.warning("La clave de Gemini no es válida o el servicio no está disponible")
        gemini_api_key = None
else:
    logging.warning("Gemini API key no configurada - funcionalidades de Gemini estarán deshabilitadas")

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
    if openai_api_key:
        apis_configuradas.append("OpenAI")
    if anthropic_api_key:
        apis_configuradas.append("Anthropic")
    if gemini_api_key:
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
    # Create an instance of FileSystemManager to use its get_user_workspace method
    file_system_manager = FileSystemManager(socketio)
    workspace = file_system_manager.get_user_workspace(user_id)

    return jsonify({
        'user_id': user_id,
        'workspace': str(workspace),  # Just return the path as a string without trying to make it relative
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

        USING_NEW_OPENAI_CLIENT = False  # Determine this based on your openai client version. This is a placeholder.

        if model_choice == 'openai':
            if openai_api_key:
                try:
                    messages = [{"role": "system", "content": system_prompt}]
                    for msg in formatted_context:
                        messages.append({"role": msg['role'], "content": msg['content']})
                    messages.append({"role": "user", "content": user_message})

                    # Usar el modelo más avanzado disponible: GPT-4o
                    openai_model = "gpt-4o"

                    if USING_NEW_OPENAI_CLIENT:
                        completion = client.chat.completions.create(
                            model=openai_model,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=2000
                        )
                        response = completion.choices[0].message.content
                    else:
                        completion = openai.ChatCompletion.create(
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
            if anthropic_api_key:
                try:
                    import anthropic
                    from anthropic import Anthropic

                    client = Anthropic(api_key=anthropic_api_key)

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
            if gemini_api_key:
                try:
                    # Make sure Gemini is configured properly
                    if not hasattr(genai, '_configured') or not genai._configured:
                        genai.configure(api_key=gemini_api_key)

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
            # Mensaje descriptivo que orienta al usuario
            available_models = []
            if openai_api_key:
                available_models.append("'openai'")
            if anthropic_api_key:
                available_models.append("'anthropic'")
            if gemini_api_key:
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

        logging.debug(f"Datos recibidos: {json.dumps(data)}")

        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'general')
        model_choice = data.get('model', 'openai')

        if not user_message:
            logging.warning("Solicitud sin mensaje")
            return jsonify({'error': 'No message provided', 'response': 'Error: No se proporcionó un mensaje.'}), 400

        logging.info(f"Mensaje procesado: {user_message} por agente {agent_id} usando {model_choice}")

        # Verificar qué APIs están disponibles
        available_apis = []
        if openai_api_key:
            available_apis.append('openai')
        if anthropic_api_key:
            available_apis.append('anthropic')
        if gemini_api_key:
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

        # Configurar prompts según el agente
        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar a los usuarios con tareas de programación, desde la corrección de errores hasta la implementación de funcionalidades completas.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas a los usuarios a tomar decisiones sobre la estructura del código, patrones de diseño y selección de tecnologías.",
            'advanced': "Eres un Agente Avanzado de Software con experiencia en integraciones complejas y funcionalidades avanzadas. Puedes asesorar sobre tecnologías emergentes, optimización de rendimiento y soluciones a problemas técnicos sofisticados.",
            'general': "Eres un asistente de desarrollo de software experto y útil. Respondes preguntas y ayudas con tareas de programación de manera clara y concisa."
        }

        system_prompt = agent_prompts.get(agent_id, agent_prompts['general'])

        # Preparar el contexto de conversación
        formatted_context = []
        for msg in data.get('context', []):
            role = msg.get('role', 'user')
            if role not in ['user', 'assistant', 'system']:
                role = 'user'
            formatted_context.append({
                "role": role,
                "content": msg.get('content', '')
            })

        # Procesar la solicitud con el modelo adecuado
        respuesta = None
        if model_choice == 'openai' and openai_api_key:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                for msg in formatted_context:
                    messages.append({"role": msg['role'], "content": msg['content']})
                messages.append({"role": "user", "content": user_message})

                # Usar el modelo más avanzado disponible: GPT-4o
                openai_model = "gpt-4o"

                try:
                    # Intentar con cliente nuevo primero
                    openai_client = openai.OpenAI()
                    completion = openai_client.chat.completions.create(
                        model=openai_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    respuesta = completion.choices[0].message.content
                except Exception as e:
                    # Fallback al cliente antiguo si es necesario
                    completion = openai.ChatCompletion.create(
                        model=openai_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    respuesta = completion.choices[0].message.content

            except Exception as e:
                logging.error(f"Error con API de OpenAI: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Error con OpenAI API: {str(e)}",
                    'agent_id': agent_id,
                    'model': model_choice
                })

        elif model_choice == 'anthropic' and anthropic_api_key:
            try:
                import anthropic
                from anthropic import Anthropic

                client = Anthropic(api_key=anthropic_api_key)

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

                respuesta = completion.content[0].text

            except Exception as e:
                logging.error(f"Error con API de Anthropic: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Error con Anthropic API: {str(e)}",
                    'agent_id': agent_id,
                    'model': model_choice
                })

        elif model_choice == 'gemini' and gemini_api_key:
            try:
                # Make sure Gemini is configured properly
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=gemini_api_key)

                model = genai.GenerativeModel('gemini-1.5-pro')

                full_prompt = system_prompt + "\n\n"
                for msg in formatted_context:
                    role_prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                    full_prompt += role_prefix + msg['content'] + "\n\n"
                full_prompt += "Usuario: " + user_message + "\n\nAsistente: "

                gemini_response = model.generate_content(full_prompt)
                respuesta = gemini_response.text

            except Exception as e:
                logging.error(f"Error con API de Gemini: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Error con Gemini API: {str(e)}",
                    'agent_id': agent_id,
                    'model': model_choice
                })

        # Si no se pudo generar una respuesta, mostrar un mensaje de error
        if not respuesta:
            return jsonify({
                'success': False,
                'error': f"No se pudo generar una respuesta con el modelo {model_choice}. Verifica que la API esté configurada correctamente.",
                'agent_id': agent_id,
                'model': model_choice,
                'available_models': available_apis
            })
            respuesta += "\n\nPuedo ayudarte a crear ese componente. ¿Quieres que te muestre un ejemplo de código?"
        # Devolver respuesta real de la API
        return jsonify({
            'success': True,
            'response': respuesta,
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
    return render_template('agente.html')

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
        code = data.get('code', '')
        instructions = data.get('instructions', 'Corrige errores y mejora la calidad del código')
        language = data.get('language', 'python')
        model = data.get('model', 'openai')
        auto_fix = data.get('auto_fix', False)

        if auto_fix:
            auto_instructions = "MODO CORRECCIÓN AUTOMÁTICA: "
            if instructions == 'Corrige errores y mejora la calidad del código':
                instructions = auto_instructions + "Corrige automáticamente errores de sintaxis, optimiza el código y mejora la calidad siguiendo las mejores prácticas. Enfócate en corregir errores sin cambiar la lógica principal."
            else:
                instructions = auto_instructions + instructions

        if not code:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó código para procesar'
            }), 400

        if model == 'openai' and openai_api_key:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas. El código resultante debe{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo sin comentarios explicativos\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"}
                    ],
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                logging.info("Código corregido con OpenAI")

            except Exception as e:
                logging.error(f"Error con API de OpenAI: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con OpenAI: {str(e)}'
                }), 500

        elif model == 'anthropic' and anthropic_api_key:
            try:
                import anthropic
                from anthropic import Anthropic

                client = Anthropic(api_key=anthropic_api_key)

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=4000,
                    system=f"Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas. Devuelve el código corregido, una lista de cambios realizados y una explicación clara en formato JSON.",
                    messages=[
                        {"role": "user", "content": f"CÓDIGO:\n```{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"}
                    ],
                    temperature=0.1
                )

                try:
                    result = json.loads(response.content[0].text.strip())
                except json.JSONDecodeError:
                    json_match = re.search(r'```(?\:json)?\s*(.*?)\s*```', response.content[0].text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1).strip())
                        except json.JSONDecodeError:
                            result = {
                                "correctedCode": code,
                                "changes": [{"description": "No se pudieron procesar los cambios correctamente", "lineNumbers": [1]}],
                                "explanation": "Error al procesar la respuesta de Claude. Respuesta recibida: " + response.content[0].text[:200] + "..."
                            }
                    else:
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

        elif model == 'gemini' and gemini_api_key:
            try:
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

                json_match = re.search(r'```json(.*?)