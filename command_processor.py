from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import logging
import re
import json
import time
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", os.urandom(24).hex())
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    async_mode='eventlet',
                    logger=True,
                    engineio_logger=True,
                    ping_timeout=60,
                    ping_interval=25)

# Security: List of allowed commands with regex patterns - MEJORADO PARA PERMITIR REDIRECCIONES
ALLOWED_COMMANDS = {
    'mkdir': r'^mkdir [\w\-\.\/]+$',
    'ls': r'^ls( -[alh]+)?( [\w\/\-\.]+)?$',
    'echo': r'^echo .*$',  # Patrón más permisivo para echo y redirecciones
    'cat': r'^cat( [\w\/\-\.]+)+$|^cat [\w\/\-\.]+ << \'EOF\'.*EOF$',  # Permitir heredocs
    'touch': r'^touch [\w\/\-\.]+$',
    'rm': r'^rm( -[rf]+)? [\w\/\-\.]+$',
    'cp': r'^cp( -[r]+)? [\w\/\-\.]+ [\w\/\-\.]+$',
    'mv': r'^mv [\w\/\-\.]+ [\w\/\-\.]+$',
}

# NLP command conversion function
def nl_to_bash(natural_command):
    """
    Convert natural language to bash command
    In production, this would use OpenAI or similar API
    """
    # Lowercase the command for better matching
    natural_command = natural_command.lower()

    # Detectar comandos específicos para crear archivos con contenido
    if re.search(r'cre[ae]r? (un )?archivo (\w+) con (un )?mensaje', natural_command):
        # Extraer el nombre del archivo
        match = re.search(r'archivo (\w+)', natural_command)
        if match:
            filename = match.group(1)
            # Si no tiene extensión, agregar .html por defecto
            if '.' not in filename:
                filename = f"{filename}.html"
            return f"echo '<!DOCTYPE html><html><head><title>Bienvenida</title></head><body><h1>Mensaje de Bienvenida</h1></body></html>' > {filename}"

    # Verificar si es un comando para crear archivo con contenido
    if 'crear archivo con contenido' in natural_command:
        try:
            # Extraer la parte después de "crear archivo con contenido"
            remaining_text = natural_command.split('crear archivo con contenido', 1)[1].strip()

            # Buscar la separación entre el nombre del archivo y el contenido
            if 'con contenido' in remaining_text:
                # El formato es "crear archivo con contenido nombre_archivo con contenido contenido_archivo"
                filename, content = remaining_text.split('con contenido', 1)
                filename = filename.strip()
                content = content.strip()

                # Escapar comillas en el contenido si es necesario
                content = content.replace('"', '\\"')

                # Generar el comando echo
                return f'echo "{content}" > {filename}'
            else:
                # Si no hay "con contenido" después del nombre del archivo
                return f'touch {remaining_text}'
        except Exception as e:
            return "echo 'Error al procesar el comando de crear archivo con contenido'"

    # Procesar otros comandos
    command_map = {
        'crear carpeta': 'mkdir',
        'crear directorio': 'mkdir',
        'listar': 'ls',
        'mostrar archivos': 'ls',
        'mostrar contenido de': 'cat',
        'leer archivo': 'cat',
        'crear archivo': 'touch',
        'eliminar': 'rm',
        'borrar': 'rm -f',
        'borrar carpeta': 'rm -rf',
        'copiar': 'cp',
        'mover': 'mv',
        'crear archivo con contenido': 'echo'  # Nuevo comando
    }

    # Procesar otros comandos
    for pattern, bash_prefix in command_map.items():
        if pattern in natural_command:
            # Extract arguments after the pattern
            args = natural_command.split(pattern, 1)[1].strip()

            # Manejo especial para echo con redirección
            if bash_prefix == 'echo' and '>' not in args:
                return f"{bash_prefix} \"{args}\" > archivo.txt"

            return f"{bash_prefix} {args}"

    # Llamada a la API de OpenAI para conversión de lenguaje natural a comandos
    if os.environ.get('OPENAI_API_KEY'):
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                        Eres un experto asistente de terminal que convierte lenguaje natural en comandos bash precisos.
                        El objetivo es generar comandos bash que cumplan con las instrucciones del usuario.
                        INSTRUCCIONES:
                        1. Genera ÚNICAMENTE el comando bash correspondiente, sin explicaciones adicionales
                        2. Para crear archivos con contenido, utiliza echo con comillas y redirección adecuada
                        3. Para operaciones complejas, usa múltiples comandos separados por punto y coma o &&
                        4. Asegúrate de escapar correctamente los caracteres especiales
                        5. Si la operación requiere múltiples líneas en un archivo, utiliza heredocs (<<EOF)

                        EJEMPLOS:
                        - Si el usuario dice: "crea un archivo index.html con un mensaje de bienvenida"
                          Responderás: echo '<!DOCTYPE html><html><head><title>Bienvenida</title></head><body><h1>Mensaje de Bienvenida</h1></body></html>' > index.html

                        - Si el usuario dice: "crear archivo JavaScript que muestre una alerta"
                          Responderás: echo 'function mostrarAlerta() { alert("Hola mundo!"); }' > script.js

                        - Si el usuario dice: "crear componente React para un botón"
                          Responderás: cat > Button.jsx << 'EOF'
                        import React from 'react';

                        const Button = ({ text, onClick }) => {
                          return (
                            <button className="custom-button" onClick={onClick}>
                              {text}
                            </button>
                          );
                        };

                        export default Button;
                        EOF

                        Prioriza la exactitud y utilidad del comando generado.
                    """},
                    {"role": "user", "content": natural_command}
                ],
                temperature=0.1,
                max_tokens=500  # Aumentado para permitir comandos más complejos
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error with OpenAI API: {str(e)}")
            return "echo 'Error al procesar el comando. Por favor intente de nuevo.'"

    # Si no hay API configurada o falla
    return "echo 'Para usar esta función, configure la API de OpenAI.'"


def validate_command(command):
    """Validate if command is allowed based on regexes"""
    # Tratar comandos con redirección especialmente
    if '>' in command:
        cmd_parts = command.split('>', 1)
        base_command = cmd_parts[0].strip()

        # Validar solo la parte del comando antes de la redirección
        command_parts = base_command.split()
        if not command_parts:
            return False

        base_cmd = command_parts[0]

        # Para echo con redirección, permitimos el patrón completo
        if base_cmd == 'echo':
            return True
    else:
        command_parts = command.split()
        if not command_parts:
            return False

        base_cmd = command_parts[0]

    if base_cmd in ALLOWED_COMMANDS:
        pattern = ALLOWED_COMMANDS[base_cmd]
        match_result = re.match(pattern, command)

        # Log para depuración
        logging.debug(f"Command: {command}, Pattern: {pattern}, Match: {match_result is not None}")

        return match_result is not None

    return False

def execute_command(command):
    """Execute command and return result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=5  # Safety: timeout after 5 seconds
        )

        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'command': command
            }
        else:
            return {
                'success': False,
                'output': result.stderr,
                'command': command
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': 'Command timed out after 5 seconds',
            'command': command
        }
    except Exception as e:
        return {
            'success': False,
            'output': str(e),
            'command': command
        }

