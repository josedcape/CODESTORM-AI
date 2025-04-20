# Flask application for Codestorm-Assistant
import os
import json
import logging
import subprocess
import shutil
import time
import re
from pathlib import Path
from threading import Thread
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import openai
import anthropic
from anthropic import Anthropic
import eventlet
import google.generativeai as genai

# Comentamos el monkey patch para evitar conflictos con gunicorn
# eventlet.monkey_patch(os=True, select=True, socket=True, thread=False, time=True)

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging - reducir nivel para mejor rendimiento
logging.basicConfig(level=logging.INFO)

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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
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
    import models
    db.create_all()

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
        # Usar el token directamente en vez de a través del cliente
        openai.api_key = openai_api_key 
        openai_client = openai.OpenAI(api_key=openai_api_key)
        # Skip validation for now to avoid errors
        # Simply log that we attempted to configure
        logging.info(f"OpenAI API key configurada: {openai_api_key[:5]}...{openai_api_key[-5:]}")
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
        logging.info("Anthropic API key configured successfully.")
    except Exception as e:
        logging.error(f"Error initializing Anthropic client: {str(e)}")
        anthropic_client = None
else:
    logging.warning("ANTHROPIC_API_KEY not found. Anthropic features will not work.")

# This is defined above, removing duplicate definition
# WORKSPACE_ROOT is already defined and created above

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

