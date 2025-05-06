# Añadir estas rutas a tu app principal o importarlas desde constructor_routes.py

@app.route('/api/constructor/start', methods=['POST'])
def start_constructor():
    data = request.json
    project_id = data.get('project_id')
    description = data.get('description')
    tech_data = data.get('tech_data')

    if not project_id or not description:
        return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400

    try:
        # Almacenar información del proyecto para seguimiento
        project_data = {
            'id': project_id,
            'description': description,
            'tech_data': tech_data,
            'agent_type': data.get('agent_type', 'developer'),
            'model_type': data.get('model_type', 'openai'),
            'progress': 0,
            'current_stage': 'Inicializando',
            'messages': [],
            'paused': False,
            'start_time': datetime.now().isoformat(),
            'settings': {
                'include_tests': data.get('include_tests', False),
                'include_docs': data.get('include_docs', False),
                'include_deployment': data.get('include_deployment', False),
                'include_ci_cd': data.get('include_ci_cd', False)
            }
        }

        # En un sistema real, almacenarías esto en una base de datos
        # Para este ejemplo, lo guardamos en la sesión
        session[f'project_{project_id}'] = project_data

        # Iniciar proceso de desarrollo en segundo plano
        threading.Thread(target=simulate_development_process, args=(project_id,)).start()

        return jsonify({
            'success': True,
            'message': 'Desarrollo iniciado correctamente',
            'project_id': project_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/constructor/progress/<project_id>', methods=['GET'])
def get_constructor_progress(project_id):
    try:
        # Obtener datos del proyecto desde la sesión
        project_key = f'project_{project_id}'
        if project_key not in session:
            return jsonify({'success': False, 'error': 'Proyecto no encontrado'}), 404

        project_data = session[project_key]

        # Extraer mensajes no leídos y marcarlos como leídos
        new_messages = project_data.get('new_messages', [])
        project_data['new_messages'] = []  # Limpiar mensajes nuevos
        session[project_key] = project_data  # Actualizar sesión

        return jsonify({
            'success': True,
            'progress': project_data['progress'],
            'current_stage': project_data['current_stage'],
            'messages': new_messages,
            'paused': project_data.get('paused', False)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/constructor/pause/<project_id>', methods=['POST'])
def pause_constructor(project_id):
    try:
        # Obtener datos del proyecto desde la sesión
        project_key = f'project_{project_id}'
        if project_key not in session:
            return jsonify({'success': False, 'error': 'Proyecto no encontrado'}), 404

        project_data = session[project_key]
        project_data['paused'] = True

        # Añadir mensaje sobre la pausa
        if 'new_messages' not in project_data:
            project_data['new_messages'] = []
        project_data['new_messages'].append('Proceso de desarrollo pausado por el usuario')

        session[project_key] = project_data

        return jsonify({
            'success': True,
            'message': 'Desarrollo pausado correctamente'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/constructor/resume/<project_id>', methods=['POST'])

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

        # Aquí procesaríamos la consulta con el modelo de IA seleccionado
        # Por ahora, devolveremos una respuesta simple simulada
        response = {
            'success': True,
            'response': f"Respuesta a: {query}\n\nConsulta procesada correctamente. Esta es una respuesta de prueba.",
            'model_used': model
        }

        return jsonify(response)

    except Exception as e:
        logging.error(f"Error en el asistente de desarrollo: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Error al procesar la solicitud: {str(e)}'
        }), 500

def resume_constructor(project_id):
    try:
        # Obtener datos del proyecto desde la sesión
        project_key = f'project_{project_id}'
        if project_key not in session:
            return jsonify({'success': False, 'error': 'Proyecto no encontrado'}), 404

        project_data = session[project_key]
        project_data['paused'] = False

        # Añadir mensaje sobre la reanudación
        if 'new_messages' not in project_data:
            project_data['new_messages'] = []
        project_data['new_messages'].append('Proceso de desarrollo reanudado con los cambios aplicados')

        session[project_key] = project_data

        return jsonify({
            'success': True,
            'message': 'Desarrollo reanudado correctamente'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Función para simular el proceso de desarrollo en segundo plano
def simulate_development_process(project_id):
    project_key = f'project_{project_id}'
    stages = [
        'Analizando requerimientos',
        'Diseñando arquitectura',
        'Configurando entorno',
        'Generando estructura de proyecto',
        'Implementando componentes base',
        'Desarrollando funcionalidades',
        'Integrando base de datos',
        'Implementando API',
        'Configurando interfaz de usuario',
        'Realizando pruebas',
        'Optimizando rendimiento',
        'Preparando documentación',
        'Finalizando proyecto'
    ]

    try:
        # Incrementar progreso gradualmente
        for i, stage in enumerate(stages):
            # Verificar si el proyecto existe y si está pausado
            if project_key not in session:
                return

            project_data = session[project_key]

            # Establecer etapa actual
            project_data['current_stage'] = stage

            # Calcular progreso basado en la etapa actual
            progress_per_stage = 100 / len(stages)
            base_progress = i * progress_per_stage

            # Para cada etapa, incrementar gradualmente
            for step in range(1, 11):  # 10 pasos por etapa
                # Verificar pausa
                if project_key not in session:
                    return

                project_data = session[project_key]
                if project_data.get('paused', False):
                    # Esperar mientras está pausado
                    while True:
                        time.sleep(1)
                        if project_key not in session:
                            return

                        project_data = session[project_key]
                        if not project_data.get('paused', False):
                            break

                # Calcular progreso actual
                current_progress = base_progress + (step * (progress_per_stage / 10))
                project_data['progress'] = min(round(current_progress, 1), 100)

                # Añadir mensaje detallado ocasionalmente (cada 3 pasos)
                if step % 3 == 0 or step == 10:
                    if 'new_messages' not in project_data:
                        project_data['new_messages'] = []

                    messages = [
                        f"Trabajando en: {stage}",
                        f"Completado paso {step}/10 de {stage}"
                    ]

                    # Añadir mensajes específicos según la etapa
                    if stage == 'Analizando requerimientos' and step == 9:
                        messages.append("Análisis completado: Se han identificado los componentes principales")
                    elif stage == 'Diseñando arquitectura' and step == 10:
                        messages.append("Arquitectura definida: Estructura MVC con capas de servicio")
                    elif stage == 'Configurando entorno' and step == 5:
                        messages.append("Dependencias instaladas correctamente")
                    elif stage == 'Desarrollando funcionalidades' and step == 8:
                        messages.append("Implementada autenticación y autorización")
                    elif stage == 'Integrando base de datos' and step == 7:
                        messages.append("Esquema de base de datos generado y validado")

                    project_data['new_messages'].extend(messages)

                # Actualizar sesión
                session[project_key] = project_data

                # Simular tiempo de procesamiento
                time.sleep(random.uniform(1.5, 3.5))

        # Finalizar proceso
        if project_key in session:
            project_data = session[project_key]
            project_data['progress'] = 100
            project_data['current_stage'] = 'Proyecto completado'
            if 'new_messages' not in project_data:
                project_data['new_messages'] = []
            project_data['new_messages'].append("¡Proyecto generado exitosamente!")
            project_data['end_time'] = datetime.now().isoformat()
            session[project_key] = project_data

    except Exception as e:
        print(f"Error en proceso de desarrollo: {str(e)}")
        if project_key in session:
            project_data = session[project_key]
            if 'new_messages' not in project_data:
                project_data['new_messages'] = []
            project_data['new_messages'].append(f"Error en el proceso de desarrollo: {str(e)}")
            session[project_key] = project_data

from dotenv import load_dotenv
import openai
import anthropic
from anthropic import Anthropic
import eventlet
import git
from github import Github
import requests
import google.generativeai as genai
import os
import logging
import json
import re
import shutil
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

# Comentamos el monkey patch para evitar conflictos con OpenAI y otras bibliotecas
# eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# Configurar APIs de IA directamente en el código
try:
    # Configurar OpenAI API
    openai_api_key = "tu_clave_openai_aqui"  # Reemplazar con tu clave real
    if openai_api_key != "tu_clave_openai_aqui":
        # Configurar globalmente la API key de OpenAI
        openai.api_key = openai_api_key
        # Solo mostrar los primeros caracteres por seguridad
        masked_key = openai_api_key[:5] + "..." + openai_api_key[-5:]
        logging.info(f"OpenAI API key configurada: {masked_key}")
    else:
        logging.warning("OpenAI API key no configurada correctamente.")
except Exception as e:
    logging.error(f"Error al configurar OpenAI API: {str(e)}")

try:
    # Configurar Anthropic API
    anthropic_api_key = "tu_clave_anthropic_aqui"  # Reemplazar con tu clave real
    if anthropic_api_key != "tu_clave_anthropic_aqui":
        logging.info("Anthropic API key configured successfully.")
    else:
        logging.warning("Anthropic API key no configurada correctamente.")
except Exception as e:
    logging.error(f"Error al configurar Anthropic API: {str(e)}")

try:
    # Configurar Gemini API
    gemini_api_key = "tu_clave_gemini_aqui"  # Reemplazar con tu clave real
    if gemini_api_key != "tu_clave_gemini_aqui":
        genai.configure(api_key=gemini_api_key)
        logging.info("Gemini API key configured successfully.")
    else:
        logging.warning("Gemini API key no configurada correctamente.")
except Exception as e:
    logging.error(f"Error al configurar Gemini API: {str(e)}")

# Helper function to determine file type for syntax highlighting
def get_file_type(filename):
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    extension_map = {
        'py': 'python',
        'js': 'javascript',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'md': 'markdown',
        'txt': 'text',
        'sh': 'bash',
        'yml': 'yaml',
        'yaml': 'yaml',
    }
    return extension_map.get(extension, 'text')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///codestorm.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set session secret
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models and create tables
with app.app_context():
    try:
        import models
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")

# Create user workspaces directory if it doesn't exist
WORKSPACE_ROOT = Path("./user_workspaces")
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# Get API keys from environment - force reload from .env
load_dotenv(override=True)
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# Initialize API clients but handle exceptions appropriately
openai_client = None
if openai_api_key:
    try:
        # Configurar la API key globalmente
        openai.api_key = openai_api_key
        # Inicializar el cliente
        openai_client = openai.OpenAI()
        logging.info(f"OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {str(e)}")
        openai_client = None
else:
    logging.warning("OPENAI_API_KEY not found. OpenAI features will not work.")

# Initialize Anthropic client if key exists
anthropic_client = None
if anthropic_api_key:
    try:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        logging.info("Anthropic client initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing Anthropic client: {str(e)}")
        anthropic_client = None
else:
    logging.warning("ANTHROPIC_API_KEY not found. Anthropic features will not work.")

# Initialize Gemini client if key exists
gemini_model = None
if gemini_api_key:
    try:
        # La configuración ya se hizo más arriba
        gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        logging.info("Gemini model initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing Gemini model: {str(e)}")
        gemini_model = None
else:
    logging.warning("GEMINI_API_KEY not found. Gemini features will not work.")

def get_user_workspace(user_id="default"):
    """Get or create a workspace directory for the user."""
    workspace_path = WORKSPACE_ROOT / user_id
    if not workspace_path.exists():
        workspace_path.mkdir(parents=True)
        # Create a README file in the workspace
        with open(workspace_path / "README.md", "w") as f:
            f.write("# Workspace\n\nEste es tu espacio de trabajo. Usa los comandos para crear y modificar archivos aquí.")

    # Track workspace in the database if possible
    try:
        from models import User, Workspace

        # Use a default user if no proper authentication is set up
        default_user = db.session.query(User).filter_by(username="default_user").first()
        if not default_user:
            default_user = User(
                username="default_user",
                email="default@example.com",
            )
            default_user.set_password("default_password")
            db.session.add(default_user)
            db.session.commit()

        # Check if workspace exists in database
        workspace = db.session.query(Workspace).filter_by(
            user_id=default_user.id,
            name=user_id
        ).first()

        if not workspace:
            # Create a new workspace record
            workspace = Workspace(
                name=user_id,
                path=str(workspace_path),
                user_id=default_user.id,
                is_default=True,
                last_accessed=datetime.utcnow()
            )
            db.session.add(workspace)
            db.session.commit()
        else:
            # Update the last accessed time
            workspace.last_accessed = datetime.utcnow()
            db.session.commit()

    except Exception as e:
        logging.error(f"Error tracking workspace in database: {str(e)}")

    return workspace_path

# Función interna para ejecutar comandos
def execute_command_internal(command):
    """Ejecuta un comando en el workspace del usuario y devuelve el resultado."""
    try:
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Registrar el comando para depuración

@app.route('/api/delete_file', methods=['GET', 'DELETE'])
def delete_file_endpoint():
    """API endpoint para eliminar un archivo del workspace del usuario."""
    try:
        # Obtener la ruta del archivo a eliminar
        if request.method == 'DELETE':
            data = request.json
            file_path = data.get('path')
        else:  # GET method
            file_path = request.args.get('path')
            
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_id = session.get('user_id', 'default')
        user_workspace = get_user_workspace(user_id)

        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                message = f'Directorio {file_path} eliminado exitosamente'
            else:
                os.remove(full_path)
                message = f'Archivo {file_path} eliminado exitosamente'

            # Notificar cambios a los clientes conectados
            socketio.emit('file_system_changed', {
                'user_id': user_id,
                'command': f'delete {file_path}',
                'timestamp': time.time()
            }, room=user_id)

            return jsonify({
                'success': True,
                'message': message,
                'file_path': file_path
            })
        except Exception as e:
            logging.error(f"Error al eliminar archivo: {str(e)}")
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

@app.route('/api/developer_assistant', methods=['POST'])
def developer_assistant():
    """API para el asistente de desarrollo que responde a consultas específicas."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        query = data.get('query', '')
        context = data.get('context', '')
        model = data.get('model', 'openai')  # Modelo predeterminado
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó una consulta'
            }), 400
            
        # Procesamiento con la API seleccionada
        if model == 'openai' and openai_api_key:
            try:
                client = openai.OpenAI()
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un asistente de desarrollo experto que ayuda con tareas de programación."},
                        {"role": "user", "content": f"Contexto: {context}\n\nConsulta: {query}"}
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
                logging.error(f"Error con OpenAI API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error con OpenAI API: {str(e)}'
                }), 500
        elif model == 'anthropic' and anthropic_api_key:
            try:
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=2000,
                    temperature=0.7,
                    system="Eres un asistente de desarrollo experto que ayuda con tareas de programación.",
                    messages=[{"role": "user", "content": f"Contexto: {context}\n\nConsulta: {query}"}]
                )
                response = completion.content[0].text
                
                return jsonify({
                    'success': True,
                    'response': response,
                    'model_used': 'anthropic'
                })
            except Exception as e:
                logging.error(f"Error con Anthropic API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error con Anthropic API: {str(e)}'
                }), 500
        elif model == 'gemini' and gemini_api_key:
            try:
                # Make sure Gemini is configured properly
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=gemini_api_key)
                    
                gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                gemini_response = gemini_model.generate_content(f"Contexto: {context}\n\nConsulta: {query}")
                response = gemini_response.text
                
                return jsonify({
                    'success': True,
                    'response': response,
                    'model_used': 'gemini'
                })
            except Exception as e:
                logging.error(f"Error con Gemini API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error con Gemini API: {str(e)}'
                }), 500
        else:
            # Caso de respuesta predeterminada si ninguna API está disponible
            available_models = []
            if openai_api_key:
                available_models.append('openai')
            if anthropic_api_key:
                available_models.append('anthropic')
            if gemini_api_key:
                available_models.append('gemini')
                
            if available_models:
                message = f"El modelo '{model}' no está disponible. Modelos disponibles: {', '.join(available_models)}"
            else:
                message = "No hay modelos de IA disponibles. Por favor configura una API key en el panel de Secrets."
                
            return jsonify({
                'success': False,
                'message': message,
                'available_models': available_models
            })

    except Exception as e:
        logging.error(f"Error en el asistente de desarrollo: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Error al procesar la solicitud: {str(e)}'
        }), 500

        logging.debug(f"Ejecutando comando: '{command}' en workspace {workspace_path}")

        # Execute the command
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(workspace_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # Registrar resultados para depuración
        logging.debug(f"Resultado comando: código={process.returncode}, stdout={len(stdout)} bytes, stderr={len(stderr)} bytes")

        return {
            'success': True,
            'stdout': stdout,
            'stderr': stderr,
            'status': process.returncode
        }
    except Exception as e:
        logging.error(f"Error executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'message': str(e)
        }

# Función interna para procesar lenguaje natural
def process_natural_language_internal(instruction):
    """Procesa instrucciones en lenguaje natural para manipular archivos."""
    try:
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Registrar la instrucción para depuración
        logging.debug(f"Procesando instrucción: '{instruction}' en workspace {workspace_path}")

        # Detectar la intención del usuario mediante reglas sencillas
        instruction_lower = instruction.lower()

        # Caso 1: Crear archivo
        if re.search(r'crea|crear|nuevo|generar?', instruction_lower) and re.search(r'archivo|fichero|file', instruction_lower):
            # Intentar extraer nombre de archivo
            file_name_match = re.search(r'(?:llamado|llamada|nombre|titulado|titulada|nombrado|nombrada)\s+["\']?([a-zA-Z0-9_\-\.]+)["\']?', instruction_lower)
            file_name = file_name_match.group(1) if file_name_match else "nuevo_archivo.txt"

            # Intentar extraer contenido
            content_match = re.search(r'(?:con(?:tenido)?|que\s+diga|con\s+el\s+texto)\s+["\']?([\s\S]+?)["\']?(?:\s*$|y\s+|\.)', instruction, re.IGNORECASE)
            content = content_match.group(1).strip() if content_match else "# Nuevo archivo creado"

            # Crear archivo
            file_path = file_name.replace('..', '')  # Prevenir path traversal
            target_file = (workspace_path / file_path).resolve()

            # Verificar seguridad
            if not str(target_file).startswith(str(workspace_path.resolve())):
                return {
                    'success': False,
                    'message': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
                }

            # Crear directorios si no existen
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Escribir archivo
            with open(target_file, 'w') as f:
                f.write(content)

            return {
                'success': True,
                'message': f'Archivo {file_path} creado correctamente',
                'file_path': file_path
            }

        # Caso 2: Mostrar contenido de archivo
        elif re.search(r'muestra|mostrar|ver|leer|cat', instruction_lower) and re.search(r'(?:contenido|archivo|fichero|file)', instruction_lower):
            # Extraer nombre de archivo
            file_parts = re.split(r'(?:de|del|el|archivo|fichero|contenido)', instruction_lower)
            possible_file = file_parts[-1].strip() if len(file_parts) > 1 else ""

            if not possible_file:
                return {
                    'success': False,
                    'message': 'No se especificó un nombre de archivo'
                }

            file_path = possible_file.replace('..', '')  # Prevenir path traversal
            target_file = (workspace_path / file_path).resolve()

            # Verificar seguridad
            if not str(target_file).startswith(str(workspace_path.resolve())):
                return {
                    'success': False,
                    'message': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
                }

            # Verificar si el archivo existe
            if not target_file.exists():
                return {
                    'success': False,
                    'message': f'El archivo {file_path} no existe'
                }

            # Leer contenido
            with open(target_file, 'r') as f:
                content = f.read()

            # Determinar tipo de archivo para resaltado de sintaxis
            file_type = get_file_type(target_file.name)

            return {
                'success': True,
                'message': f'Contenido del archivo {file_path}',
                'file_path': file_path,
                'content': content,
                'file_type': file_type
            }

        # Fallback: Ejecutar como comando

@app.route('/api/format_code', methods=['POST'])
def format_code():
    """Formatea el código del usuario basado en el lenguaje especificado."""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')

        if not code:
            return jsonify({'success': False, 'error': 'No se proporcionó código para formatear'}), 400

        # Formatear según el lenguaje
        formatted_code = code

        if language == 'python':
            try:
                # Intenta usar black para formatear
                import black
                mode = black.Mode()
                formatted_code = black.format_str(code, mode=mode)
            except Exception as e:
                logging.warning(f"Error usando black: {str(e)}, usando formato básico")
                # Formateo básico para Python
                import autopep8
                formatted_code = autopep8.fix_code(code)

        elif language in ['javascript', 'typescript', 'js', 'ts']:
            # Formateo básico para JavaScript/TypeScript
            try:
                import jsbeautifier
                opts = jsbeautifier.default_options()
                opts.indent_size = 2
                formatted_code = jsbeautifier.beautify(code, opts)
            except Exception as e:
                logging.warning(f"Error formateando JavaScript: {str(e)}")

        elif language in ['html', 'xml']:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(code, 'html.parser')
                formatted_code = soup.prettify()
            except Exception as e:
                logging.warning(f"Error formateando HTML: {str(e)}")

        elif language == 'css':
            try:
                import cssbeautifier
                opts = cssbeautifier.default_options()
                formatted_code = cssbeautifier.beautify(code, opts)

@app.route('/api/format_code', methods=['POST'])
def format_code():
    """
    Formatea el código según el lenguaje especificado.
    """
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({'success': False, 'error': 'No se proporcionó código para formatear'}), 400

        code = data['code']
        language = data.get('language', 'python')

        # Formatear código según el lenguaje
        formatted_code = code  # Por defecto, devolver el mismo código

        if language == 'python':
            try:
                import black
                formatted_code = black.format_str(code, mode=black.Mode())
            except Exception as e:
                # Si black falla, intentar con autopep8
                try:
                    import autopep8
                    formatted_code = autopep8.fix_code(code)
                except Exception as e2:
                    logging.warning(f"Error al formatear Python con autopep8: {str(e2)}")

        elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
            try:
                import jsbeautifier
                opts = jsbeautifier.default_options()
                opts.indent_size = 2
                opts.space_in_empty_paren = True
                formatted_code = jsbeautifier.beautify(code, opts)
            except Exception as e:
                logging.warning(f"Error al formatear JavaScript/TypeScript: {str(e)}")

        elif language in ['html', 'xml']:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(code, 'html.parser')
                formatted_code = soup.prettify()
            except Exception as e:
                logging.warning(f"Error al formatear HTML/XML: {str(e)}")

        elif language in ['css', 'scss', 'less']:
            try:
                import cssbeautifier
                opts = cssbeautifier.default_options()
                opts.indent_size = 2
                formatted_code = cssbeautifier.beautify(code, opts)
            except Exception as e:
                logging.warning(f"Error al formatear CSS: {str(e)}")

        return jsonify({
            'success': True,
            'formatted_code': formatted_code
        })

    except Exception as e:
        logging.error(f"Error al formatear código: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

            except Exception as e:
                logging.warning(f"Error formateando CSS: {str(e)}")

        return jsonify({
            'success': True,
            'formatted_code': formatted_code
        })

    except Exception as e:
        logging.error(f"Error al formatear código: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

        else:
            return execute_command_internal(instruction)

    except Exception as e:
        logging.error(f"Error processing natural language: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'message': str(e)
        }

# Función interna para generar archivos complejos
def generate_complex_file_internal(description, file_type="html", filename="", agent_id="developer"):
    """Genera un archivo complejo basado en una descripción."""
    try:
        # Get user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Generar nombre de archivo si no se proporciona
        if not filename:
            words = re.sub(r'[^\w\s]', '', description.lower()).split()
            filename = '_'.join(words[:3])[:30]

            # Añadir extensión según tipo
            if file_type == 'html':
                filename += '.html'
            elif file_type == 'css':
                filename += '.css'
            elif file_type == 'js':
                filename += '.js'
            elif file_type == 'py':
                filename += '.py'
            else:
                filename += '.txt'

        # Asegurarse de que la extensión existe
        if '.' not in filename:
            filename += f'.{file_type}'

        logging.info(f"Generando archivo complejo: {filename} del tipo {file_type}")

        # Generar contenido usando el modelo seleccionado
        file_content = ""

        # Seleccionar el modelo apropiado para la generación de archivos (OpenAI por defecto)
        selected_model = "openai"
        if not openai_api_key and anthropic_api_key:
            selected_model = "anthropic"
        elif not openai_api_key and not anthropic_api_key and gemini_api_key:
            selected_model = "gemini"

        logging.info(f"Usando modelo {selected_model} para generar archivo")

        # Preparar prompt según tipo de archivo
        file_type_prompt = ""
        if file_type == 'html' or '.html' in filename:
            file_type_prompt = """Genera un archivo HTML moderno y atractivo.
            Usa las mejores prácticas de HTML5, CSS responsivo y, si es necesario, JavaScript moderno.
            Asegúrate de que el código sea válido, accesible y optimizado para móviles.
            El archivo debe usar Bootstrap para estilos y ser visualmente atractivo."""
        elif file_type == 'css' or '.css' in filename:
            file_type_prompt = """Genera un archivo CSS moderno y eficiente.
            Usa las mejores prácticas de CSS3, incluyendo flexbox y/o grid donde sea apropiado.
            El código debe ser responsivo y seguir metodologías como BEM si es apropiado."""
        elif file_type == 'js' or '.js' in filename:
            file_type_prompt = """Genera un archivo JavaScript moderno y bien estructurado.
            Usa características modernas de ES6+ y mejores prácticas.
            El código debe ser funcional, eficiente y bien comentado."""
        elif file_type == 'py' or '.py' in filename:
            file_type_prompt = """Genera un archivo Python bien estructurado y eficiente.
            Sigue PEP 8 y las mejores prácticas de Python.
            El código debe incluir documentación adecuada y manejo de errores."""
        else:
            file_type_prompt = """Genera un archivo de texto plano con el contenido solicitado,
            bien estructurado y formateado de manera clara y legible."""

        # Construir prompt completo
        prompt = f"""Como experto desarrollador, crea un archivo {file_type} con el siguiente requerimiento:

        "{description}"

        {file_type_prompt}

        Genera SOLO el código sin explicaciones adicionales. No incluyas markdown ni comentarios sobre lo que haces.
        """

        # Ejecutar con el modelo seleccionado
        if selected_model == "anthropic" and anthropic_api_key:
            try:
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=3000,
                    temperature=0.7,
                    system="Eres un experto en desarrollo de software especializado en crear archivos de alta calidad.",
                    messages=[{"role": "user", "content": prompt}]
                )
                file_content = completion.content[0].text.strip()
            except Exception as e:
                logging.error(f"Error en Anthropic al generar archivo: {str(e)}")
                raise Exception(f"Error con Anthropic API: {str(e)}")

        elif selected_model == "gemini" and gemini_api_key:
            try:
                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                gemini_response = model.generate_content(prompt)
                file_content = gemini_response.text.strip()
            except Exception as e:
                logging.error(f"Error en Gemini al generar archivo: {str(e)}")
                raise Exception(f"Error con Gemini API: {str(e)}")
        else:
            # Por defecto, usar OpenAI
            try:
                client = openai.OpenAI()
                completion = client.chat.completions.create(
                    model=""(?:\w+)?\s*([\s\S]+?)\s*```", file_content)
        if match:
            file_content = match.group(1).strip()

        # Guardar archivo
        file_path = filename.replace('..', '')  # Prevenir path traversal
        target_file = (workspace_path / file_path).resolve()

        # Verificar seguridad
        if not str(target_file).startswith(str(workspace_path.resolve())):
            return {
                'success': False,
                'message': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
            }

        # Crear directorios si no existen
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Escribir archivo
        with open(target_file, 'w') as f:
            f.write(file_content)

        # Notificar cambio
        file_data = {
            'path': file_path,
            'name': target_file.name,
            'type': 'file'
        }
        try:
            notify_file_change(user_id, 'create', file_data)
        except Exception as e:
            logging.warning(f"Error al notificar cambio de archivo: {str(e)}")
            # Si la notificación falla, continuamos

        return {
            'success': True,
            'message': f'Archivo {file_path} generado correctamente',
            'file_path': file_path,
            'file_content': file_content
        }

    except Exception as e:
        logging.error(f"Error generating complex file: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'message': str(e)
        }

# Función para procesar mensajes de chat internamente
def handle_chat_internal(data):
    """Versión interna de handle_chat para usar desde otras funciones."""
    try:
        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'default')
        agent_prompt = data.get('agent_prompt', '')
        context = data.get('context', [])
        model_choice = data.get('model', 'openai')
        collaborative_mode = data.get('collaborative_mode', True)  # Modo colaborativo activado por defecto

        if not user_message:
            return {'error': 'No message provided', 'response': 'Error: No se proporcionó un mensaje.'}

        # Configurar prompts específicos según el agente seleccionado
        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar a los usuarios con tareas de programación, desde la corrección de errores hasta la implementación de funcionalidades completas. Puedes modificar archivos, ejecutar comandos y resolver problemas técnicos específicos.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas a los usuarios a tomar decisiones sobre la estructura del código, patrones de diseño y selección de tecnologías. Puedes proporcionar diagramas conceptuales y recomendaciones sobre la organización de componentes.",
            'advanced': "Eres un Agente Avanzado de Software con experiencia en integraciones complejas y funcionalidades avanzadas. Puedes asesorar sobre tecnologías emergentes, optimización de rendimiento y soluciones a problemas técnicos sofisticados. Tienes la capacidad de coordinar entre diferentes componentes y sistemas."
        }

        # Si no se proporcionó un prompt específico, usar uno predefinido basado en el agente
        if not agent_prompt:
            agent_prompt = agent_prompts.get(agent_id, "Eres un asistente de desarrollo de software experto y útil.")

        # Añadir capacidades de manipulación de archivos al prompt para todos los agentes
        file_capabilities = "\n\nPuedes ayudar al usuario a manipular archivos usando comandos como: 'crea un archivo index.js con este contenido...', 'modifica config.py para añadir...', 'muestra el contenido de app.js', etc. Puedes ejecutar comandos en la terminal con: 'ejecuta npm install', 'ejecuta python run.py', etc."
        agent_prompt += file_capabilities

        # Si está en modo colaborativo, añadir información sobre otros agentes
        if collaborative_mode:
            agent_prompt += "\n\nEstás trabajando en modo colaborativo con otros agentes especializados. Si la consulta del usuario requiere conocimientos fuera de tu dominio, puedes sugerir consultar a otro agente especializado o solicitar su perspectiva adicional."

def find_available_model():
    """
    Encuentra el primer modelo de IA disponible basado en las API keys configuradas.
    Retorna el nombre del modelo o None si no hay ninguno disponible.
    """
    if os.environ.get('OPENAI_API_KEY'):
        return 'gpt4o'
    elif os.environ.get('ANTHROPIC_API_KEY'):
        return 'claude'
    elif os.environ.get('GEMINI_API_KEY'):
        return 'gemini'
    return None

def log_processing_metrics(original_code, corrected_code, language, model):
    """
    Registra métricas sobre el procesamiento de código para análisis y mejora.
    """
    try:
        # Calcular métricas básicas
        original_lines = len(original_code.split('\n'))
        corrected_lines = len(corrected_code.split('\n'))
        changed_lines_percent = abs(corrected_lines - original_lines) / original_lines * 100 if original_lines > 0 else 0

        # Registrar métricas
        logging.info(f"Métricas de corrección - Modelo: {model}, Lenguaje: {language}")
        logging.info(f"Líneas originales: {original_lines}, Líneas corregidas: {corrected_lines}")
        logging.info(f"Cambio porcentual: {changed_lines_percent:.2f}%")

        # Aquí se podrían implementar métricas más avanzadas como:

def enhance_results(result, original_code, language, static_analysis):
    """
    Mejora los resultados con información adicional y validaciones.
    """
    enhanced = result.copy()
    enhanced['success'] = True

    # Asegurarse de que el código corregido sea válido
    if not enhanced.get('corrected_code'):
        enhanced['corrected_code'] = original_code
        enhanced['changes'] = enhanced.get('changes', [])
        enhanced['changes'].append({
            'description': 'No se pudieron aplicar correcciones',
            'lineNumbers': [1],
            'category': 'error',
            'importance': 'alta'
        })

    # Asegurarse de que todos los cambios tengan los campos requeridos
    if 'changes' in enhanced:
        normalized_changes = []
        for change in enhanced['changes']:
            normalized_change = {
                'description': change.get('description', 'Sin descripción'),
                'lineNumbers': change.get('lineNumbers', change.get('line_numbers', [1])),
                'category': change.get('category', 'general'),
                'importance': change.get('importance', 'media')
            }
            normalized_changes.append(normalized_change)
        enhanced['changes'] = normalized_changes
    else:
        enhanced['changes'] = []

    # Agregar métricas de código si no existen
    if 'metrics' not in enhanced:
        enhanced['metrics'] = calculate_code_metrics(original_code, enhanced['corrected_code'], language)

    # Agregar recomendaciones si no existen
    if 'recommendations' not in enhanced:
        enhanced['recommendations'] = []

    # Agregar diferencias para visualización
    enhanced['diff'] = generate_diff(original_code, enhanced['corrected_code'])

    # Agregar información de análisis estático si está disponible
    if static_analysis and static_analysis.get('issues'):
        enhanced['static_analysis'] = {
            'issues_count': len(static_analysis['issues']),
            'issues_summary': summarize_issues(static_analysis['issues'])
        }

    return enhanced

def calculate_code_metrics(original_code, corrected_code, language):
    """
    Calcula métricas de código para comparar original y corregido.
    """
    # Métricas básicas
    metrics = {
        'loc': len(corrected_code.split('\n')),
        'original_loc': len(original_code.split('\n')),
        'complexity': 0,
        'errors_fixed': 0,
        'warnings_fixed': 0,
        'performance_improvements': 0,
        'readability_improvements': 0
    }

    # Estimar complejidad y otras métricas según el lenguaje
    try:
        # Complejidad ciclomática básica
        control_keywords = {
            'python': ['if', 'for', 'while', 'except', 'with', 'def'],
            'javascript': ['if', 'for', 'while', 'try', 'switch', 'function'],
            'java': ['if', 'for', 'while', 'try', 'switch', 'case', 'catch'],
            'cpp': ['if', 'for', 'while', 'try', 'switch', 'case', 'catch']
        }

        lang_keywords = control_keywords.get(language, control_keywords['python'])
        complexity = 1

        for keyword in lang_keywords:
            complexity += corrected_code.count(f' {keyword} ')

        metrics['complexity'] = complexity

        # Estimar errores corregidos contando líneas modificadas
        orig_lines = original_code.split('\n')
        corr_lines = corrected_code.split('\n')

        metrics['errors_fixed'] = abs(len(orig_lines) - len(corr_lines))

    except Exception as e:
        logging.warning(f"Error calculando métricas de código: {str(e)}")

    return metrics

def generate_diff(original_code, corrected_code):
    """
    Genera un diff básico entre el código original y el corregido.
    """
    try:
        import difflib
        orig_lines = original_code.splitlines()
        corr_lines = corrected_code.splitlines()

        diff = difflib.unified_diff(
            orig_lines, 
            corr_lines,
            fromfile='original',
            tofile='corregido',
            lineterm=''
        )
        return '\n'.join(diff)
    except Exception as e:
        logging.warning(f"Error generando diff: {str(e)}")
        return "No se pudo generar el diff"

def summarize_issues(issues):
    """
    Genera un resumen de los problemas encontrados en el análisis estático.
    """
    if not issues:
        return "No se encontraron problemas en el análisis estático."

    categories = {}
    for issue in issues:
        category = issue.get('severity', 'unknown')
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    summary = []
    for category, count in categories.items():
        summary.append(f"{count} {category}")

    return f"Resumen de problemas: {', '.join(summary)}"

        # - Detección de patrones corregidos comunes
        # - Comparación de complejidad ciclomática
        # - Análisis de mejoras específicas por lenguaje

    except Exception as e:
        logging.warning(f"Error al registrar métricas de procesamiento: {str(e)}")


        # Preprocesar contexto para dar formato consistente
        formatted_context = []
        for msg in context:
            role = msg.get('role', 'user')
            if role not in ['user', 'assistant', 'system']:
                role = 'user'
            formatted_context.append({
                "role": role,
                "content": msg.get('content', '')
            })

        # Verificar si es una solicitud de gestión de archivos o ejecución de comandos
        is_file_operation = re.search(r'(?:crea|modifica|elimina|muestra|crear|editar|borrar|ver).*?(?:archivo|fichero|file|documento)', user_message, re.IGNORECASE)

        # Detectar comandos para ejecutar directamente en la terminal
        is_command_execution = re.search(r'(?:ejecuta|corre|lanza|inicia|run).*?(?:comando|terminal|consola|cli|bash|shell|\$|>|comando:)', user_message, re.IGNORECASE)

        # Detección directa de comandos de terminal usando un patrón de reconocimiento mejorado
        direct_command_match = re.search(r'(?:ejecuta|corre|terminal|consola|comando)(?:\s+en\s+terminal)?:?\s*[`\'"]?([\w\s\.\-\$\{\}\/\\\|\&\>\<\;\:\*\?$$$$$$$$\=\+\,\_\!]+)[`\'"]?', user_message, re.IGNORECASE)

        # Detectar solicitudes para generar archivos complejos
        is_complex_file_request = re.search(r'(?:crea|genera|hacer|crear|implementa|programa|diseña|haz)\s+(?:una?|el)?\s*(?:página|pagina|sitio|web|componente|interfaz|archivo|aplicación|app)', user_message, re.IGNORECASE)


@app.route('/api/file/delete', methods=['POST'])
def delete_file():
    """Eliminar un archivo o carpeta."""
    try:
        data = request.json
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo'
            }), 400

        file_path = data['file_path']

        # Obtener workspace del usuario
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Crear ruta completa y verificar seguridad
        target_path = (workspace_path / file_path).resolve()
        if not str(target_path).startswith(str(workspace_path.resolve())):
            return jsonify({
                'success': False,
                'error': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
            }), 403

        # Eliminar archivo o directorio
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()

        # Notificar cambio si es posible
        try:
            file_data = {
                'path': file_path,
                'name': target_path.name,
                'type': 'directory' if target_path.is_dir() else 'file'
            }
            notify_file_change(user_id, 'delete', file_data)
        except Exception as e:
            logging.warning(f"Error al notificar cambio de archivo: {str(e)}")

        return jsonify({
            'success': True,
            'message': f'{"Directorio" if target_path.is_dir() else "Archivo"} eliminado correctamente'
        })

    except Exception as e:
        logging.error(f"Error al eliminar archivo: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/rename', methods=['POST'])
def rename_file():
    """Renombrar un archivo o carpeta."""
    try:
        data = request.json
        if not data or 'file_path' not in data or 'new_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo y nuevo nombre'
            }), 400

        file_path = data['file_path']
        new_name = data['new_name']

        # Obtener workspace del usuario
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Crear ruta completa y verificar seguridad
        source_path = (workspace_path / file_path).resolve()
        if not str(source_path).startswith(str(workspace_path.resolve())):
            return jsonify({
                'success': False,
                'error': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
            }), 403

        # Crear ruta de destino
        target_path = source_path.parent / new_name

        # Verificar que el destino no existe
        if target_path.exists():
            return jsonify({
                'success': False,
                'error': f'Ya existe un archivo o directorio con el nombre {new_name}'
            }), 400

        # Renombrar archivo o directorio
        source_path.rename(target_path)

        # Notificar cambio si es posible
        try:
            file_data = {
                'path': str(target_path.relative_to(workspace_path)),
                'name': target_path.name,
                'type': 'directory' if target_path.is_dir() else 'file',
                'old_path': file_path
            }
            notify_file_change(user_id, 'rename', file_data)
        except Exception as e:
            logging.warning(f"Error al notificar cambio de archivo: {str(e)}")

        return jsonify({
            'success': True,
            'message': f'{"Directorio" if target_path.is_dir() else "Archivo"} renombrado correctamente',
            'new_path': str(target_path.relative_to(workspace_path))
        })

    except Exception as e:
        logging.error(f"Error al renombrar archivo: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

        logging.debug(f"Mensaje recibido: '{user_message}'")

        # Procesar comando directo de terminal si se detecta uno
        if direct_command_match:
            try:
                # Extraer el comando a ejecutar
                terminal_command = direct_command_match.group(1).strip()
                logging.debug(f"Ejecutando comando directo: {terminal_command}")

                # Ejecutar el comando
                result = execute_command_internal(terminal_command)

                if result.get('success'):
                    # Construir una respuesta detallada
                    response_message = f"He ejecutado el comando: `{terminal_command}`\n\n"

                    # Mostrar la salida del comando
                    \n{result['stdout']}\n```\\n\n"

                    # Mostrar errores si existen
                    if result.get('stderr'):
                        response_message += f"**Errores/Advertencias:**\n```\n{result['stderr']}\n```\n\n"

                    # Añadir información sobre el estado de salida
                    if 'status' in result:
                        status_emoji = "✅" if result['status'] == 0 else "⚠️"
                        response_message += f"{status_emoji} Comando finalizado con código de salida: {result['status']}"

                    return {'response': response_message}
                else:
                    return {'response': f"No pude ejecutar el comando: {result.get('message', 'Error desconocido')}"}
            except Exception as e:
                logging.error(f"Error al ejecutar comando directo: {str(e)}")
                # Continuar con el procesamiento normal si falla

        # Si es una solicitud de generación de archivo complejo
        if is_complex_file_request and not is_file_operation:
            try:
                # Procesar solicitud de generación de archivo complejo
                description = user_message
                file_type = "html"  # Por defecto HTML

                # Determinar tipo de archivo según el contenido
                if any(word in user_message.lower() for word in ['css', 'estilo', 'estilos']):
                    file_type = "css"
                elif any(word in user_message.lower() for word in ['javascript', 'js', 'interactividad']):
                    file_type = "js"
                elif any(word in user_message.lower() for word in ['python', 'script', 'programa', 'backend']):
                    file_type = "py"

                # Intentar extraer nombre de archivo si se menciona
                filename = ""
                name_match = re.search(r'(?:llamado|llamada|nombre|titulado|titulada|nombrado|nombrada)\s+["\']?([a-zA-Z0-9_\-]+)["\']?', user_message, re.IGNORECASE)
                if name_match:
                    filename = name_match.group(1)

                # Generar el archivo complejo
                response = generate_complex_file_internal(description, file_type, filename, agent_id)

                if response.get('success'):
                    file_path = response.get('file_path', '')
                    response_message = f"He creado el archivo que solicitaste en `{file_path}`.\n\n"
                    response_message += "¿Te gustaría que realice algún cambio en este archivo? Puedo modificarlo para ajustarlo mejor a tus necesidades."

                    # Añadir ejemplo de uso o vista previa si es HTML
                    if file_type == 'html':
                        response_message += f"\n\nPuedes ver la página en la ruta `/preview?file={file_path}`."
                else:
                    response_message = f"Lo siento, no pude crear el archivo: {response.get('message', 'Error desconocido')}"

                return {'response': response_message}
            except Exception as e:
                logging.error(f"Error processing complex file request: {str(e)}")
                # Continuar con el procesamiento normal si falla

        if is_file_operation or is_command_execution:
            try:
                # Procesar como una instrucción de manipulación de archivos
                result = process_natural_language_internal(user_message)
                if result.get('success'):
                    # Construir una respuesta contextual más elaborada
                    response_message = f"He procesado tu instrucción: {result.get('message', 'Operación completada.')}"

                    # Añadir detalles según el tipo de operación
                    if 'content' in result:
                        # Para visualización de archivos
                        response_message += f"\n\nContenido del archivo:\n```\n{result['content']}\n```"

                        if 'file_type' in result:
                            response_message += f"\n\nTipo de archivo detectado: {result['file_type']}"

                    if 'stdout' in result:
                        # Para ejecución de comandos
                        response_message += f"\n\nSalida del comando:\n```\n{result['stdout']}\n```"

                        if result.get('stderr'):
                            response_message += f"\n\nErrores/Advertencias:\n```\n{result['stderr']}\n```"

                    return {'response': response_message}
                else:
                    # Si hubo error, proporcionar información detallada
                    error_message = f"No pude completar la operación: {result.get('message', 'Error desconocido.')}"

                    # Sugerir soluciones según el error
                    if 'no existe' in result.get('message', '').lower():
                        error_message += "\n\n¿Quieres que cree este archivo primero? Puedes pedirme 'Crea un archivo [nombre] con [contenido]'."
                    elif 'ya existe' in result.get('message', '').lower():
                        error_message += "\n\n¿Quieres modificar este archivo en lugar de crearlo? Puedes pedirme 'Modifica el archivo [nombre] con [contenido]'."

                    return {'response': error_message}
            except Exception as e:
                logging.error(f"Error processing file instruction: {str(e)}")
                # Continuar con el procesamiento normal si falla

        # Generar respuesta según el modelo seleccionado
        response = ""

        if model_choice == 'anthropic' and anthropic_api_key:
            # Usar Anthropic Claude
            try:
                logging.info("Intentando generar respuesta con Anthropic Claude")

                client = anthropic.Anthropic(api_key=anthropic_api_key)
                messages = [{"role": "system", "content": agent_prompt}]

                # Añadir mensajes de contexto
                for msg in formatted_context:
                    messages.append({"role": msg['role'], "content": msg['content']})

                # Añadir el mensaje actual del usuario
                messages.append({"role": "user", "content": user_message})

                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.7
                )
                response = completion.content[0].text
                logging.debug(f"Respuesta generada con Anthropic: {response[:100]}...")
            except Exception as e:
                logging.error(f"Error with Anthropic API: {str(e)}")
                logging.error(traceback.format_exc())
                response = f"Lo siento, hubo un error al procesar tu solicitud con Anthropic: {str(e)}"

        elif model_choice == 'gemini' and gemini_api_key:
            # Usar Google Gemini
            try:
                logging.info("Intentando generar respuesta con Google Gemini")

                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')

                # Construir el prompt con contexto
                full_prompt = agent_prompt + "\n\n"

                for msg in formatted_context:
                    prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                    full_prompt += prefix + msg['content']

                # Añadir instrucciones para corrección de código al prompt
                full_prompt += f"\n```{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"

                # Configurar y hacer la llamada a la API
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un experto programador especializado en corregir código."},
                        {"role": "user", "content": full_prompt}
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

        elif model == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                # Importar anthropic si es necesario
                import anthropic
                from anthropic import Anthropic

                # Inicializar cliente
                client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

                prompt = f"""Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas.

CÓDIGO:
```{language}
{code}
```

INSTRUCCIONES:
{instructions}

Responde EXACTAMENTE en este formato JSON y nada más:
```json
{{
  "correctedCode": "código corregido aquí",
  "changes": [
    {{
      "description": "descripción del cambio 1",
      "lineNumbers": [1, 2]
    }}
  ],
  "explanation": "explicación detallada de los cambios"
}}
```
"""

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=4000,
                    system="Eres un experto programador especializado en corregir código. Siempre respondes en formato JSON válido.",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )

                try:
                    # Buscar JSON en formato de bloque de código
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response.content[0].text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1).strip())
                        except json.JSONDecodeError:
                            # Si el contenido dentro de las comillas triples no es JSON válido
                            result = {
                                "correctedCode": code,
                                "changes": [{"description": "No se pudo procesar el JSON correctamente", "lineNumbers": [1]}],
                                "explanation": "Error al procesar la respuesta. Probablemente el formato no es correcto."
                            }
                    else:
                        # Intenta extraer cualquier objeto JSON de la respuesta completa
                        try:
                            # Buscar un objeto JSON completo en cualquier parte del texto
                            json_match = re.search(r'(\{.*\})', response.content[0].text, re.DOTALL)
                            if json_match:
                                result = json.loads(json_match.group(1))
                            else:
                                # Fallback a un formato básico si no hay JSON
                                result = {
                                    "correctedCode": code,
                                    "changes": [],
                                    "explanation": "No se pudo procesar correctamente la respuesta del modelo."
                                }
                        except (json.JSONDecodeError, AttributeError):
                            result = {
                                "correctedCode": code,
                                "changes": [],
                                "explanation": "No se pudo extraer JSON válido de la respuesta."
                            }
                except Exception as e:
                    logging.error(f"Error procesando respuesta de Anthropic: {str(e)}")
                    result = {
                        "correctedCode": code,
                        "changes": [],
                        "explanation": f"Error procesando respuesta de Anthropic: {str(e)}"
                    }

                logging.info("Código corregido con Anthropic")

            except Exception as e:
                logging.error(f"Error con API de Anthropic: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al conectar con Anthropic: {str(e)}'
                }), 500

        elif model == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                # Usar genai para procesar con Gemini
                import google.generativeai as genai

                if not hasattr(genai, '_configured') or not genai._configured:
                    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

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

                # Extraer el JSON de la respuesta de Gemini
                import re
                json_match = re.search(r'```json(.*?)if json_match:
                    result = json.loads(json_match.group(1).strip())
                else:
                    # Intentar extraer cualquier JSON de la respuesta
                    json_match = re.search(r'{.*}', response.text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                    else:
                        # Fallback a un formato básico
                        result = {
                            "correctedCode": code,
                            "changes": [],
                            "explanation": "No se pudo procesar correctamente la respuesta del modelo."
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

        # Verificar que la respuesta contiene los campos necesarios
        if not result or 'corrected_code' not in result:
            return jsonify({
                'success': False,
                'error': 'La respuesta del modelo no incluye el código corregido'
            }), 500

        # Devolver resultado en formato esperado por el frontend
        return jsonify({
            'success': True,
            'corrected_code': result.get('corrected_code', ''),
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


def perform_static_analysis(code, language):
    """
    Realiza análisis estático básico del código antes de enviarlo al modelo.
    Esto ayuda a identificar problemas obvios y proporcionar contexto adicional.
    """
    results = {
        'issues': [],
        'metrics': {
            'loc': len(code.split('\n')),
            'complexity': 0
        }
    }

    try:
        # Análisis específico por lenguaje
        if language == 'python':
            # Usar herramientas como pylint, pyflakes o flake8 (versión simplificada)
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(suffix='.py', mode='w+') as temp:
                temp.write(code)
                temp.flush()

                try:
                    # Intentar ejecutar flake8 si está disponible
                    result = subprocess.run(['flake8', temp.name], capture_output=True, text=True)
                    if result.returncode != 0:
                        for line in result.stdout.splitlines():
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                line_num = int(parts[1])
                                message = parts[2].strip()
                                results['issues'].append({
                                    'line': line_num,
                                    'message': message,
                                    'severity': 'warning'
                                })
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Fallback a análisis básico si flake8 no está disponible
                    pass

                # Calcular complejidad ciclomática básica contando estructuras de control
                control_keywords = ['if', 'for', 'while', 'except', 'with']
                complexity = 1  # Complejidad base
                for keyword in control_keywords:
                    complexity += code.count(f' {keyword} ')
                results['metrics']['complexity'] = complexity

        elif language == 'javascript':
            # Análisis básico para JavaScript
            control_keywords = ['if', 'for', 'while', 'try', 'switch']
            complexity = 1
            for keyword in control_keywords:
                complexity += code.count(f' {keyword} ')
            results['metrics']['complexity'] = complexity

            # Detectar problemas comunes
            if 'var ' in code:
                results['issues'].append({
                    'line': 0,  # Línea genérica
                    'message': 'Uso de "var" en lugar de "let" o "const"',
                    'severity': 'suggestion'
                })

            if '== null' in code or '== undefined' in code:
                results['issues'].append({
                    'line': 0,
                    'message': 'Uso de operador de igualdad débil con null/undefined',
                    'severity': 'warning'
                })
    except Exception as e:
        logging.warning(f"Error en análisis estático: {str(e)}")
        # Continuar con el proceso incluso si el análisis estático falla

    return results


def build_detailed_instructions(base_instructions, language, auto_fix, optimize, 
                              improve_readability, follow_conventions, correction_level,
                              static_analysis=None):
    """
    Construye instrucciones detalladas para el modelo basadas en las opciones seleccionadas
    y los resultados del análisis estático.
    """
    instructions = [base_instructions]

    # Agregar instrucciones basadas en opciones
    if auto_fix:
        instructions.append("Corrige automáticamente errores de sintaxis y lógica.")

    if optimize:
        instructions.append("Optimiza el código para mejorar su rendimiento y eficiencia.")

    if improve_readability:
        instructions.append("Mejora la legibilidad con nombres de variables descriptivos, comentarios apropiados y estructura clara.")

    if follow_conventions:
        # Agregar convenciones específicas por lenguaje
        if language == 'python':
            instructions.append("Sigue estrictamente PEP 8 para estilo y convenciones de Python.")
        elif language == 'javascript':
            instructions.append("Sigue el estándar Airbnb JavaScript Style Guide.")
        elif language == 'java':
            instructions.append("Sigue las convenciones de código de Google para Java.")
        else:
            instructions.append(f"Sigue las mejores prácticas y convenciones estándar para {language}.")

    # Ajustar nivel de corrección
    if correction_level == 'minimal':
        instructions.append("Realiza solo las correcciones esenciales para que el código funcione correctamente.")
    elif correction_level == 'moderate':
        instructions.append("Equilibra las correcciones necesarias con mejoras de estilo y optimizaciones moderadas.")
    elif correction_level == 'aggressive':
        instructions.append("Realiza una refactorización completa si es necesario para optimizar y mejorar el código significativamente.")

    # Incorporar resultados del análisis estático
    if static_analysis and static_analysis.get('issues'):
        issues_text = "Problemas detectados en análisis estático que deben corregirse:\n"
        for issue in static_analysis['issues'][:10]:  # Limitar a 10 problemas para no sobrecargar
            issues_text += f"- Línea {issue['line']}: {issue['message']} ({issue['severity']})\n"
        instructions.append(issues_text)

    # Instrucciones específicas por lenguaje
    language_specific = get_language_specific_instructions(language)
    if language_specific:
        instructions.append(language_specific)

    # Instrucciones para formato de respuesta
    instructions.append("""Responde en formato JSON con las siguientes claves:
    - corrected_code: el código corregido completo
    - changes: una lista de objetos, cada uno con:
        - description: descripción del cambio
        - lineNumbers: números de línea afectados
        - category: categoría del cambio (sintaxis, optimización, estilo, seguridad, etc.)
        - importance: importancia del cambio (alta, media, baja)
    - explanation: explicación detallada de los cambios realizados
    - metrics: métricas del código (opcional)
    - recommendations: recomendaciones adicionales (opcional)
    """)

    return "\n\n".join(instructions)

def get_language_specific_instructions(language):
    """
    Proporciona instrucciones específicas según el lenguaje de programación.
    """
    instructions = {
        'python': """
            - Usa f-strings en lugar de .format() o % cuando sea posible
            - Prefiere list/dict comprehensions sobre bucles cuando sea apropiado
            - Usa pathlib en lugar de os.path para manejo de rutas
            - Implementa manejo de errores con bloques try/except específicos
            - Asegúrate de que el código sea compatible con Python 3.8+
        """,
        'javascript': """
            - Usa sintaxis ES6+ (const/let, arrow functions, destructuring, etc.)
            - Prefiere métodos de array funcionales (map, filter, reduce) sobre bucles for
            - Evita modificar objetos directamente, usa técnicas inmutables
            - Maneja promesas correctamente con async/await
            - Evita el uso de var y prefiere const siempre que sea posible
        """,
        'typescript': """
            - Usa tipos explícitos y evita 'any' cuando sea posible
            - Aprovecha interfaces y tipos para estructuras de datos
            - Usa enums para valores constantes relacionados
            - Implementa patrones de manejo de errores consistentes
            - Asegúrate de que las funciones tengan tipos de retorno explícitos
        """,
        'java': """
            - Sigue el principio de inmutabilidad cuando sea posible
            - Usa Stream API para operaciones de colecciones
            - Implementa manejo de excepciones adecuado
            - Usa Optional para valores que pueden ser nulos
            - Prefiere interfaces sobre clases concretas para variables
        """,
        'cpp': """
            - Usa características modernas de C++ (C++17/20)
            - Prefiere referencias y smart pointers sobre punteros crudos
            - Usa RAII para gestión de recursos
            - Implementa manejo de errores con excepciones o códigos de error consistentes
            - Optimiza para rendimiento cuando sea crítico
        """,
    }

    return instructions.get(language, "")


def process_with_openai(code, language, instructions, model="gpt-4o"):
    """
    Procesa el código usando OpenAI con manejo de errores mejorado y reintentos.
    """
    try:
        # Mapeo de nombres de modelos amigables a identificadores reales de API
        model_mapping = {
            'gpt4o': "gpt-4o",
            'gpt4-turbo': "gpt-4-turbo",
            'gpt4': "gpt-4-turbo",  # Fallback a turbo si solo se especifica gpt4
        }

        api_model = model_mapping.get(model, model)  # Usar el modelo mapeado o el original si no está en el mapeo

        client = openai.OpenAI()

        # Sistema de reintentos con backoff exponencial
        max_retries = 3
        retry_delay = 2  # segundos

        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model=api_model,
                    messages=[{
                        "role": "system", 
                        "content": f"Eres un experto programador especializado en {language}. Tu tarea es corregir y mejorar código siguiendo las mejores prácticas y estándares actuales."
                    },
                    {
                        "role": "user", 
                        "content": f"Aquí está el código en {language} que necesito corregir:\n\n```{language}\n{code}\n```\n\nInstrucciones:\n{instructions}"
                    }],
                    response_format={"type": "json_object"},
                    temperature=0.2,  # Temperatura más baja para respuestas más precisas
                )

                result = json.loads(completion.choices[0].message.content)

                # Verificar que la respuesta tenga la estructura esperada
                if 'corrected_code' not in result:
                    if 'correctedCode' in result:  # Manejar posible variación en nombres de campos
                        result['corrected_code'] = result.pop('correctedCode')
                    else:
                        raise ValueError("La respuesta del modelo no incluye el código corregido")

                # Normalizar nombres de campos si es necesario
                if 'changes' not in result and 'changes_made' in result:
                    result['changes'] = result.pop('changes_made')

                logging.info(f"Código procesado exitosamente con {api_model}")

                # Agregar metadatos
                result['model_used'] = api_model
                result['success'] = True

                return result

            except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Error temporal con OpenAI (intento {attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (2 ** attempt))  # Backoff exponencial
                else:
                    logging.error(f"Error persistente con OpenAI después de {max_retries} intentos: {str(e)}")
                    return {
                        'success': False,
                        'error': f'Error al conectar con OpenAI después de {max_retries} intentos: {str(e)}'
                    }
            except Exception as e:
                logging.error(f"Error inesperado con OpenAI: {str(e)}")
                return {
                    'success': False,
                    'error': f'Error al procesar con OpenAI: {str(e)}'
                }

    except Exception as e:
        logging.exception(f"Error general al procesar con OpenAI: {str(e)}")
        return {
            'success': False,
            'error': f'Error al configurar OpenAI: {str(e)}'
        }


def process_with_anthropic(code, language, instructions, model="claude-3-5-sonnet"):
    """
    Procesa el código usando Anthropic Claude con manejo de errores mejorado.
    """
    try:
        # Mapeo de nombres de modelos amigables a identificadores reales de API
        model_mapping = {
            'claude-3-5-sonnet': "claude-3-5-sonnet-20240620",
            'claude-3-5-opus': "claude-3-5-opus-20240620",
            'claude-3-7-sonnet': "claude-3-7-sonnet-20240307",
        }

        api_model = model_mapping.get(model, model)

        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

        # Mensaje del sistema más detallado para mejor control
        system_message = f"""
        Eres un experto programador especializado en {language}. Tu tarea es corregir y mejorar código siguiendo
        las mejores prácticas y estándares actuales. Responde SIEMPRE en formato JSON válido con los campos solicitados.

        Debes analizar el código a fondo, identificar problemas y aplicar mejoras según las instrucciones.
        Asegúrate de que tu respuesta incluya estos campos:
        - corrected_code: el código corregido completo
        - changes: lista de cambios con description, lineNumbers, category e importance
        - explanation: explicación detallada de los cambios
        """

        # Crear prompt con formato específico para mejorar la respuesta
        prompt = f"""Analiza y mejora el siguiente código en {language}: 

```{language}
{code}
INSTRUCCIONES:
{instructions}

Tu respuesta debe ser un objeto JSON válido con exactamente esta estructura:
```json
{{
  "corrected_code": "código corregido completo aquí",
  "changes": [
    {{
      "description": "descripción del cambio",
      "lineNumbers": [1, 2],
      "category": "categoría del cambio",
      "importance": "alta|media|baja"
    }}
  ],
  "explanation": "explicación detallada de los cambios",
  "metrics": {{
    "loc": 10,
    "complexity": 5,
    "errors_fixed": 3,
    "warnings_fixed": 2,
    "performance_improvements": 1,
    "readability_improvements": 4,
    "quality_scores": {{
      "mantenibilidad": {{"before": 5, "after": 8}},
      "legibilidad": {{"before": 4, "after": 7}},
      "eficiencia": {{"before": 6, "after": 8}},
      "robustez": {{"before": 3, "after": 7}},
      "seguridad": {{"before": 5, "after": 6}}
    }}
  }},
  "recommendations": [
    {{
      "title": "título de la recomendación",
      "description": "descripción detallada"
    }}
  ]
}}
```"""

        # Realizar la llamada a la API con reintentos
        max_retries = 2
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=api_model,
                    max_tokens=4000,
                    system=system_message,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )

                # Extraer JSON de la respuesta
                content = response.content[0].text

                # Buscar JSON en formato de bloque de código primero
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError:
                        # Intentar limpiar el JSON antes de fallar
                        cleaned_json = clean_json_string(json_match.group(1).strip())
                        result = json.loads(cleaned_json)
                else:
                    # Intentar extraer cualquier objeto JSON de la respuesta completa
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        cleaned_json = clean_json_string(json_match.group(1))
                        result = json.loads(cleaned_json)
                    else:
                        raise ValueError("No se pudo extraer JSON de la respuesta")

                # Normalizar nombres de campos si es necesario
                if 'correctedCode' in result and 'corrected_code' not in result:
                    result['corrected_code'] = result.pop('correctedCode')

                logging.info(f"Código procesado exitosamente con {api_model}")

                # Agregar metadatos
                result['model_used'] = api_model
                result['success'] = True

                return result

            except (anthropic.APIError, anthropic.APIConnectionError, anthropic.RateLimitError) as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Error temporal con Anthropic (intento {attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (2 ** attempt))  # Backoff exponencial
                else:
                    logging.error(f"Error persistente con Anthropic después de {max_retries} intentos: {str(e)}")
                    return {
                        'success': False,
                        'error': f'Error al conectar con Anthropic después de {max_retries} intentos: {str(e)}'
                    }
            except Exception as e:
                logging.error(f"Error inesperado con Anthropic: {str(e)}")
                return {
                    'success': False,
                    'error': f'Error al procesar con Anthropic: {str(e)}'
                }

    except Exception as e:
        logging.exception(f"Error general al procesar con Anthropic: {str(e)}")
        return {
            'success': False,
            'error': f'Error al configurar Anthropic: {str(e)}'
        }


def process_with_gemini(code, language, instructions, model="gemini-1-5-pro"):
    """
    Procesa el código usando Google Gemini con manejo de errores mejorado.
    """
    try:
        # Configurar la API si no está configurada
        if not hasattr(genai, '_configured') or not genai._configured:
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

        # Mapeo de nombres de modelos amigables a identificadores reales de API
        model_mapping = {
            'gemini-1-5-pro': "gemini-1.5-pro",
            'gemini-1-5-flash': "gemini-1.5-flash",
            'gemini-1-5-ultra': "gemini-1.5-ultra",
        }

        api_model = model_mapping.get(model, model)

        gemini_model = genai.GenerativeModel(
            model_name=api_model,
            generation_config={
                'temperature': 0.2,
                'top_p': 0.9,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )

        prompt = f"""Eres un experto programador especializado en {language}. Tu tarea es corregir y mejorar el siguiente código:

```{language}
{code}
INSTRUCCIONES:
{instructions}

Responde ÚNICAMENTE con un objeto JSON válido con exactamente esta estructura:

json
Copiar
{{
  "corrected_code": "código corregido completo aquí",
  "changes": [
    {{
      "description": "descripción del cambio",
      "lineNumbers": [1, 2],
      "category": "categoría del cambio",
      "importance": "alta|media|baja"
    }}
  ],
  "explanation": "explicación detallada de los cambios",
  "metrics": {{
    "loc": 10,
    "complexity": 5,
    "errors_fixed": 3,
    "warnings_fixed": 2,
    "performance_improvements": 1,
    "readability_improvements": 4,
    "quality_scores": {{
      "mantenibilidad": {{"before": 5, "after": 8}},
      "legibilidad": {{"before": 4, "after": 7}},
      "eficiencia": {{"before": 6, "after": 8}},
      "robustez": {{"before": 3, "after": 7}},
      "seguridad": {{"before": 5, "after": 6}}
    }}
  }},
  "recommendations": [
    {{
      "title": "título de la recomendación",
      "description": "descripción detallada"
    }}
  ]
}}
No incluyas ningún texto adicional fuera del objeto JSON.
"""
        # Realizar la llamada a la API con reintentos
        max_retries = 2
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content(prompt)

                # Extraer JSON de la respuesta
                content = response.text

                # Buscar JSON en formato de bloque de código primero
                json_match = re.search(r'json\s*(.*?)\s*