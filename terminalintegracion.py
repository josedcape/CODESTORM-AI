
import os
import json
import logging
from flask import request, jsonify
import subprocess
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_user_workspace(user_id="default"):
    """Obtiene o crea un espacio de trabajo para el usuario."""
    workspace_root = Path("./user_workspaces")
    workspace_path = workspace_root / user_id
    if not workspace_path.exists():
        workspace_path.mkdir(parents=True, exist_ok=True)
        # Crear README inicial
        with open(workspace_path / "README.md", "w") as f:
            f.write("# Workspace\n\nEste es tu espacio de trabajo para el terminal integrado.")
    return workspace_path

def register_terminal_routes(app):
    """Registra las rutas relacionadas con la terminal en la aplicación Flask."""
    
    @app.route('/api/terminal/execute', methods=['POST'])
    def execute_terminal_command():
        """Ejecuta un comando en la terminal y devuelve el resultado."""
        try:
            data = request.json
            command = data.get('command', '')
            user_id = data.get('user_id', 'default')
            
            if not command:
                return jsonify({
                    'success': False,
                    'error': 'No se proporcionó ningún comando'
                }), 400
                
            # Obtener el workspace del usuario
            workspace_path = get_user_workspace(user_id)
            
            # Ejecutar el comando
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Preparar la respuesta
            response = {
                'success': process.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'exitCode': process.returncode,
                'workspace': str(workspace_path.relative_to(Path.cwd())),
                'currentDir': os.path.basename(workspace_path)
            }
            
            logging.debug(f"Comando ejecutado: '{command}', código: {process.returncode}")
            return jsonify(response)
            
        except Exception as e:
            logging.error(f"Error al ejecutar comando: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/terminal/files', methods=['GET'])
    def list_files_for_terminal():
        """Lista archivos y carpetas para la terminal integrada."""
        try:
            directory = request.args.get('directory', '.')
            user_id = request.args.get('user_id', 'default')
            
            # Obtener workspace
            workspace_path = get_user_workspace(user_id)
            
            # Construir ruta completa
            if directory == '.':
                target_dir = workspace_path
                relative_dir = '.'
            else:
                # Limpiar para evitar path traversal
                directory = directory.replace('..', '').strip('/')
                target_dir = workspace_path / directory
                relative_dir = directory
                
            # Verificar existencia
            if not target_dir.exists():
                return jsonify({
                    'success': False,
                    'error': 'Directorio no encontrado'
                }), 404
                
            # Listar contenido
            items = []
            for item in os.listdir(target_dir):
                item_path = target_dir / item
                
                if item_path.is_dir():
                    items.append({
                        'name': item,
                        'path': str(Path(relative_dir) / item),
                        'type': 'directory',
                        'size': 0,
                        'modified': os.path.getmtime(item_path)
                    })
                else:
                    items.append({
                        'name': item,
                        'path': str(Path(relative_dir) / item),
                        'type': 'file',
                        'size': os.path.getsize(item_path),
                        'modified': os.path.getmtime(item_path),
                        'extension': item_path.suffix[1:] if item_path.suffix else ''
                    })
                    
            return jsonify({
                'success': True,
                'path': relative_dir,
                'items': items
            })
            
        except Exception as e:
            logging.error(f"Error al listar archivos: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/terminal/file/content', methods=['GET'])
    def get_file_content_for_terminal():
        """Obtiene el contenido de un archivo para la terminal integrada."""
        try:
            file_path = request.args.get('path')
            user_id = request.args.get('user_id', 'default')
            
            if not file_path:
                return jsonify({
                    'success': False,
                    'error': 'Ruta de archivo no especificada'
                }), 400
                
            # Obtener workspace
            workspace_path = get_user_workspace(user_id)
            
            # Limpiar ruta para evitar path traversal
            file_path = file_path.replace('..', '').strip('/')
            target_file = workspace_path / file_path
            
            # Verificar existencia
            if not target_file.exists():
                return jsonify({
                    'success': False,
                    'error': 'Archivo no encontrado'
                }), 404
                
            if target_file.is_dir():
                return jsonify({
                    'success': False,
                    'error': 'La ruta especificada es un directorio'
                }), 400
                
            # Detectar si es binario
            try:
                with open(target_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    
                return jsonify({
                    'success': True,
                    'content': content,
                    'path': file_path,
                    'isBinary': False
                })
            except Exception as read_error:
                return jsonify({
                    'success': False,
                    'error': f'Error al leer archivo: {str(read_error)}'
                }), 500
                
        except Exception as e:
            logging.error(f"Error al obtener contenido: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    logging.info("Rutas de integración terminal-explorador registradas correctamente")
    return app
