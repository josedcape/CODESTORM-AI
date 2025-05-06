import os
import json
import uuid
import logging
import subprocess
import shutil
from pathlib import Path
from functools import lru_cache
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
import traceback
from werkzeug.utils import secure_filename

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('xterm')

# Constantes
DEFAULT_WORKSPACE = 'default'
WORKSPACE_ROOT = 'user_workspaces'
README_TEMPLATE = """# Workspace

Este es tu espacio de trabajo colaborativo. Usa comandos o instrucciones en lenguaje natural para crear y modificar archivos.

Ejemplos:
- "crea una carpeta llamada proyectos"
- "mkdir proyectos"
- "touch archivo.txt"
"""

# Comandos que pueden modificar archivos
FILE_MODIFYING_COMMANDS = ['mkdir', 'touch', 'rm', 'cp', 'mv', 'echo', 'cat', 'nano', 'vim', 'sed', 'awk', 'chmod']

# Blueprint para XTerm
xterm_bp = Blueprint('xterm', __name__, url_prefix='/xterm')

class WorkspaceManager:
    """Gestiona los espacios de trabajo de los usuarios."""

    def __init__(self):
        self.workspaces = {}

    def get_workspace_path(self, user_id):
        """Obtiene la ruta del workspace del usuario."""
        if not user_id:
            user_id = DEFAULT_WORKSPACE

        if user_id not in self.workspaces:
            workspace_path = Path(WORKSPACE_ROOT) / user_id
            os.makedirs(workspace_path, exist_ok=True)
            self.workspaces[user_id] = workspace_path

            # Crear README inicial si no existe
            self._initialize_workspace(workspace_path)

        return self.workspaces[user_id]

    def _initialize_workspace(self, workspace_path):
        """Inicializa un workspace con archivos básicos."""
        readme_path = workspace_path / 'README.md'
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write(README_TEMPLATE)

    def get_full_path(self, user_id, relative_path='.'):
        """Obtiene la ruta completa a partir de una ruta relativa."""
        workspace_path = self.get_workspace_path(user_id)

        if relative_path == '.':
            return workspace_path

        full_path = workspace_path / relative_path

        # Verificar que la ruta no salga del workspace (seguridad)
        if not os.path.normpath(str(full_path)).startswith(os.path.normpath(str(workspace_path))):
            raise ValueError(f"Ruta no válida: {relative_path}")

        return full_path

# Instancia global del gestor de workspaces
workspace_manager = WorkspaceManager()

# Caché para comandos frecuentes
@lru_cache(maxsize=100)
def get_command_suggestion(text_key):
    """Obtiene sugerencias de comandos para texto frecuente."""
    return process_natural_language(text_key, 'cached')

@xterm_bp.route('/xterm_terminal')
def xterm_terminal():
    """Render the XTerm terminal page."""
    # Asegurar que existe el workspace por defecto
    workspace_manager.get_workspace_path(DEFAULT_WORKSPACE)
    return render_template('xterm_terminal.html')

# Agregar una ruta adicional para acceder sin el prefijo
@xterm_bp.route('/')
def xterm_terminal_root():
    """Render the XTerm terminal page at the root of the blueprint."""
    workspace_manager.get_workspace_path(DEFAULT_WORKSPACE)
    return render_template('xterm_terminal.html')

@xterm_bp.route('/api/xterm/execute', methods=['POST'])
def execute_xterm_command():
    """Execute a command in the terminal."""
    try:
        data = request.json
        command = data.get('command', '').strip()
        user_id = data.get('user_id', DEFAULT_WORKSPACE)

        if not command:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó comando'
            }), 400

        # Obtener directorio de trabajo
        workspace_path = workspace_manager.get_workspace_path(user_id)

        # Validar comando por seguridad
        if not is_command_safe(command):
            return jsonify({
                'success': False,
                'error': 'Comando no permitido por razones de seguridad'
            }), 403

        # Ejecutar comando
        result = execute_command(command, workspace_path)

        return jsonify({
            'success': result['success'],
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', ''),
            'exitCode': result.get('returncode', 1)
        })

    except ValueError as e:
        logger.warning(f"Error de validación: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error ejecutando comando XTerm: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@xterm_bp.route('/api/process_natural', methods=['POST'])
def process_natural_instruction():
    """Procesa instrucciones en lenguaje natural y devuelve comandos o respuestas."""
    try:
        data = request.json
        text = data.get('text', '').strip()
        user_id = data.get('user_id', DEFAULT_WORKSPACE)
        model = data.get('model', 'openai')

        if not text:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó texto para procesar'
            }), 400

        # Procesar la instrucción
        command, response = process_natural_language(text, model)

        # Preparar resultado
        result = {
            'success': True if (command or response) else False
        }

        if command:
            result['command'] = command

        if response:
            result['response'] = response

        if not command and not response:
            result = {
                'success': False,
                'error': 'No se pudo procesar la instrucción'
            }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error procesando instrucción natural: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@xterm_bp.route('/api/delete_file', methods=['GET', 'DELETE'])