# File system event handler
class FileSystemHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            socketio.emit('file_created', {
                'path': event.src_path,
                'is_directory': False,
                'timestamp': time.time()
            })
        else:
            socketio.emit('directory_created', {
                'path': event.src_path,
                'is_directory': True,
                'timestamp': time.time()
            })

    def on_deleted(self, event):
        socketio.emit('file_deleted', {
            'path': event.src_path,
            'is_directory': event.is_directory,
            'timestamp': time.time()
        })

    def on_modified(self, event):
        if not event.is_directory:
            socketio.emit('file_modified', {
                'path': event.src_path,
                'timestamp': time.time()
            })

    def on_moved(self, event):
        socketio.emit('file_moved', {
            'src_path': event.src_path,
            'dest_path': event.dest_path,
            'is_directory': event.is_directory,
            'timestamp': time.time()
        })

# Start file system observer
observer = Observer()
event_handler = FileSystemHandler()
observer.schedule(event_handler, path=".", recursive=True)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'connected'})
    logging.info('Client connected to WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected from WebSocket')

@socketio.on('natural_command')
def handle_natural_command(data):
    """Process natural language command"""
    natural_text = data.get('text', '')
    logging.info(f"Received natural command: {natural_text}")

    # Convert to bash
    bash_command = nl_to_bash(natural_text)
    logging.info(f"Converted to bash: {bash_command}")

    # Validación con más información
    validation_result = validate_command(bash_command)
    logging.info(f"Validation result: {validation_result}")

    # Log con el patrón específico que está fallando
    if not validation_result:
        command_parts = bash_command.split()
        if command_parts and command_parts[0] in ALLOWED_COMMANDS:
            pattern = ALLOWED_COMMANDS[command_parts[0]]
            match_result = re.match(pattern, bash_command)
            logging.info(f"Command: {bash_command}, Pattern: {pattern}, Match: {match_result is not None}")

    # Validate command
    if validation_result:
        # Execute command
        result = execute_command(bash_command)
        emit('command_result', result)
    else:
        # Si el comando tiene un echo con redirección, hacemos una excepción
        if bash_command.startswith('echo') and '>' in bash_command:
            result = execute_command(bash_command)
            emit('command_result', result)
        else:
            emit('command_result', {
                'success': False,
                'output': f"Comando no permitido: {bash_command}",
                'command': bash_command
            })

