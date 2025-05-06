"""
Backend para el soporte de la terminal xterm.js y colaboración en tiempo real.
"""
import os
import json
import uuid
import logging
import subprocess
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit, join_room, leave_room
import traceback

xterm_bp = Blueprint('xterm', __name__, url_prefix='/xterm')

@xterm_bp.route('/xterm_terminal')
def xterm_terminal():
    """Render the XTerm terminal page."""
    # Asegurarse de que las rutas estén creadas
    os.makedirs('user_workspaces/default', exist_ok=True)

    # README inicial si está vacío
    readme_path = Path('user_workspaces/default/README.md')
    if not readme_path.exists():
        with open(readme_path, 'w') as f:
            f.write('# Workspace\n\nEste es tu espacio de trabajo colaborativo. Usa comandos o instrucciones en lenguaje natural para crear y modificar archivos.\n\nEjemplos:\n- "crea una carpeta llamada proyectos"\n- "mkdir proyectos"\n- "touch archivo.txt"')

    return render_template('xterm_terminal.html')

@xterm_bp.route('/api/xterm/execute', methods=['POST'])
def execute_xterm_command():
    """Execute a command in the terminal."""
    try:
        data = request.json
        command = data.get('command', '')

        if not command:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó comando'
            }), 400

        # Obtener directorio de trabajo
        workspace_dir = os.path.join(os.getcwd(), 'user_workspaces/default')
        os.makedirs(workspace_dir, exist_ok=True)

        # Ejecutar comando
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=workspace_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        return jsonify({
            'success': True,
            'stdout': stdout,
            'stderr': stderr,
            'exitCode': process.returncode
        })

    except Exception as e:
        logging.error(f"Error ejecutando comando XTerm: {str(e)}")
        logging.error(traceback.format_exc())
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

        # Obtener workspace
        workspace_dir = os.path.join(os.getcwd(), 'user_workspaces/default')
        full_path = os.path.join(workspace_dir, file_path)

        # Verificar seguridad de ruta
        if not os.path.normpath(full_path).startswith(os.path.normpath(workspace_dir)):
            return jsonify({
                'success': False,
                'error': 'Ruta no válida'
            }), 403

        # Eliminar archivo o directorio
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                import shutil
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
        logging.error(f"Error al eliminar archivo: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def init_xterm_blueprint(app, socketio):
    """Registra el blueprint en la aplicación Flask."""
    app.register_blueprint(xterm_bp, url_prefix='')
    # Registrar manejadores de eventos SocketIO después de inicializar el blueprint

    user_workspaces = {}

    def get_user_workspace(user_id):
        """Obtiene la ruta del workspace del usuario."""
        if user_id not in user_workspaces:
            user_workspaces[user_id] = Path('user_workspaces') / (user_id or 'default')
            os.makedirs(user_workspaces[user_id], exist_ok=True)

        return user_workspaces[user_id]

    @socketio.on('connect')
    def handle_connect():
        """Maneja la conexión de un cliente."""
        client_id = request.sid
        logging.info(f"Cliente conectado: {client_id}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Maneja la desconexión de un cliente."""
        client_id = request.sid
        logging.info(f"Cliente desconectado: {client_id}")

    @socketio.on('join_room')
    def handle_join(data):
        """Maneja la unión a una sala."""
        room = data.get('room')
        if room:
            join_room(room)
            emit('room_joined', {'success': True, 'room': room}, room=request.sid)
            logging.info(f"Cliente {request.sid} unido a la sala {room}")

    @socketio.on('bash_command')
    def handle_bash_command(data):
        """Ejecuta un comando bash y devuelve el resultado."""
        command = data.get('command', '')
        user_id = data.get('user_id', 'default')
        terminal_id = data.get('terminal_id', 'default') # Added terminal_id
        directory = data.get('directory', '.')

        logging.info(f"Comando recibido: '{command}' de usuario: {user_id}, terminal: {terminal_id}")

        if not command:
            emit('command_result', {
                'success': False,
                'command': '',
                'stderr': 'No se proporcionó ningún comando',
                'output': 'No se proporcionó ningún comando',
                'terminal_id': terminal_id # Added terminal_id
            }, room=request.sid)
            return

        try:
            # Obtener workspace del usuario
            workspace_path = get_user_workspace(user_id)

            # Construir ruta completa para el directorio actual
            if directory == '.':
                current_dir = workspace_path
            else:
                current_dir = workspace_path / directory

            # Ejecutar comando en esa ruta
            logging.debug(f"Ejecutando comando: '{command}' en directorio: {current_dir}")
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(current_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            # Emitir resultado
            result = {
                'success': process.returncode == 0,
                'command': command,
                'stdout': stdout,
                'stderr': stderr,
                'output': stdout if process.returncode == 0 else stderr,
                'terminal_id': terminal_id # Added terminal_id
            }
            logging.debug(f"Resultado del comando: {result['success']}")
            emit('command_result', result, room=request.sid)

            # Detectar cambios en archivos para notificar a todos los clientes
            if process.returncode == 0 and any(cmd in command for cmd in ['mkdir', 'touch', 'rm', 'cp', 'mv', 'echo', 'cat', 'nano', 'vim']):
                emit('file_change', {
                    'type': 'command',
                    'message': f'Comando ejecutado: {command}',
                    'command': command
                }, broadcast=True)

        except Exception as e:
            logging.error(f"Error al ejecutar comando: {str(e)}")
            emit('command_result', {
                'success': False,
                'command': command,
                'stderr': str(e),
                'output': f"Error: {str(e)}",
                'terminal_id': terminal_id # Added terminal_id
            }, room=request.sid)


    @socketio.on('natural_language')
    def handle_natural_language(data):
        """Procesa instrucciones en lenguaje natural de forma segura."""
        text = data.get('text', '')
        user_id = data.get('user_id', 'default')
        model = data.get('model', 'openai')
        directory = data.get('directory', '.')

        if not text:
            emit('instruction_result', {
                'success': False,
                'command': '',
                'error': 'No se proporcionó ningún texto',
                'explanation': 'Es necesario proporcionar una instrucción'
            }, room=request.sid)
            return

        try:
            # Procesar el texto usando el modelo seleccionado
            command = process_natural_language(text, model)

            # Emitir resultado con el comando sugerido pero sin ejecutarlo
            emit('instruction_result', {
                'success': True,
                'command': command,
                'explanation': f'Comando sugerido basado en: "{text}"',
                'auto_execute': False # Siempre falso para seguridad
            }, room=request.sid)

        except Exception as e:
            logging.error(f"Error al procesar lenguaje natural: {str(e)}")
            emit('instruction_result', {
                'success': False,
                'command': '',
                'error': str(e),
                'explanation': 'Error al procesar la instrucción'
            }, room=request.sid)

    @socketio.on('list_directory')
    def handle_list_directory(data):
        """Lista los contenidos de un directorio."""
        path = data.get('path', '.')
        user_id = data.get('user_id', 'default')

        try:
            # Obtener workspace del usuario
            workspace_path = get_user_workspace(user_id)

            # Construir ruta completa
            if path == '.':
                target_dir = workspace_path
            else:
                target_dir = workspace_path / path

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
                contents.append({
                    'name': item,
                    'is_directory': item_path.is_dir(),
                    'size': os.path.getsize(item_path) if item_path.is_file() else 0,
                    'modified': os.path.getmtime(item_path)
                })

            emit('directory_contents', {
                'success': True,
                'path': path,
                'contents': contents
            }, room=request.sid)

        except Exception as e:
            logging.error(f"Error al listar directorio: {str(e)}")
            emit('directory_contents', {
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

        if not room:
            return

        # Unirse a la sala si es join
        if action == 'join':
            join_room(room)
            emit('yjs', {
                'action': 'joined',
                'room': room
            }, room=request.sid)
            return

        # Reenviar el mensaje a todos en la sala excepto al emisor
        emit('yjs', {
            'action': action,
            'payload': payload
        }, room=room, skip_sid=request.sid)

    # Registrar eventos adicionales que se necesiten
    logging.info("Terminal xterm.js y colaboración en tiempo real inicializados")
    logging.info("XTerm terminal blueprint registered successfully")


def process_natural_language(text, model):
    """Procesa instrucciones en lenguaje natural y devuelve el comando correspondiente.  """
    #Se modifico para que solo devuelva comandos sin comentarios.
    command_map = {
        "listar": "ls -la",
        "mostrar archivos": "ls -la",
        "crear directorio": "mkdir ",
        "crear carpeta": "mkdir ",
        "crear archivo": "touch ",
        "eliminar": "rm ",
        "borrar": "rm ",
        "mover": "mv ",
        "copiar": "cp ",
        "mostrar contenido": "cat ",
        "leer archivo": "cat ",
        "crea un proyecto": "mkdir proyecto && echo '# Mi Proyecto' > proyecto/README.md",
    }

    # Buscar coincidencias exactas primero
    if text.lower() in command_map:
        command = command_map[text.lower()]
    else:
        # Buscar coincidencias parciales
        for key, cmd in command_map.items():
            if key in text.lower():
                command = cmd
                # Extraer nombres si es necesario
                if cmd in ["mkdir ", "touch ", "rm ", "mv ", "cp ", "cat "]:
                    parts = text.split()
                    for i, part in enumerate(parts):
                        if part.lower() in ["llamada", "llamado", "nombre"]:
                            if i + 1 < len(parts):
                                command += parts[i + 1]
                                break
                    # Si no se encontró un nombre específico y hay palabras después del comando
                    if command == cmd and len(parts) > 1:
                        # Usar la última palabra como nombre predeterminado
                        command += parts[-1]
                break
    if not command:
        command = "echo 'Comando no encontrado'" # Default command if no match

    return command

def process_natural_language_to_command(user_message):
    """Convierte lenguaje natural a comando directamente."""
    #Implementación simplificada - Requiere un NLP más robusto en un entorno real
    command = process_natural_language(user_message, 'openai') #usar el modelo openai por defecto
    return command