@app.route('/')
def index():
    """Render the main page."""
    try:
        # Respuesta HTML directa para pruebas
        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CODESTORM - Asistente de Desarrollo</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2a4b8d; }
                .btn { display: inline-block; padding: 10px 15px; background: #3a6ea5; color: white; 
                     text-decoration: none; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>CODESTORM - Asistente de Desarrollo</h1>
            <p>Sistema de asistente inteligente para desarrollo con procesamiento de lenguaje natural</p>
            <a href="/chat" class="btn">Ir al Chat</a>
        </body>
        </html>
        """
        return html
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}")
        return str(e), 500
    
@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')
    
@app.route('/files')
def files():
    """File explorer view."""
    return render_template('files.html')
    
@app.route('/edit/<path:file_path>')
def edit_file(file_path):
    """Edit a file."""
    try:
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Determine the target file
        # Make sure we don't escape the workspace
        file_path = file_path.replace('..', '')  # Basic path traversal protection
        target_file = (workspace_path / file_path).resolve()
        
        if not str(target_file).startswith(str(workspace_path.resolve())):
            return jsonify({'error': 'Access denied: Cannot access files outside workspace'}), 403
            
        if not target_file.exists():
            return jsonify({'error': 'File not found'}), 404
            
        if target_file.is_dir():
            return jsonify({'error': 'Cannot edit a directory'}), 400
            
        # Read file content
        with open(target_file, 'r') as f:
            content = f.read()
            
        # Determine file type for syntax highlighting
        file_type = get_file_type(target_file.name)
        file_size = target_file.stat().st_size
            
        return render_template('editor.html', 
                             file_path=file_path,
                             file_name=target_file.name,
                             file_content=content,
                             file_type=file_type,
                             file_size=file_size)
    except Exception as e:
        logging.error(f"Error editing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/code_corrector')
def code_corrector():
    """Render the code corrector page."""
    return render_template('code_corrector.html')
    
@app.route('/api/process_code', methods=['POST'])
def process_code():
    """Process code for corrections and improvements."""
    try:
        data = request.json
        code = data.get('code', '')
        file_path = data.get('file_path', '')
        instructions = data.get('instructions', 'Corrige errores y mejora la calidad del código')
        
        if not code:
            return jsonify({'error': 'No se proporcionó código para procesar'}), 400
            
        # Detectar el lenguaje por la extensión del archivo
        language = 'unknown'
        if file_path:
            ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            if ext in ['py', 'pyw']:
                language = 'python'
            elif ext in ['js', 'ts', 'jsx', 'tsx']:
                language = 'javascript'
            elif ext in ['html', 'htm']:
                language = 'html'
            elif ext in ['css', 'scss', 'sass']:
                language = 'css'
            elif ext in ['json']:
                language = 'json'
        
        # Preparar el prompt para el modelo
        prompt = f"""Eres un experto corrector de código en {language}. 
        
        Analiza el siguiente código y realiza correcciones y mejoras siguiendo estas instrucciones:
        {instructions}
        
        Código original:
        ```
        {code}
        ```
        
        Por favor, proporciona:
        1. El código corregido
        2. Un resumen de los cambios realizados (máximo 5 puntos)
        3. Una explicación detallada de las correcciones y mejoras

        Formato de respuesta:
        {{"corrected_code": "código corregido aquí", 
          "summary": ["punto 1", "punto 2", ...], 
          "explanation": "explicación detallada aquí"}}
        """
        
        # Utilizar el modelo seleccionado predeterminado (OpenAI)
        response = {}
        model_choice = data.get('model', 'openai')

        if model_choice == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            # Usar Anthropic Claude
            client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
            completion = client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
            openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            completion = openai_client.chat.completions.create(
                model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
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
        
        # Use selected model to generate command - Versión optimizada para velocidad
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
                    if not openai_client:
                        raise Exception("OpenAI API key not configured")
                    
                    # Optimización: Usamos gpt-4o con menos tokens para respuesta más rápida
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
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
            # Implementación básica de Gemini con manejo de errores mejorado
            try:
                import google.generativeai as genai
                
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
                    genai.configure(api_key=gemini_api_key)
                    # Actualizado para usar gemini-1.5-pro que está disponible
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
                
                # Si el modelo devuelve una respuesta vacía, intentamos con un comando simple
                if not terminal_command:
                    logging.warning("Gemini returned empty response, using fallback logic")
                    
                    # Lógica simple para comandos básicos
                    if "crear" in user_input.lower() and "carpeta" in user_input.lower():
                        folder_name = user_input.lower().split("carpeta")[-1].strip()
                        terminal_command = f"mkdir -p {folder_name}"
                    else:
                        terminal_command = "echo 'No se pudo generar un comando'"
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
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview():
    """Render the preview page."""
    return render_template('preview.html')

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
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Procesa mensajes del chat usando el agente especializado seleccionado."""
    try:
        data = request.json
        message = data.get('message', '')
        agent_prompt = data.get('agent_prompt', '')
        model_choice = data.get('model', 'openai')  # Default to OpenAI
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        response = ""
        
        # Generar respuesta según el modelo seleccionado
        if model_choice == 'openai':
            if not openai_client:
                return jsonify({'error': 'OpenAI API key not configured'}), 500
                
            try:
                openai_response = openai_client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=1500
                )
                response = openai_response.choices[0].message.content
            except Exception as e:
                logging.error(f"OpenAI API error: {str(e)}")
                return jsonify({'error': f"Error with OpenAI API: {str(e)}"}), 500
                
        elif model_choice == 'anthropic':
            if not anthropic_client:
                return jsonify({'error': 'Anthropic API key not configured'}), 500
                
            try:
                anthropic_response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                    system=agent_prompt,
                    messages=[
                        {"role": "user", "content": message}
                    ],
                    max_tokens=1500
                )
                response = anthropic_response.content[0].text
            except Exception as e:
                logging.error(f"Anthropic API error: {str(e)}")
                return jsonify({'error': f"Error with Anthropic API: {str(e)}"}), 500
                
        elif model_choice == 'gemini':
            if not gemini_api_key:
                return jsonify({'error': 'Gemini API key not configured'}), 500
                
            try:
                model = genai.GenerativeModel('gemini-pro')
                chat = model.start_chat(
                    history=[
                        {"role": "user", "parts": [agent_prompt]}
                    ]
                )
                gemini_response = chat.send_message(message)
                response = gemini_response.text
            except Exception as e:
                logging.error(f"Gemini API error: {str(e)}")
                return jsonify({'error': f"Error with Gemini API: {str(e)}"}), 500
        else:
            return jsonify({'error': 'Invalid model choice'}), 400
            
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        logging.error(f"Error processing chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_files', methods=['POST'])
def list_files():
    """List files in the specified directory."""
    try:
        data = request.json
        relative_directory = data.get('directory', '.')
        
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Ensure workspace exists
        if not workspace_path.exists():
            workspace_path.mkdir(parents=True, exist_ok=True)
            # Create a README file in the workspace
            with open(workspace_path / "README.md", "w") as f:
                f.write("# Workspace\n\nEste es tu espacio de trabajo. Usa los comandos para crear y modificar archivos aquí.")
        
        # Determine the target directory
        if relative_directory == '.' or relative_directory == '/':
            target_dir = workspace_path
        else:
            # Clean up any leading slashes
            if relative_directory.startswith('/'):
                relative_directory = relative_directory[1:]
                
            # Make sure we don't escape the workspace
            try:
                # Try to safely resolve the path relative to the workspace
                target_dir = (workspace_path / relative_directory)
                # Safety check - ensure we're still in workspace
                if not os.path.commonpath([target_dir.resolve()]).startswith(os.path.commonpath([workspace_path.resolve()])):
                    logging.warning(f"Access attempt outside workspace: {target_dir}")
                    target_dir = workspace_path
            except Exception as e:
                logging.error(f"Error resolving path: {str(e)}")
                target_dir = workspace_path
        
        # List files using Path
        files = []
        
        try:
            # Add parent directory entry if not in root workspace
            if target_dir != workspace_path:
                files.append({
                    'name': '..',
                    'type': 'directory',
                    'permissions': 'drwxr-xr-x',
                    'size': '0',
                    'modified': ''
                })
            
            # List all files and directories in the target directory
            for item in target_dir.iterdir():
                try:
                    stat = item.stat()
                    file_type = 'directory' if item.is_dir() else 'file'
                    permissions = 'drwxr-xr-x' if file_type == 'directory' else '-rw-r--r--'
                    
                    # Skip hidden files
                    if item.name.startswith('.') and item.name not in ['.', '..']:
                        continue
                        
                    files.append({
                        'name': item.name,
                        'type': file_type,
                        'permissions': permissions,
                        'size': str(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    logging.warning(f"Error accessing file {item}: {str(e)}")
                    
            # Sort files - directories first, then alphabetically
            files.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name']))
            
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
        except FileNotFoundError:
            return jsonify({'error': 'Directory not found'}), 404
        
        # Return the relative path for display in UI
        display_path = os.path.relpath(target_dir, workspace_path)
        if display_path == '.':
            display_path = '/'
        
        return jsonify({
            'files': files,
            'current_dir': display_path
        })
    except Exception as e:
        logging.error(f"Error listing files: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/create_file', methods=['POST'])
def create_file():
    """Create a new file in the workspace."""
    try:
        data = request.json
        file_path = data.get('file_path', '').strip()
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
            
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Make sure we don't escape the workspace with path traversal
        file_path = file_path.replace('..', '')  # Basic protection
        target_file = (workspace_path / file_path).resolve()
        
        if not str(target_file).startswith(str(workspace_path.resolve())):
            return jsonify({'error': 'Access denied: Cannot create files outside workspace'}), 403
            
        # Create parent directories if they don't exist
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Don't overwrite existing files
        if target_file.exists():
            return jsonify({'error': 'File already exists'}), 409
            
        # Write file content
        with open(target_file, 'w') as f:
            f.write(content)
            
        # Log file creation
        logging.info(f"File created: {target_file}")
        
        return jsonify({
            'success': True,
            'message': 'File created successfully',
            'file_path': file_path,
            'file_size': target_file.stat().st_size
        })
    except Exception as e:
        logging.error(f"Error creating file: {str(e)}")
        return jsonify({'error': str(e)}), 500
        


@app.route('/api/save_file', methods=['POST'])
def save_file():
    """Save changes to a file in the workspace."""
    try:
        data = request.json
        file_path = data.get('file_path', '').strip()
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
            
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Make sure we don't escape the workspace
        file_path = file_path.replace('..', '')  # Basic protection
        target_file = (workspace_path / file_path).resolve()
        
        if not str(target_file).startswith(str(workspace_path.resolve())):
            return jsonify({'error': 'Access denied: Cannot modify files outside workspace'}), 403
            
        # Check if file exists
        if not target_file.exists():
            return jsonify({'error': 'File not found'}), 404
            
        # Check if it's a file (not a directory)
        if target_file.is_dir():
            return jsonify({'error': 'Cannot save to a directory'}), 400
            
        # Write file content
        with open(target_file, 'w') as f:
            f.write(content)
            
        # Log file update
        logging.info(f"File updated: {target_file}")
        
        return jsonify({
            'success': True,
            'message': 'File saved successfully',
            'file_path': file_path,
            'file_size': target_file.stat().st_size
        })
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/natural_language', methods=['POST'])
def process_natural_language():
    """
    Procesa una instrucción en lenguaje natural y la convierte en acciones.
    Este endpoint permite a los agentes manipular archivos y ejecutar comandos
    a través de instrucciones en lenguaje natural.
    """
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó texto para procesar'
            }), 400
        
        # Patrones para diferentes acciones
        file_patterns = {
            'modify_file': re.compile(r'(?:modifica|edita|cambia|actualiza|agrega|a[ñn]ade).*?(?:archivo|fichero).*?[\"\'"]?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[\"\'"]?', re.IGNORECASE),
            'create_file': re.compile(r'(?:crea|genera|nuevo).*?(?:archivo|fichero).*?[\"\'"]?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[\"\'"]?', re.IGNORECASE),
            'delete_file': re.compile(r'(?:elimina|borra|quita|remueve).*?(?:archivo|fichero).*?[\"\'"]?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[\"\'"]?', re.IGNORECASE),
            'execute_command': re.compile(r'(?:ejecuta|corre|lanza|inicia).*?(?:comando|instrucci[óo]n|terminal)[\:\s]?[\"\'"]?(.+?)[\"\'"]?(?:[\.!\?]|$)', re.IGNORECASE),
            'view_file': re.compile(r'(?:muestra|visualiza|ver|abre).*?(?:archivo|fichero).*?[\"\'"]?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[\"\'"]?', re.IGNORECASE)
        }
        
        # Extraer contenido (para crear/modificar)
        content_pattern = re.compile(r'(?:contenido|código|texto)[\:\s]?[\"\'"](.+?)[\"\'"]|```(?:\w+)?\s*(.+?)```', re.IGNORECASE | re.DOTALL)
        content_match = content_pattern.search(text)
        content = None
        if content_match:
            content = content_match.group(1) if content_match.group(1) else content_match.group(2)
        
        # Determinar acción y parámetros
        action = None
        params = {}
        
        for action_type, pattern in file_patterns.items():
            match = pattern.search(text)
            if match:
                action = action_type
                if action_type == 'execute_command':
                    params['command'] = match.group(1).strip()
                else:
                    params['file_path'] = match.group(1).strip()
                
                if action_type in ['create_file', 'modify_file'] and content:
                    params['content'] = content
                
                break
        
        # Si no se determinó ninguna acción
        if not action:
            return jsonify({
                'success': False,
                'message': 'No se pudo determinar la acción a realizar. Por favor, sé más específico.'
            }), 400
        
        # Obtener el workspace del usuario
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Procesar la acción
        result = {}
        
        if action == 'execute_command':
            # Ejecutar comando en terminal
            command = params.get('command')
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(workspace_path)
                )
                stdout, stderr = process.communicate(timeout=30)
                
                result = {
                    'success': process.returncode == 0,
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                    'returncode': process.returncode
                }
            except subprocess.TimeoutExpired:
                result = {
                    'success': False,
                    'message': 'El comando excedió el tiempo límite de ejecución (30s)'
                }
            except Exception as e:
                result = {
                    'success': False,
                    'message': f'Error al ejecutar el comando: {str(e)}'
                }
        else:
            # Asegurar que estamos operando dentro del workspace
            file_path = params.get('file_path', '')
            file_path = file_path.replace('..', '')  # Prevenir path traversal
            target_file = (workspace_path / file_path).resolve()
            
            if not str(target_file).startswith(str(workspace_path.resolve())):
                return jsonify({
                    'success': False,
                    'message': 'Acceso denegado: No se puede acceder a archivos fuera del workspace'
                }), 403
            
            # Procesar operaciones de archivos
            if action == 'create_file':
                content = params.get('content', '')
                try:
                    # Crear directorios si no existen
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Verificar si el archivo ya existe
                    if target_file.exists():
                        result = {
                            'success': False,
                            'message': f'El archivo {file_path} ya existe'
                        }
                    else:
                        with open(target_file, 'w') as f:
                            f.write(content or '')
                        
                        result = {
                            'success': True,
                            'message': f'Archivo {file_path} creado correctamente'
                        }
                except Exception as e:
                    result = {
                        'success': False,
                        'message': f'Error al crear el archivo: {str(e)}'
                    }
            
            elif action == 'modify_file':
                content = params.get('content', '')
                try:
                    if not target_file.exists():
                        result = {
                            'success': False,
                            'message': f'El archivo {file_path} no existe'
                        }
                    else:
                        # Leer contenido actual
                        with open(target_file, 'r') as f:
                            current_content = f.read()
                        
                        # Escribir contenido actualizado
                        with open(target_file, 'w') as f:
                            f.write(current_content + '\n' + content)
                        
                        result = {
                            'success': True,
                            'message': f'Archivo {file_path} modificado correctamente'
                        }
                except Exception as e:
                    result = {
                        'success': False,
                        'message': f'Error al modificar el archivo: {str(e)}'
                    }
            
            elif action == 'delete_file':
                try:
                    if not target_file.exists():
                        result = {
                            'success': False,
                            'message': f'El archivo {file_path} no existe'
                        }
                    else:
                        if target_file.is_dir():
                            shutil.rmtree(target_file)
                        else:
                            target_file.unlink()
                        
                        result = {
                            'success': True,
                            'message': f'Archivo {file_path} eliminado correctamente'
                        }
                except Exception as e:
                    result = {
                        'success': False,
                        'message': f'Error al eliminar el archivo: {str(e)}'
                    }
            
            elif action == 'view_file':
                try:
                    if not target_file.exists():
                        result = {
                            'success': False,
                            'message': f'El archivo {file_path} no existe'
                        }
                    else:
                        with open(target_file, 'r') as f:
                            content = f.read()
                        
                        result = {
                            'success': True,
                            'message': f'Contenido del archivo {file_path}:',
                            'content': content,
                            'file_type': get_file_type(target_file.name)
                        }
                except Exception as e:
                    result = {
                        'success': False,
                        'message': f'Error al leer el archivo: {str(e)}'
                    }
        
        # Notificar a través de WebSockets
        if action in ['create_file', 'modify_file', 'delete_file']:
            try:
                socketio.emit('file_change', {
                    'type': action.split('_')[0],  # create, modify, delete
                    'file_path': file_path,
                    'workspace': user_id
                }, namespace='/ws')
            except Exception as e:
                logging.error(f"Error emitiendo evento WebSocket: {str(e)}")
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error procesando lenguaje natural: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error procesando instrucción: {str(e)}'
        }), 500

