import os
import re
import json
import logging
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import requests  # Usamos requests en lugar de aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'codestorm-secret-key')

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

@app.route('/api/files/delete', methods=['POST'])
def api_delete_file():
    """API para eliminar un archivo o directorio."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        file_path = data.get('file_path')
        
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
        
        # Verificar que el archivo o directorio existe
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'El archivo o directorio no existe'
            }), 404
        
        # Eliminar archivo o directorio
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'message': f"Se ha eliminado {file_path}"
        })
    except Exception as e:
        logger.error(f"Error al eliminar archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API para chat y generación de contenido
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API para chat con agentes especializados."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        message = data.get('message')
        agent_id = data.get('agent_id', 'general')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Se requiere un mensaje'
            }), 400
        
        # Respuesta simulada (en una implementación real, aquí se conectaría con el servicio de IA)
        agent_name = {
            'developer': "Desarrollador Experto",
            'architect': "Arquitecto de Software",
            'advanced': "Especialista Avanzado",
            'general': "Asistente General"
        }.get(agent_id, "Asistente General")
        
        response = f"Soy {agent_name}. He recibido tu mensaje: '{message}'. ¿En qué puedo ayudarte?"
        
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

@app.route('/api/process', methods=['POST'])
def process_instruction():
    """
    Procesa una instrucción en lenguaje natural para realizar acciones.
    
    La instrucción puede ser:
    - Crear un archivo
    - Ejecutar un comando
    - Modificar un archivo existente
    """
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        instruction = data.get('instruction')
        
        if not instruction:
            return jsonify({
                'success': False,
                'error': 'Se requiere una instrucción'
            }), 400
        
        workspace = get_user_workspace(user_id)
        
        # Simulación de procesamiento de lenguaje natural:
        # En una implementación real, aquí se conectaría con un modelo de IA
        
        # Detectar si la instrucción parece ser un comando
        if instruction.startswith('ejecuta ') or instruction.startswith('corre ') or instruction.startswith('run '):
            command = instruction.split(' ', 1)[1]
            
            # Ejecutar el comando
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
                'command': command,
                'result': stdout.decode('utf-8', errors='replace'),
                'error': stderr.decode('utf-8', errors='replace'),
                'status': status
            })
            
        # Detectar si la instrucción parece ser para crear un archivo
        elif 'crea' in instruction.lower() and ('archivo' in instruction.lower() or 'fichero' in instruction.lower()):
            # Extraer un nombre de archivo básico de la instrucción
            filename_match = re.search(r'(?:llamado|nombrado|nombre)\s+["\']?([^"\']+)["\']?', instruction)
            if filename_match:
                filename = filename_match.group(1)
            else:
                # Si no se encuentra un nombre específico, crear uno genérico
                extension = '.txt'
                if 'html' in instruction.lower(): extension = '.html'
                elif 'css' in instruction.lower(): extension = '.css'
                elif 'javascript' in instruction.lower() or 'js' in instruction.lower(): extension = '.js'
                elif 'python' in instruction.lower() or 'py' in instruction.lower(): extension = '.py'
                
                filename = f"nuevo_archivo{extension}"
            
            # Contenido básico según el tipo de archivo
            content = ""
            if filename.endswith('.html'):
                content = "<!DOCTYPE html>\n<html>\n<head>\n    <title>Nuevo documento</title>\n</head>\n<body>\n    <h1>Nuevo documento</h1>\n    <p>Contenido del documento.</p>\n</body>\n</html>"
            elif filename.endswith('.css'):
                content = "body {\n    margin: 0;\n    padding: 0;\n    font-family: Arial, sans-serif;\n}"
            elif filename.endswith('.js'):
                content = "// Archivo JavaScript\nconsole.log('Nuevo archivo JavaScript');"
            elif filename.endswith('.py'):
                content = "# Archivo Python\n\ndef main():\n    print('Hola mundo')\n\nif __name__ == '__main__':\n    main()"
            
            # Crear el archivo
            file_path = os.path.join(workspace, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({
                'success': True,
                'file_path': filename,
                'content': content,
                'result': f"Se ha creado el archivo '{filename}' con contenido básico."
            })
            
        else:
            # Respuesta genérica para instrucciones no reconocidas
            return jsonify({
                'success': True,
                'result': f"He recibido tu instrucción: '{instruction}'. " +
                          "Para ejecutar un comando, comienza con 'ejecuta'. " +
                          "Para crear un archivo, incluye 'crea archivo' en tu instrucción."
            })
            
    except Exception as e:
        logger.error(f"Error al procesar instrucción: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Verificar estado
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Aplicación funcionando correctamente'
    })

# Servir archivos estáticos
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos desde el directorio static."""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)