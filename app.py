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

# Configurar APIs de IA correctamente
try:
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key:
        # Configurar globalmente la API key de OpenAI
        openai.api_key = openai_api_key
        # Solo mostrar los primeros caracteres por seguridad
        masked_key = openai_api_key[:5] + "..." + openai_api_key[-5:]
        logging.info(f"OpenAI API key configurada: {masked_key}")
    else:
        logging.warning("OPENAI_API_KEY no encontrada en variables de entorno.")
except Exception as e:
    logging.error(f"Error al configurar OpenAI API: {str(e)}")

try:
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        logging.info("Anthropic API key configured successfully.")
    else:
        logging.warning("ANTHROPIC_API_KEY no encontrada en variables de entorno.")
except Exception as e:
    logging.error(f"Error al configurar Anthropic API: {str(e)}")

try:
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        logging.info("Gemini API key configured successfully.")
    else:
        logging.warning("GEMINI_API_KEY no encontrada en variables de entorno.")
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

        # Asegurar extensión
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
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto en desarrollo de software especializado en crear archivos de alta calidad."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                file_content = completion.choices[0].message.content.strip()
            except Exception as e:
                logging.error(f"Error en OpenAI al generar archivo: {str(e)}")
                raise Exception(f"Error con OpenAI API: {str(e)}")

        # Eliminar marcadores de código markdown
        if file_content.startswith("```"):
            match = re.match(r"```(?:\w+)?\s*([\s\S]+?)\s*```", file_content)
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
                    if result.get('stdout'):
                        response_message += f"**Salida del comando:**\n```\n{result['stdout']}\n```\n\n"

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
                    full_prompt += prefix + msg['content'] +{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"}
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

                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=4000,
                    system=f"Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas. Devuelve el código corregido, una lista de cambios realizados y una explicación clara en formato JSON.",
                    messages=[
                        {"role": "user", "content": f"CÓDIGO:\n```{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"}
                    ],
                    temperature=0.1
                )

                # Extraer el JSON de la respuesta de Claude
                import re
                json_match = re.search(r'```json(.*?)```', response.content[0].text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1).strip())
                else:
                    result = json.loads(response.content[0].text)

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
                json_match = re.search(r'```json(.*?)```', response.text, re.DOTALL)
                if json_match:
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
        if not result or 'correctedCode' not in result:
            return jsonify({
                'success': False,
                'error': 'La respuesta del modelo no incluye el código corregido'
            }), 500

        # Devolver resultado en formato esperado por el frontend
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

