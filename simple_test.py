import os
import re
import json
import logging
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash
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
    
    # Asegurarnos de que el directorio exista
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Crear un archivo README.md si el workspace está vacío
    readme_path = os.path.join(workspace_dir, 'README.md')
    if not os.path.exists(readme_path) and len(os.listdir(workspace_dir)) == 0:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("""# Workspace de Usuario

Este es tu espacio de trabajo personal en CODESTORM Assistant.

## ¿Qué puedes hacer aquí?

- Crear nuevos archivos y carpetas
- Editar código con el asistente
- Ejecutar comandos y aplicaciones
- Gestionar tus proyectos

¡Comienza creando un nuevo archivo o preguntando al asistente cómo ayudarte!
""")
            
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
    
@app.route('/files')
def files():
    """Ruta al explorador de archivos."""
    return render_template('files.html')

@app.route('/code_corrector')
def code_corrector():
    """Ruta al corrector de código."""
    return render_template('code_corrector.html')

@app.route('/edit_file')
def edit_file():
    """Editar un archivo."""
    file_path = request.args.get('path', '')
    if not file_path:
        return redirect('/files')
    
    try:
        workspace = get_user_workspace()
        full_path = os.path.join(workspace, file_path)
        
        # Verificar path traversal
        if not os.path.normpath(full_path).startswith(os.path.normpath(workspace)):
            flash('Ruta de archivo inválida', 'danger')
            return redirect('/files')
        
        # Verificar que el archivo existe
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            flash('El archivo no existe', 'danger')
            return redirect('/files')
        
        # Leer el archivo
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Determinar el tipo de archivo
        file_type = os.path.splitext(file_path)[1].lstrip('.').upper() or 'TXT'
        
        return render_template('editor.html', file_path=file_path, file_content=content, file_type=file_type)
    except Exception as e:
        logger.error(f"Error al editar archivo: {str(e)}")
        flash(f'Error al abrir el archivo: {str(e)}', 'danger')
        return redirect('/files')

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

@app.route('/api/save_file', methods=['POST'])
def save_file():
    """Guarda cambios en un archivo."""
    try:
        data = request.json
        file_path = data.get('file_path')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Se requiere ruta de archivo'
            }), 400
        
        workspace = get_user_workspace()
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
            'file_path': file_path,
            'message': 'Archivo guardado correctamente'
        })
    except Exception as e:
        logger.error(f"Error al guardar archivo: {str(e)}")
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

# API para análisis de código
@app.route('/api/analyze_code', methods=['POST'])
def process_code():
    """API para analizar código con instrucciones específicas."""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        code = data.get('code')
        language = data.get('language', 'python')
        instructions = data.get('instructions', '')
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Se requiere código para analizar'
            }), 400
        
        # En una implementación real, aquí se conectaría con un servicio de IA
        # para analizar el código. Para esta versión simplificada, simulamos una respuesta.
        
        # Análisis básico de código
        improved_code = code
        explanations = ["El código se ve bien estructurado."]
        suggestions = ["Considera añadir comentarios para mejorar la legibilidad."]
        
        # Respuestas según el lenguaje
        if language == 'python':
            if 'def ' in code and not code.strip().startswith('def '):
                explanations.append("Has definido funciones correctamente.")
            if 'import ' in code:
                suggestions.append("Verifica que todas las importaciones sean necesarias para tu código.")
            if 'while ' in code and 'break' not in code:
                suggestions.append("Considera añadir una condición de salida en tu bucle while para evitar bucles infinitos.")
                
        elif language == 'javascript':
            if 'function ' in code:
                explanations.append("Has definido funciones correctamente.")
            if 'var ' in code:
                suggestions.append("Considera usar 'let' o 'const' en lugar de 'var' para una mejor gestión de ámbito.")
            if 'console.log' in code:
                suggestions.append("Recuerda eliminar las declaraciones console.log en código de producción.")
                
        # Mejoras simuladas basadas en instrucciones
        if instructions:
            if 'optimizar' in instructions.lower() or 'rendimiento' in instructions.lower():
                suggestions.append("Para optimizar el rendimiento, considera utilizar estructuras de datos más eficientes.")
                explanations.append("El rendimiento podría mejorarse reduciendo las operaciones redundantes.")
            
            if 'seguridad' in instructions.lower():
                suggestions.append("Para mejorar la seguridad, valida todas las entradas del usuario.")
                explanations.append("Es importante proteger tu código contra entradas maliciosas.")
        
        # Simulamos mejoras en el código para casos específicos
        if language == 'python' and 'fibonacci' in code.lower() and 'def fibonacci' in code.lower():
            if 'fibonacci(n-1) + fibonacci(n-2)' in code:
                improved_code = code.replace('def fibonacci(n):', 'def fibonacci(n):  # Versión optimizada')
                improved_code = improved_code.replace('    if n <= 0:', '    # Verificación de entrada\n    if n <= 0:')
                improved_code = improved_code.replace('    elif n == 1:', '    elif n == 1:')
                improved_code = improved_code.replace('    else:\n        return fibonacci(n-1) + fibonacci(n-2)', 
                                                   '    else:\n        # Usamos enfoque iterativo para mejor rendimiento\n'
                                                   '        a, b = 0, 1\n        for _ in range(2, n + 1):\n'
                                                   '            a, b = b, a + b\n        return b')
                
                explanations = ["Tu implementación usa recursión, lo que puede llevar a desbordamiento de pila para valores grandes.",
                               "La función recursiva tiene complejidad de tiempo O(2^n), que es exponencial.",
                               "La implementación iterativa propuesta tiene complejidad O(n), mucho más eficiente."]
                
                suggestions = ["Utiliza el enfoque iterativo para mejorar el rendimiento.",
                              "Añade validación de entrada para manejar valores negativos.",
                              "Considera implementar memoización si necesitas mantener el enfoque recursivo."]
        
        return jsonify({
            'success': True,
            'improved_code': improved_code,
            'explanations': explanations,
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"Error al analizar código: {str(e)}")
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
        model = data.get('model', 'openai')
        agent_id = data.get('agent_id', 'general')
        
        if not instruction:
            return jsonify({
                'success': False,
                'error': 'Se requiere una instrucción'
            }), 400
        
        logger.info(f"Procesando instrucción con modelo: {model}, agente: {agent_id}")
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
                'result': f"He recibido tu instrucción: '{instruction}'. "
                          "Para ejecutar un comando, comienza con 'ejecuta'. "
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

@app.route('/workspace/<path:filename>')
def serve_workspace_file(filename):
    """Servir archivos desde el workspace del usuario."""
    return send_from_directory('user_workspaces/default', filename)

# Esta ruta ya existe en otra parte del código, eliminamos esta duplicada

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)