@app.route('/api/delete_file', methods=['POST'])
def delete_file():
    """Delete a file or directory in the workspace."""
    try:
        data = request.json
        file_path = data.get('file_path', '').strip()
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
            
        # Get the user workspace
        user_id = session.get('user_id', 'default')
        workspace_path = get_user_workspace(user_id)
        
        # Make sure we don't escape the workspace
        file_path = file_path.replace('..', '')  # Basic protection
        target_path = (workspace_path / file_path).resolve()
        
        if not str(target_path).startswith(str(workspace_path.resolve())):
            return jsonify({'error': 'Access denied: Cannot delete files outside workspace'}), 403
            
        # Check if path exists
        if not target_path.exists():
            return jsonify({'error': 'File or directory not found'}), 404
            
        # Delete the file or directory
        if target_path.is_dir():
            # Delete directory and all contents
            import shutil
            shutil.rmtree(target_path)
            message = 'Directory deleted successfully'
        else:
            # Delete single file
            target_path.unlink()
            message = 'File deleted successfully'
            
        # Log file deletion
        logging.info(f"Deleted: {target_path}")
        
        return jsonify({
            'success': True,
            'message': message,
            'file_path': file_path
        })
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/session', methods=['GET'])
def get_session():
    """Get the current session info or create a new one."""
    if 'user_id' not in session:
        session['user_id'] = 'user_' + os.urandom(4).hex()
    
    return jsonify({
        'user_id': session['user_id'],
        'workspace': str(get_user_workspace(session['user_id']).name)
    })