def delete_file():
    """Delete a file from the workspace."""
    try:
        if request.method == 'DELETE':
            data = request.json
            file_path = data.get('file_path')
        else:
            file_path = request.args.get('path')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        user_id = request.args.get('user_id', DEFAULT_WORKSPACE)

        # Obtener ruta completa
        try:
            full_path = workspace_manager.get_full_path(user_id, file_path)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 403

        # Eliminar archivo o directorio
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

            return jsonify({
                'success': True,
                'message': f'Se eliminó {file_path} correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

    except Exception as e:
        logger.error(f"Error al eliminar archivo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def is_command_safe(command):
    """Verifica si un comando es seguro para ejecutar."""
    # Lista de comandos prohibidos por seguridad
    dangerous_commands = [
        'rm -rf /', 'rm -rf *', 'rm -rf ~', 'rm -rf .', 
        'wget', 'curl', 'sudo', 'su', 'chmod 777', 
        '>', '|', ';', '&&', '||', '`', '$(',
    ]

    # Verificar si el comando contiene alguno de los patrones peligrosos
    command_lower = command.lower()
    for dangerous in dangerous_commands:
        if dangerous in command_lower:
            # Permitir algunos casos específicos
            if dangerous in ['>', '|'] and is_redirection_safe(command):
                continue
            return False

    return True

def is_redirection_safe(command):
    """Verifica si una redirección es segura."""
    # Permitir redirecciones simples a archivos dentro del directorio actual
    if '>' in command:
        parts = command.split('>')
        if len(parts) == 2 and not any(c in parts[1] for c in ['/', '..']):
            return True

    # Permitir pipes simples entre comandos básicos
    if '|' in command:
        parts = command.split('|')
        if all(is_basic_command(part.strip()) for part in parts):
            return True

    return False

def is_basic_command(cmd):
    """Verifica si es un comando básico."""
    basic_commands = ['ls', 'cat', 'grep', 'sed', 'awk', 'head', 'tail', 'wc', 'sort', 'uniq']
    return any(cmd.startswith(bc) for bc in basic_commands)

def execute_command(command, cwd):
    """Ejecuta un comando y devuelve su resultado."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=10)  # Timeout de 10 segundos

        return {
            'success': process.returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        }
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Comando cancelado: tiempo de ejecución excedido (10s)',
            'returncode': 124
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Error al ejecutar comando: {str(e)}',
            'returncode': 1
        }

def init_xterm_blueprint(app, socketio):
    """Registra el blueprint en la aplicación Flask."""
    app.register_blueprint(xterm_bp, url_prefix='/xterm', name='xterm_blueprint')

    # Registrar manejadores de eventos SocketIO
    @socketio.on('connect')
    def handle_connect():
        """Maneja la conexión de un cliente."""
        client_id = request.sid
        logger.info(f"Cliente conectado: {client_id}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Maneja la desconexión de un cliente."""
        client_id = request.sid
        logger.info(f"Cliente desconectado: {client_id}")

    @socketio.on('join_room')
    def handle_join(data):
        """Maneja la unión a una sala."""
        room = data.get('room')
        if room:
            join_room(room)
            emit('room_joined', {'success': True, 'room': room}, room=request.sid)
            logger.info(f"Cliente {request.sid} unido a la sala {room}")

    @socketio.on('leave_room')
    def handle_leave(data):
        """Maneja la salida de una sala."""
        room = data.get('room')
        if room:
            leave_room(room)
            emit('room_left', {'success': True, 'room': room}, room=request.sid)
            logger.info(f"Cliente {request.sid} salió de la sala {room}")

    @socketio.on('bash_command')
    def handle_bash_command(data):
        """Ejecuta un comando bash y devuelve el resultado."""
        command = data.get('command', '').strip()
        user_id = data.get('user_id', DEFAULT_WORKSPACE)
        terminal_id = data.get('terminal_id', 'default')
        directory = data.get('directory', '.')

        logger.info(f"Comando recibido: '{command}' de usuario: {user_id}, terminal: {terminal_id}")

        if not command:
            emit('command_result', {
                'success': False,
                'command': '',
                'stderr': 'No se proporcionó ningún comando',
                'output': 'No se proporcionó ningún comando',
                'terminal_id': terminal_id
            }, room=request.sid)
            return

        try:
            # Validar el comando por seguridad
            if not is_command_safe(command):
                emit('command_result', {
                    'success': False,
                    'command': command,
                    'stderr': 'Comando no permitido por razones de seguridad',
                    'output': 'Comando no permitido por razones de seguridad',
                    'terminal_id': terminal_id
                }, room=request.sid)
                return

            # Obtener ruta completa para el directorio actual
            try:
                current_dir = workspace_manager.get_full_path(user_id, directory)
            except ValueError as e:
                emit('command_result', {
                    'success': False,
                    'command': command,
                    'stderr': str(e),
                    'output': str(e),
                    'terminal_id': terminal_id
                }, room=request.sid)
                return

            # Ejecutar comando en esa ruta
            logger.debug(f"Ejecutando comando: '{command}' en directorio: {current_dir}")
            result = execute_command(command, current_dir)

            # Emitir resultado
            response = {
                'success': result['success'],
                'command': command,
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', ''),
                'output': result.get('stdout', '') if result['success'] else result.get('stderr', ''),
                'terminal_id': terminal_id
            }
            logger.debug(f"Resultado del comando: {result['success']}")
            emit('command_result', response, room=request.sid)

            # Detectar cambios en archivos para notificar a todos los clientes
            if result['success'] and any(cmd in command for cmd in FILE_MODIFYING_COMMANDS):
                room_id = f"workspace_{user_id}"
                emit('file_change', {
                    'type': 'command',
                    'message': f'Comando ejecutado: {command}',
                    'command': command,
                    'user_id': user_id
                }, room=room_id)

        except Exception as e:
            logger.error(f"Error al ejecutar comando: {str(e)}")
            logger.error(traceback.format_exc())
            emit('command_result', {
                'success': False,
                'command': command,
                'stderr': str(e),
                'output': f"Error: {str(e)}",
                'terminal_id': terminal_id
            }, room=request.sid)

    @socketio.on('natural_language')
    def handle_natural_language(data):
        """Procesa instrucciones en lenguaje natural de forma segura."""
        text = data.get('text', '').strip()
        user_id = data.get('user_id', DEFAULT_WORKSPACE)
        model = data.get('model', 'openai')
        terminal_id = data.get('terminal_id', 'default')

        if not text:
            emit('instruction_result', {
                'success': False,
                'command': '',
                'error': 'No se proporcionó ningún texto',
                'explanation': 'Es necesario proporcionar una instrucción',
                'terminal_id': terminal_id
            }, room=request.sid)
            return

        try:
            # Usar caché para consultas frecuentes
            if len(text) < 50:  # Solo cachear consultas cortas
                command, response = get_command_suggestion(text.lower())
            else:
                # Procesar el texto usando el modelo seleccionado
                command, response = process_natural_language(text, model)

            # Si tenemos un comando, devolverlo
            if command:
                # Validar el comando por seguridad
                if not is_command_safe(command):
                    emit('instruction_result', {
                        'success': False,
                        'command': command,
                        'error': 'El comando sugerido no está permitido por razones de seguridad',
                        'explanation': 'Por favor, intenta con una instrucción diferente',
                        'terminal_id': terminal_id
                    }, room=request.sid)
                    return

                emit('instruction_result', {
                    'success': True,
                    'command': command,
                    'explanation': f'Comando sugerido basado en: "{text}"',
                    'auto_execute': False,  # Siempre falso para seguridad
                    'terminal_id': terminal_id
                }, room=request.sid)
            # Si tenemos una respuesta, devolverla
            elif response:
                emit('instruction_result', {
                    'success': True,
                    'response': response,
                    'command': None,
                    'explanation': 'Respuesta del asistente',
                    'terminal_id': terminal_id
                }, room=request.sid)
            else:
                emit('instruction_result', {
                    'success': False,
                    'command': '',
                    'error': 'No se pudo procesar la instrucción',
                    'explanation': 'No se pudo generar ni comando ni respuesta',
                    'terminal_id': terminal_id
                }, room=request.sid)

        except Exception as e:
            logger.error(f"Error al procesar lenguaje natural: {str(e)}")
            logger.error(traceback.format_exc())
            emit('instruction_result', {
                'success': False,
                'command': '',
                'error': str(e),
                'explanation': 'Error al procesar la instrucción',
                'terminal_id': terminal_id
            }, room=request.sid)

    @socketio.on('list_directory')
    def handle_list_directory(data):
        """Lista los contenidos de un directorio."""
        path = data.get('path', '.')
        user_id = data.get('user_id', DEFAULT_WORKSPACE)

        try:
            # Obtener ruta completa
            try:
                target_dir = workspace_manager.get_full_path(user_id, path)
            except ValueError as e:
                emit('directory_contents', {
                    'success': False,
                    'error': str(e)
                }, room=request.sid)
                return

            # Verificar que exista
            if not target_dir.exists():
                emit('directory_contents', {
                    'success': False,
                    'error': 'Directorio no encontrado'
                }, room=request.sid)
                return

            # Listar archivos y directorios
            contents = []
            for item in os.listdir(target_dir):
                item_path = target_dir / item
                try:
                    stat_info = item_path.stat()
                    contents.append({
                        'name': item,
                        'is_directory': item_path.is_dir(),
                        'size': stat_info.st_size if item_path.is_file() else 0,
                        'modified': stat_info.st_mtime,
                        'permissions': stat_info.st_mode & 0o777
                    })
                except Exception as e:
                    logger.warning(f"Error al obtener información de {item_path}: {str(e)}")

            emit('directory_contents', {
                'success': True,
                'path': path,
                'contents': contents
            }, room=request.sid)

        except Exception as e:
            logger.error(f"Error al listar directorio: {str(e)}")
            logger.error(traceback.format_exc())
            emit('directory_contents', {
                'success': False,
                'error': str(e)
            }, room=request.sid)

    @socketio.on('read_file')
    def handle_read_file(data):
        """Lee el contenido de un archivo."""
        file_path = data.get('path', '')
        user_id = data.get('user_id', DEFAULT_WORKSPACE)

        if not file_path:
            emit('file_content', {
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }, room=request.sid)
            return

        try:
            # Obtener ruta completa
            try:
                full_path = workspace_manager.get_full_path(user_id, file_path)
            except ValueError as e:
                emit('file_content', {
                    'success': False,
                    'error': str(e)
                }, room=request.sid)
                return

            # Verificar que existe y es un archivo
            if not full_path.exists():
                emit('file_content', {
                    'success': False,
                    'error': 'Archivo no encontrado'
                }, room=request.sid)
                return

            if not full_path.is_file():
                emit('file_content', {
                    'success': False,
                    'error': 'La ruta especificada no es un archivo'
                }, room=request.sid)
                return

            # Leer contenido
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            emit('file_content', {
                'success': True,
                'path': file_path,
                'content': content
            }, room=request.sid)

        except Exception as e:
            logger.error(f"Error al leer archivo: {str(e)}")
            logger.error(traceback.format_exc())
            emit('file_content', {
                'success': False,
                'error': str(e)
            }, room=request.sid)

    @socketio.on('write_file')
    def handle_write_file(data):
        """Escribe contenido en un archivo."""
        file_path = data.get('path', '')
        content = data.get('content', '')
        user_id = data.get('user_id', DEFAULT_WORKSPACE)

        if not file_path:
            emit('file_written', {
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }, room=request.sid)
            return

        try:
            # Obtener ruta completa
            try:
                full_path = workspace_manager.get_full_path(user_id, file_path)
            except ValueError as e:
                emit('file_written', {
                    'success': False,
                    'error': str(e)
                }, room=request.sid)
                return

            # Crear directorios si no existen
            os.makedirs(full_path.parent, exist_ok=True)

            # Escribir contenido
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Notificar a todos los clientes en la sala del workspace
            room_id = f"workspace_{user_id}"
            emit('file_change', {
                'type': 'write',
                'path': file_path,
                'message': f'Archivo actualizado: {file_path}',
                'user_id': user_id
            }, room=room_id)

            emit('file_written', {
                'success': True,
                'path': file_path
            }, room=request.sid)

        except Exception as e:
            logger.error(f"Error al escribir archivo: {str(e)}")
            logger.error(traceback.format_exc())
            emit('file_written', {
                'success': False,
                'error': str(e)
            }, room=request.sid)

    # Configurar servidor WebSocket para Yjs
    @socketio.on('yjs')
    def handle_yjs(data):
        """Maneja mensajes de sincronización Yjs."""
        # Extraer información
        room = data.get('room')
        action = data.get('action')
        payload = data.get('payload')
        user_id = data.get('user_id', DEFAULT_WORKSPACE)

        if not room:
            return

        # Unirse a la sala si es join
        if action == 'join':
            join_room(room)
            emit('yjs', {
                'action': 'joined',
                'room': room,
                'user_id': user_id
            }, room=request.sid)
            return

        # Reenviar el mensaje a todos en la sala excepto al emisor
        emit('yjs', {
            'action': action,
            'payload': payload,
            'user_id': user_id
        }, room=room, skip_sid=request.sid)

    # Unirse a la sala del workspace al conectar
    @socketio.on('join_workspace')
    def handle_join_workspace(data):
        """Une al cliente a la sala de su workspace."""
        user_id = data.get('user_id', DEFAULT_WORKSPACE)
        room_id = f"workspace_{user_id}"
        join_room(room_id)
        emit('workspace_joined', {
            'success': True,
            'workspace': user_id,
            'room': room_id
        }, room=request.sid)
        logger.info(f"Cliente {request.sid} unido al workspace {user_id}")

    logger.info("Terminal xterm.js y colaboración en tiempo real inicializados")


def process_natural_language(text, model):
    """Procesa instrucciones en lenguaje natural y devuelve el comando correspondiente o una respuesta."""
    # Normalizar texto
    text = text.strip().lower()

    # Mapa de comandos comunes
    command_map = {
        "listar": "ls -la",
        "mostrar archivos": "ls -la",
        "directorio actual": "pwd",
        "donde estoy": "pwd",
        "crear directorio": "mkdir ",
        "crear carpeta": "mkdir ",
        "nueva carpeta": "mkdir ",
        "crear archivo": "touch ",
        "nuevo archivo": "touch ",
        "eliminar archivo": "rm ",
        "borrar archivo": "rm ",
        "eliminar carpeta": "rm -r ",
        "borrar carpeta": "rm -r ",
        "eliminar directorio": "rm -r ",
        "borrar directorio": "rm -r ",
        "mover": "mv ",
        "copiar": "cp ",
        "mostrar contenido": "cat ",
        "leer archivo": "cat ",
        "ver archivo": "cat ",
        "fecha actual": "date",
        "hora actual": "date",
        "crea un proyecto": "mkdir proyecto && echo '# Mi Proyecto' > proyecto/README.md",
        "procesos": "ps aux",
        "memoria": "free -h",
        "espacio en disco": "df -h",
    }

    # Respuestas para mensajes que no son comandos
    response_map = {
        "hola": "¡Hola! ¿En qué puedo ayudarte hoy? Puedo ayudarte a ejecutar comandos o a resolver dudas.",
        "ayuda": """Puedo ejecutar comandos como:
- listar archivos
- crear directorio [nombre]
- crear archivo [nombre]
- mostrar contenido [archivo]
- eliminar [archivo/directorio]
- mover [origen] [destino]
- copiar [origen] [destino]
- fecha actual
- procesos
- memoria
- espacio en disco""",
        "gracias": "¡De nada! Estoy aquí para ayudarte.",
        "adios": "¡Hasta luego! Vuelve cuando necesites ayuda.",
    }

    # Verificar primero si es un saludo o ayuda
    for key, response in response_map.items():
        if key in text:
            return None, response

    # Buscar coincidencias exactas primero
    if text in command_map:
        return command_map[text], None

    # Buscar coincidencias parciales
    for key, cmd in command_map.items():
        if key in text and cmd is not None:
            # Si el comando necesita un argumento
            if cmd.endswith(' '):
                # Extraer nombre después de palabras clave
                name_keywords = ["llamado", "llamada", "nombre", "llamados", "llamadas"]
                for keyword in name_keywords:
                    if keyword in text:
                        parts = text.split(keyword)
                        if len(parts) > 1:
                            # Obtener el primer argumento después de la palabra clave
                            arg = parts[1].strip().split()[0].strip('"\'')
                            return cmd + arg, None

                # Si no hay palabra clave, buscar la última palabra
                words = text.split()
                if len(words) > 1:
                    last_word = words[-1].strip('"\'')
                    # Verificar que la última palabra no sea parte del comando
                    if last_word not in key:
                        return cmd + last_word, None
            else:
                return cmd, None

    # Si es una pregunta, intentar dar una respuesta
    if any(q in text for q in ["qué", "cómo", "por qué", "cuál", "explica"]):
        return None, "Lo siento, no puedo responder a esa pregunta específica. Intenta preguntar sobre comandos o archivos."

    # Si no se reconoció ningún comando, devolver un mensaje