@socketio.on('bash_command')
def handle_bash_command(data):
    """Process direct bash command"""
    bash_command = data.get('command', '')
    logging.info(f"Received bash command: {bash_command}")

    # Validate command
    if validate_command(bash_command):
        # Execute command
        result = execute_command(bash_command)
        emit('command_result', result)
    else:
        # Si el comando tiene un echo con redirección, hacemos una excepción
        if bash_command.startswith('echo') and '>' in bash_command:
            result = execute_command(bash_command)
            emit('command_result', result)
        else:
            emit('command_result', {
                'success': False,
                'output': f"Comando no permitido: {bash_command}",
                'command': bash_command
            })

@socketio.on('list_directory')
def handle_list_directory(data):
    """List directory contents"""
    try:
        directory = data.get('path', '.')

        # Security: prevent directory traversal
        if '..' in directory:
            emit('directory_contents', {
                'success': False,
                'error': 'No se permite la navegación hacia arriba (..)' 
            })
            return

        # Get directory contents
        contents = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            contents.append({
                'name': item,
                'path': item_path,
                'is_directory': os.path.isdir(item_path),
                'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                'modified': os.path.getmtime(item_path)
            })

        emit('directory_contents', {
            'success': True,
            'path': directory,
            'contents': contents
        })
    except Exception as e:
        emit('directory_contents', {
            'success': False,
            'error': str(e)
        })

@socketio.on('delete_file')
def handle_delete_file(data):
    """Delete a file"""
    try:
        file_path = data.get('path', '')

        # Validación básica
        if not file_path:
            emit('delete_result', {
                'success': False,
                'error': 'Ruta de archivo no especificada'
            })
            return

        # Prevenir navegación hacia arriba
        if '..' in file_path:
            emit('delete_result', {
                'success': False,
                'error': 'No se permite la navegación hacia arriba (..)'
            })
            return

        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            emit('delete_result', {
                'success': False,
                'error': f'El archivo no existe: {file_path}'
            })
            return

        # Eliminar archivo
        if os.path.isfile(file_path):
            os.remove(file_path)
            emit('delete_result', {
                'success': True,
                'message': f'Archivo eliminado: {file_path}'
            })

            # Notificar cambio en sistema de archivos
            emit('file_system_changed', {
                'type': 'file_deleted',
                'path': file_path,
                'timestamp': time.time()
            })
        else:
            emit('delete_result', {
                'success': False,
                'error': f'La ruta no es un archivo: {file_path}'
            })
    except Exception as e:
        logging.error(f"Error eliminando archivo: {str(e)}")
        emit('delete_result', {
            'success': False,
            'error': str(e)
        })

@socketio.on('delete_directory')
def handle_delete_directory(data):
    """Delete a directory and its contents"""
    try:
        dir_path = data.get('path', '')

        # Validación básica
        if not dir_path:
            emit('delete_result', {
                'success': False,
                'error': 'Ruta de directorio no especificada'
            })
            return

        # Prevenir navegación hacia arriba
        if '..' in dir_path:
            emit('delete_result', {
                'success': False,
                'error': 'No se permite la navegación hacia arriba (..)'
            })
            return

        # Verificar si el directorio existe
        if not os.path.exists(dir_path):
            emit('delete_result', {
                'success': False,
                'error': f'El directorio no existe: {dir_path}'
            })
            return

        # Verificar que es un directorio
        if not os.path.isdir(dir_path):
            emit('delete_result', {
                'success': False,
                'error': f'La ruta no es un directorio: {dir_path}'
            })
            return

        # Eliminar directorio y su contenido
        import shutil
        shutil.rmtree(dir_path)

        emit('delete_result', {
            'success': True,
            'message': f'Directorio eliminado: {dir_path}'
        })

        # Notificar cambio en sistema de archivos
        emit('file_system_changed', {
            'type': 'directory_deleted',
            'path': dir_path,
            'timestamp': time.time()
        })
    except Exception as e:
        logging.error(f"Error eliminando directorio: {str(e)}")
        emit('delete_result', {
            'success': False,
            'error': str(e)
        })

@app.route('/')
def index():
    return render_template('command_terminal.html')

@app.route('/terminal')
def terminal():
    return render_template('command_terminal.html')

def start_observer():
    observer.start()

if __name__ == '__main__':
    # Start file system observer in a separate thread
    observer_thread = threading.Thread(target=start_observer)
    observer_thread.daemon = True
    observer_thread.start()

    # Configurar eventlet para Socket.IO
    import eventlet
    eventlet.monkey_patch()

    # Start Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