@app.route('/api/process_code_old', methods=['POST'])
def process_code_old():
    """Process code for corrections and improvements using older method."""
    try:
        data = request.json
        code = data.get('code', '')
        instructions = data.get('instructions', 'Corrige errores y mejora la calidad del código')
        language = data.get('language', 'python')

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        prompt = f"""Corrige y mejora el siguiente código {language} para que funcione correctamente y tenga mejores prácticas.  El código debe estar optimizado y con comentarios útiles para explicar el código corregido.

        Instrucciones de corrección y mejoras:
        {instructions}

        Código original:
        ```
        {code}
        ```

        Por favor, proporciona:
        1. El código corregido y completo
        2. Un resumen de los cambios realizados (máximo 5 puntos)
        3. Una explicación detallada de las correcciones y mejoras

        Formato de respuesta:
        {{
            "corrected_code": "código corregido aquí",
            "summary": ["punto 1", "punto 2", ...],
            "explanation": "explicación detallada aquí"
        }}
        """

        # Utilizar el modelo seleccionado
        response = {}
        model_choice = data.get('model', 'openai')

        if model_choice == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            # Usar Anthropic Claude
            client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
            completion = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=4000,
                temperature=0.2,
                system="Eres un experto en programación y tu tarea es corregir y mejorar código. Responde siempre en JSON.",
                messages=[{"role": "user", "content": prompt}]
            )
            try:
                response = json.loads(completion.content[0].text)
            except (json.JSONDecodeError, IndexError):
                # Si no podemos analizar JSON, devolver el texto completo
                response = {
                    "corrected_code": code,  # Mantener el código original
                    "summary": ["No se pudieron procesar las correcciones"],
                    "explanation": completion.content[0].text if completion.content else "No se pudo generar explicación"
                }

        elif model_choice == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            # Usar Google Gemini
            if not hasattr(genai, '_configured') or not genai._configured:
                genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-pro')
            gemini_response = model.generate_content(prompt)

            try:
                response = json.loads(gemini_response.text)
            except json.JSONDecodeError:
                # Intentar extraer JSON si está en un formato no estándar
                response = {
                    "corrected_code": code,  # Mantener el código original
                    "summary": ["No se pudieron procesar las correcciones"],
                    "explanation": gemini_response.text
                }

        else:
            # Usar OpenAI como valor predeterminado
            client = openai.OpenAI()  # Usa la API key configurada globalmente
            completion = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "Eres un experto en programación y tu tarea es corregir y mejorar código. Responde siempre en JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            try:
                response = json.loads(completion.choices[0].message.content)
            except json.JSONDecodeError:
                response = {
                    "corrected_code": code,  # Mantener el código original
                    "summary": ["No se pudieron procesar las correcciones"],
                    "explanation": completion.choices[0].message.content
                }

        # Asegurar que todos los campos necesarios estén presentes
        if 'corrected_code' not in response:
            response['corrected_code'] = code
        if 'summary' not in response:
            response['summary'] = ["No se generó resumen de cambios"]
        if 'explanation' not in response:
            response['explanation'] = "No se generó explicación detallada"

        return jsonify(response)

    except Exception as e:
        logging.error(f"Error processing code: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

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
            # Ampliamos la lista de comandos locales para evitar llamadas a la API
            user_input_lower = user_input.lower()

            # Mapa de comandos comunes para respuesta inmediata
            command_map = {
                "listar": "ls -la",
                "mostrar archivos": "ls -la",
                "mostrar directorio": "ls -la",
                "ver archivos": "ls -la",
                "archivos": "ls -la",
                "dir": "ls -la",
                "hola": "echo '¡Hola! ¿En qué puedo ayudarte hoy?'",
                "saludar": "echo '¡Hola! ¿En qué puedo ayudarte hoy?'",
                "fecha": "date",
                "hora": "date +%H:%M:%S",
                "calendario": "cal",
                "ayuda": "echo 'Puedo convertir tus instrucciones en comandos de terminal. Prueba pidiendo crear archivos, listar directorios, etc.'",
                "quien soy": "whoami",
                "donde estoy": "pwd",
                "limpiar": "clear",
                "sistema": "uname -a",
                "memoria": "free -h",
                "espacio": "df -h",
                "procesos": "ps aux"
            }

            # Búsqueda exacta primero (más rápida)
            for key, cmd in command_map.items():
                if key in user_input_lower:
                    terminal_command = cmd
                    break

            # Patrones específicos si no hubo coincidencia exacta
            if not terminal_command:
                if "crear" in user_input_lower and "carpeta" in user_input_lower:
                    folder_name = user_input_lower.split("carpeta")[-1].strip()
                    terminal_command = f"mkdir -p {folder_name}"
                elif "crear" in user_input_lower and "archivo" in user_input_lower:
                    parts = user_input_lower.split("archivo")
                    if len(parts) > 1:
                        file_name = parts[-1].strip()
                        terminal_command = f"touch {file_name}"
                    else:
                        terminal_command = "touch nuevo_archivo.txt"
                elif "mostrar" in user_input_lower and ("contenido" in user_input_lower or "cat" in user_input_lower):
                    parts = user_input_lower.replace("mostrar", "").replace("contenido", "").replace("del", "").replace("de", "").strip()
                    terminal_command = f"cat {parts}"
                elif "eliminar" in user_input_lower or "borrar" in user_input_lower:
                    words = user_input_lower.split()
                    target_idx = -1
                    for i, word in enumerate(words):
                        if word in ["archivo", "carpeta", "directorio", "fichero"]:
                            target_idx = i + 1
                            break
                    if target_idx >= 0 and target_idx < len(words):
                        target = words[target_idx]
                        terminal_command = f"rm -rf {target}"
                    else:
                        terminal_command = "echo 'Por favor especifica qué quieres eliminar'"

            # Solo llamamos a la API si no se encontró un comando local
            if not terminal_command:
                try:
                    client = openai.OpenAI()  # Usa la API key configurada globalmente

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Convierte instrucciones a comandos de terminal Linux. Responde solo con el comando exacto, sin comillas ni texto adicional."},
                            {"role": "user", "content": user_input}
                        ],
                        max_tokens=60,
                        temperature=0.1
                    )

                    terminal_command = response.choices[0].message.content.strip()
                    # Limpiamos los bloques de código que a veces devuelve
                    terminal_command = terminal_command.replace("```bash", "").replace("```", "").strip()
                except Exception as e:
                    logging.warning(f"OpenAI failed, using fallback: {str(e)}")
                    # Fallback más inteligente basado en palabras clave
                    if "listar" in user_input_lower or "mostrar" in user_input_lower:
                        terminal_command = "ls -la"
                    else:
                        terminal_command = "echo 'No se pudo procesar la instrucción'"

        elif model_choice == 'anthropic':
            try:
                client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

                # Use Anthropic to generate terminal command
                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=100,
                    messages=[
                        {"role": "user", "content": f"Convert this instruction to a terminal command without any explanation: {user_input}"}
                    ],
                    system="You are a helpful assistant that converts natural language instructions into terminal commands. Only output the exact command without explanations."
                )

                terminal_command = response.content[0].text.strip()
            except Exception as e:
                logging.error(f"Anthropic API error: {str(e)}")
                terminal_command = "echo 'Error connecting to Anthropic API'"

        elif model_choice == 'gemini':
            # Implementación básica de Gemini con manejo de errores mejorado
            try:
                gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
                if not gemini_api_key:
                    # Fallback para cuando no hay API key configurada
                    logging.warning("Gemini API key not configured, using fallback logic")
                    if "crear" in user_input.lower() and "carpeta" in user_input.lower():
                        folder_name = user_input.lower().split("carpeta")[-1].strip()
                        terminal_command = f"mkdir -p {folder_name}"
                    else:
                        terminal_command = "echo 'Gemini API key not configured'"
                    return jsonify({'command': terminal_command})

                try:
                    # Ensure Gemini is configured
                    if not hasattr(genai, '_configured') or not genai._configured:
                        genai.configure(api_key=gemini_api_key)

                    model = genai.GenerativeModel('gemini-1.5-pro')

                    response = model.generate_content(
                        f"Convert this instruction to a terminal command without any explanation: {user_input}"
                    )
                    terminal_command = response.text.strip()
                except Exception as api_error:
                    logging.error(f"Gemini API error: {str(api_error)}")
                    # Fallback si hay error con la API
                    if "crear" in user_input.lower() and "carpeta" in user_input.lower():
                        folder_name = user_input.lower().split("carpeta")[-1].strip()
                        terminal_command = f"mkdir -p {folder_name}"
                    else:
                        terminal_command = "echo 'Error connecting to Gemini API'"

            except Exception as e:
                logging.error(f"Error using Gemini API: {str(e)}")
                # En lugar de devolver error 500, usamos lógica de respaldo
                if "crear" in user_input.lower() and "carpeta" in user_input.lower():
                    folder_name = user_input.lower().split("carpeta")[-1].strip()
                    terminal_command = f"mkdir -p {folder_name}"
                else:
                    terminal_command = "echo 'Error with Gemini API'"
        else:
            return jsonify({'error': 'Invalid model selection'}), 400

        logging.debug(f"Generated command using {model_choice}: {terminal_command}")

        return jsonify({'command': terminal_command})
    except Exception as e:
        logging.error(f"Error processing instructions: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview():
    """Render the preview page."""
    return render_template('preview.html')

@app.route('/terminal')
def terminal():
    """Render the terminal page."""
    return render_template('terminal.html')

@app.route('/api/preview', methods=['POST'])
def generate_preview():
    """Generate a preview of HTML content."""
    try:
        data = request.json
        html_content = data.get('html', '')

        if not html_content:
            return jsonify({'error': 'No HTML content provided'}), 400

        # TODO: Mejorar esta función para validar y sanitizar el HTML

        # Devolver el HTML para previsualización
        return jsonify({
            'success': True,
            'html': html_content
        })
    except Exception as e:
        logging.error(f"Error generating preview: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_command', methods=['POST'])
def execute_command():
    """Execute a terminal command and return the output."""
    try:
        data = request.json
        command = data.get('command', '')
        model_used = data.get('model', 'openai')
        instruction = data.get('instruction', '')

        if not command:
            return jsonify({'error': 'No command provided'}), 400

        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)

        # Execute the command in the user's workspace
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(workspace_path),  # Set working directory to user workspace
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # Store command in database - but with error handling
        try:
            # Verificar si existe el usuario por defecto, crearlo si no existe
            from models import User, Command

            # Verificar si existe el usuario por defecto
            default_user = db.session.query(User).filter_by(username="default_user").first()

            # Si no existe, crear un usuario por defecto
            if not default_user:
                default_user = User(
                    username="default_user",
                    email="default@example.com"
                )
                default_user.set_password("defaultpassword")
                db.session.add(default_user)
                db.session.commit()
                logging.info("Created default user")

            # Create command history entry
            cmd = Command(
                instruction=instruction,
                generated_command=command,
                output=stdout + ("\n" + stderr if stderr else ""),
                status=process.returncode,
                model_used=model_used,
                user_id=default_user.id
            )
            db.session.add(cmd)
            db.session.commit()
        except Exception as e:
            logging.error(f"Error storing command in database: {str(e)}")
            # Seguimos ejecutando aunque falle el guardado en base de datos

        result = {
            'stdout': stdout,
            'stderr': stderr,
            'exitCode': process.returncode,
            'workspace': str(workspace_path.relative_to(WORKSPACE_ROOT.parent))
        }

        logging.debug(f"Command execution result: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Procesa mensajes del chat usando el agente especializado seleccionado."""
    try:
        logging.info("Solicitud recibida en /api/chat")
        data = request.json
        logging.debug(f"Datos recibidos: {json.dumps(data)}")

        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'default')

        if not user_message:
            logging.warning("Solicitud sin mensaje")
            return jsonify({'error': 'No message provided', 'response': 'Error: No se proporcionó un mensaje.'}), 400

        logging.info(f"Procesando mensaje de chat: '{user_message[:30]}...' usando agente {agent_id}")

        # Usar la función interna para procesar la solicitud
        result = handle_chat_internal(data)

        # Verificar si hay un error
        if 'error' in result:
            logging.error(f"Error al procesar mensaje de chat: {result['error']}")
            return jsonify(result), 500

        # Registrar respuesta exitosa
        logging.info(f"Respuesta generada exitosamente: '{result['response'][:30]}...'")

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error general en handle_chat: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'response': f"Ocurrió un error inesperado: {str(e)}. Por favor, intenta de nuevo o contacta al administrador."
        }), 500