# Initialize SocketIO - using threading mode for more stable connections
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25, logger=True)

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection to WebSocket."""
    logging.info("Client connected to WebSocket")
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection from WebSocket."""
    logging.info("Client disconnected from WebSocket")

@socketio.on('join_workspace')
def handle_join_workspace(data):
    """Join a specific workspace for real-time updates."""
    workspace_id = data.get('workspace_id', 'default')
    logging.info(f"Client joined workspace: {workspace_id}")
    # Join a room named after the workspace for targeted broadcasts
    from flask_socketio import join_room
    join_room(workspace_id)
    emit('workspace_update', {
        'status': 'joined',
        'workspace_id': workspace_id
    })

# Function to notify clients about file changes
def notify_file_change(workspace_id, change_type, file_data):
    """Send real-time notification about file changes."""
    socketio.emit('file_change', {
        'type': change_type,  # 'create', 'update', 'delete'
        'file': file_data
    })

# Function to notify clients about command execution
def notify_command_executed(workspace_id, command_data):
    """Send real-time notification about command execution."""
    socketio.emit('command_executed', command_data)

# Monitor for file changes in workspaces
def watch_workspace_files():
    """Background task to monitor file changes in workspaces."""
    import time
    import os
    from models import Workspace, File
    
    tracked_files = {}
    
    while True:
        try:
            # Check all workspaces
            with app.app_context():
                workspaces = db.session.query(Workspace).all()
                
                for workspace in workspaces:
                    workspace_path = Path(workspace.path)
                    workspace_id = workspace.name
                    
                    if not workspace_path.exists():
                        continue
                        
                    # Get all files in workspace
                    current_files = {}
                    for item in workspace_path.glob('**/*'):
                        if item.is_file() and not any(part.startswith('.') for part in item.parts):
                            rel_path = item.relative_to(workspace_path)
                            mtime = item.stat().st_mtime
                            size = item.stat().st_size
                            current_files[str(rel_path)] = {'mtime': mtime, 'size': size}
                    
                    # Check for changes
                    if workspace_id not in tracked_files:
                        tracked_files[workspace_id] = current_files
                        continue
                        
                    old_files = tracked_files[workspace_id]
                    
                    # Check for new or modified files
                    for file_path, info in current_files.items():
                        if file_path not in old_files:
                            # New file
                            file_data = {
                                'path': file_path,
                                'workspace_id': workspace_id,
                                'size': info['size']
                            }
                            notify_file_change(workspace_id, 'create', file_data)
                        elif old_files[file_path]['mtime'] != info['mtime'] or old_files[file_path]['size'] != info['size']:
                            # Modified file
                            file_data = {
                                'path': file_path,
                                'workspace_id': workspace_id,
                                'size': info['size']
                            }
                            notify_file_change(workspace_id, 'update', file_data)
                    
                    # Check for deleted files
                    for file_path in old_files:
                        if file_path not in current_files:
                            # Deleted file
                            file_data = {
                                'path': file_path,
                                'workspace_id': workspace_id
                            }
                            notify_file_change(workspace_id, 'delete', file_data)
                    
                    # Update tracked files
                    tracked_files[workspace_id] = current_files
        except Exception as e:
            logging.error(f"Error monitoring workspace files: {str(e)}")
            
        # Sleep to avoid excessive CPU usage
        time.sleep(1)

# Start background task for file monitoring when running the app directly
if __name__ == '__main__':
    import threading
    # Start file watcher in a background thread
    file_watcher_thread = threading.Thread(target=watch_workspace_files, daemon=True)
    file_watcher_thread.start()
    
    # Start the SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