@app.route('/api/generate_complex_file', methods=['POST'])
def generate_complex_file():
    """Genera un archivo con contenido complejo basado en una descripción."""
    try:
        data = request.json
        description = data.get('description', '')
        file_type = data.get('file_type', 'html')
        filename = data.get('filename', '')

        if not description:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó una descripción para el archivo'
            }), 400

        # Usar la función interna para generar el archivo
        result = generate_complex_file_internal(description, file_type, filename)

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error generating complex file: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check the health status of the application."""
    try:
        # Check database connection
        db_status = "ok"
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            db_status = f"error: {str(e)}"
            logging.error(f"Database error: {str(e)}")

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
            "database": db_status,
            "apis": apis
        })
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Endpoint simplificado para la verificación del servidor
@app.route('/health', methods=['GET'])
def simple_health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/api/generate', methods=['POST'])
def generate():
    """Fallback endpoint for content generation."""
    try:
        data = request.json
        message = data.get('message', '')
        model_choice = data.get('model', 'openai')

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        # Default to OpenAI if no other model is available
        try:
            client = openai.OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4o",
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

# Socket.IO setup
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25, logger=True, engineio_logger=True)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Manejar conexión de cliente Socket.IO."""
    logging.info(f"Cliente Socket.IO conectado: {request.sid}")
    emit('server_info', {'status': 'connected', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Manejar desconexión de cliente Socket.IO."""
    logging.info(f"Cliente Socket.IO desconectado: {request.sid}")

@socketio.on('user_message')
def handle_user_message(data):
    """Manejar mensajes del usuario a través de Socket.IO."""
    try:
        logging.info(f"Mensaje recibido vía Socket.IO: {data}")
        user_message = data.get('message', '')
        agent_id = data.get('agent', 'architect')
        model = data.get('model', 'gemini')
        document = data.get('document', '')

        if not user_message:
            emit('error', {'message': 'Mensaje vacío'})
            return

        logging.info(f"Procesando mensaje Socket.IO: '{user_message[:30]}...' usando agente {agent_id} y modelo {model}")

        # Preparar datos para procesamiento
        request_data = {
            'message': user_message,
            'agent_id': agent_id,
            'model': model,
            'context': data.get('context', [])
        }

        # Procesar el mensaje usando la lógica existente
        result = handle_chat_internal(request_data)

        # Enviar respuesta al cliente
        logging.info(f"Enviando respuesta Socket.IO: '{result.get('response', '')[:30]}...'")
        emit('agent_response', {
            'response': result.get('response', ''),
            'agent': agent_id,
            'model': model,
            'error': result.get('error', None)
        })

    except Exception as e:
        logging.error(f"Error en Socket.IO user_message: {str(e)}")
        logging.error(traceback.format_exc())
        emit('error', {'message': str(e)})

# Función para notificar cambios de archivos
def notify_file_change(workspace_id, change_type, file_data):
    """Send real-time notification about file changes."""
    try:
        socketio.emit('file_change', {
            'type': change_type,  # 'create', 'update', 'delete'
            'workspace': workspace_id,
            'file': file_data
        })
        logging.debug(f"Notificación de cambio de archivo enviada: {change_type} {file_data['path']}")
    except Exception as e:
        logging.error(f"Error al notificar cambio de archivo: {str(e)}")

# Función para servir archivos estáticos
@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

# Start server when running directly
if __name__ == '__main__':
    try:
        logging.info("Iniciando servidor CODESTORM Assistant...")

        # Comprobar claves de API
        if not openai_api_key:
            logging.warning("OPENAI_API_KEY no configurada - funcionalidades de OpenAI estarán deshabilitadas")
        if not anthropic_api_key:
            logging.warning("ANTHROPIC_API_KEY no configurada - funcionalidades de Anthropic estarán deshabilitadas")
        if not gemini_api_key:
            logging.warning("GEMINI_API_KEY no configurada - funcionalidades de Gemini estarán deshabilitadas")

        # Comprobar si al menos una API está configurada
        if not any([openai_api_key, anthropic_api_key, gemini_api_key]):
            logging.error("¡ADVERTENCIA! Ninguna API está configurada. El sistema funcionará en modo degradado.")

        import threading
        # Start file watcher in a background thread
        file_watcher_thread = threading.Thread(target=watch_workspace_files, daemon=True)
        file_watcher_thread.start()

        logging.info("Servidor listo para recibir conexiones")

        # Start the SocketIO server
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.critical(f"Error fatal al iniciar el servidor: {str(e)}")
        logging.critical(traceback.format_exc())

# La función terminal ya está definida anteriormente en el archivo