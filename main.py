from flask import Flask, render_template, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
import os
import logging
import json
import re
from dotenv import load_dotenv
import openai
import requests
import traceback
import time
import subprocess
import shutil
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from intelligent_terminal import init_terminal

# Load environment variables with force reload
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")  # Inicializar Socket.IO

# Set session secret
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Verificar y cargar explícitamente las claves API
openai_api_key = os.environ.get('OPENAI_API_KEY')
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
gemini_api_key = os.environ.get('GEMINI_API_KEY')

if openai_api_key:
    # Configurar la API key de OpenAI
    openai.api_key = openai_api_key
    logging.info(f"OpenAI API key configurada: {openai_api_key[:5]}...{openai_api_key[-5:]}")
else:
    logging.warning("OPENAI_API_KEY no encontrada")

if anthropic_api_key:
    logging.info(f"Anthropic API key configurada: {anthropic_api_key[:5]}...{anthropic_api_key[-5:]}")
else:
    logging.warning("ANTHROPIC_API_KEY no encontrada")

if gemini_api_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        logging.info(f"Gemini API key configurada: {gemini_api_key[:5]}...{gemini_api_key[-5:]}")
    except ImportError as ie:
        logging.error(f"Error al importar módulos para Gemini: {str(ie)}")
    except Exception as e:
        logging.error(f"Error al configurar Gemini API: {str(e)}")
else:
    logging.warning("GEMINI_API_KEY no encontrada")


# Initialize API clients with error handling
openai_client = None
if openai_api_key:
    try:
        openai.api_key = openai_api_key
        openai_client = openai.OpenAI()
        logging.info("OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {str(e)}")

@app.route('/')
def index():
    """Render the main page or redirect to terminal."""
    # Para simplificar, también podemos redireccionar directamente a la terminal
    # Descomenta la siguiente línea para redireccionar directamente
    # return redirect('/terminal')
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')

@app.route('/files')
def files():
    """Render the files explorer page."""
    return render_template('files.html')

@app.route('/code_corrector')
def code_corrector():
    """Render the code corrector page."""
    return render_template('code_corrector.html')

@app.route('/preview')
def preview():
    """Render the preview page."""
    return render_template('preview.html')

@app.route('/terminal')
def terminal():
    """Render the Monaco terminal page."""
    # Asegurarse de que las rutas estén creadas
    os.makedirs('user_workspaces/default', exist_ok=True)
    # README inicial si está vacío
    readme_path = os.path.join('user_workspaces/default', 'README.md')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write('# Workspace\n\nEste es tu espacio de trabajo. Usa comandos o instrucciones en lenguaje natural para crear y modificar archivos.\n\nEjemplos:\n- "crea una carpeta llamada proyectos"\n- "mkdir proyectos"\n- "touch archivo.txt"')

    return render_template('monaco_terminal.html')

# Ruta alternativa para la terminal Monaco (mantenemos para compatibilidad)
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

        if not code:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó código para procesar'
            }), 400

        # Verificar qué modelo usar
        if model == 'openai' and openai_client:
            try:
                # Usar OpenAI para corregir el código
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"Eres un experto programador. Tu tarea es corregir el siguiente código en {language} según las instrucciones proporcionadas. El código resultante debe ser limpio, optimizado y SIN COMENTARIOS explicativos dentro del código. Devuelve el código corregido, una lista de cambios realizados y una explicación clara separada del código."},
                        {"role": "user", "content": f"CÓDIGO:\n```{language}\n{code}\n```\n\nINSTRUCCIONES:\n{instructions}\n\nResponde en formato JSON con las siguientes claves:\n- correctedCode: el código corregido completo sin comentarios explicativos\n- changes: una lista de objetos, cada uno con 'description' y 'lineNumbers'\n- explanation: una explicación detallada de los cambios"}
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
                # Importar anthropic si es necesario
                import anthropic
                from anthropic import Anthropic

                # Inicializar cliente
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

                # Extraer la respuesta de Claude en formato JSON
                try:
                    # Primero intentamos ver si toda la respuesta es JSON directamente
                    result = json.loads(response.content[0].text.strip())
                except json.JSONDecodeError:
                    # Si no es JSON válido, buscamos dentro de bloques de código
                    import re
                    # Buscar JSON dentro de un bloque de código markdown
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response.content[0].text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1).strip())
                        except json.JSONDecodeError:
                            # Si aún falla, creamos una estructura básica con la respuesta completa
                            result = {
                                "correctedCode": code,  # Mantener código original
                                "changes": [{"description": "No se pudieron procesar los cambios correctamente", "lineNumbers": [1]}],
                                "explanation": "Error al procesar la respuesta de Claude. Respuesta recibida: " + response.content[0].text[:200] + "..."
                            }
                    else:
                        # Si no encontramos bloques JSON, construimos una respuesta informativa
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for the application."""
    try:
        # Check API configurations
        apis = {
            "openai": "ok" if os.environ.get('OPENAI_API_KEY') else "not configured",
            "anthropic": "ok" if os.environ.get('ANTHROPIC_API_KEY') else "not configured",
            "gemini": "ok" if os.environ.get('GEMINI_API_KEY') else "not configured"
        }

        return jsonify({
            "status": "ok",
            "timestamp": time.time(),
            "version": "1.0.0",
            "apis": apis
        })
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

def get_user_workspace(user_id='default'):
    """Obtiene o crea un espacio de trabajo para el usuario."""
    workspace_dir = os.path.join(os.getcwd(), 'user_workspaces', user_id)
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir

@app.route('/api/files', methods=['GET'])
def list_files():
    """API para listar archivos del workspace del usuario."""
    try:
        directory = request.args.get('directory', '.')
        user_id = request.args.get('user_id', 'default')

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa
        if directory == '.':
            full_directory = user_workspace
            relative_dir = '.'
        else:
            # Limpiar la ruta para evitar path traversal
            directory = directory.replace('..', '').strip('/')
            full_directory = os.path.join(user_workspace, directory)
            relative_dir = directory

        # Verificar que el directorio existe
        if not os.path.exists(full_directory):
            # Si no existe pero es la raíz, lo creamos
            if directory == '.':
                os.makedirs(full_directory, exist_ok=True)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Directorio no encontrado'
                }), 404

        # Listar archivos y carpetas
        files = []
        try:
            for item in os.listdir(full_directory):
                item_path = os.path.join(full_directory, item)
                relative_path = os.path.join(relative_dir, item) if relative_dir != '.' else item

                # Extraer extensión del archivo
                extension = os.path.splitext(item)[1].lower()[1:] if os.path.isfile(item_path) and '.' in item else ''

                if os.path.isdir(item_path):
                    files.append({
                        'name': item,
                        'path': relative_path,
                        'type': 'directory',
                        'size': 0,
                        'modified': os.path.getmtime(item_path),
                        'extension': ''
                    })
                else:
                    file_size = os.path.getsize(item_path)
                    files.append({
                        'name': item,
                        'path': relative_path,
                        'type': 'file',
                        'size': file_size,
                        'modified': os.path.getmtime(item_path),
                        'extension': extension
                    })
        except Exception as e:
            logging.error(f"Error al listar archivos: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al listar archivos: {str(e)}'
            }), 500

        return jsonify({
            'success': True,
            'files': files,
            'directory': relative_dir
        })
    except Exception as e:
        logging.error(f"Error en endpoint de archivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/read', methods=['GET'])
def read_file():
    """API para leer el contenido de un archivo en el workspace del usuario."""
    try:
        file_path = request.args.get('file_path')
        user_id = request.args.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa y limpiar para evitar path traversal
        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        # Verificar que el archivo existe
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        if os.path.isdir(full_path):
            return jsonify({
                'success': False,
                'error': 'La ruta especificada es un directorio'
            }), 400

        # Leer contenido del archivo con manejo de errores para archivos binarios
        try:
            # Detectar si es un archivo binario (imágenes, etc.)
            is_binary = False
            binary_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'zip', 'pdf', 'doc', 'docx', 'xls', 'xlsx']
            file_ext = os.path.splitext(file_path)[1].lower()[1:] if '.' in file_path else ''

            if file_ext in binary_extensions:
                is_binary = True
                return jsonify({
                    'success': True,
                    'is_binary': True,
                    'file_path': file_path,
                    'file_url': f'/api/files/download?file_path={file_path}&user_id={user_id}'
                })

            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return jsonify({
                'success': True,
                'content': content,
                'file_path': file_path,
                'is_binary': False
            })
        except Exception as e:
            logging.error(f"Error al leer archivo: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al leer archivo: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error en endpoint de lectura de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/create', methods=['POST'])
def create_file():
    """API para crear un archivo o directorio en el workspace del usuario."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        file_path = data.get('file_path')
        content = data.get('content', '')
        is_directory = data.get('is_directory', False)
        user_id = data.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa y limpiar para evitar path traversal
        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        # Verificar si ya existe
        if os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': f'Ya existe un{"a carpeta" if is_directory else " archivo"} con ese nombre'
            }), 400

        try:
            if is_directory:
                # Crear directorio
                os.makedirs(full_path, exist_ok=True)
                message = f'Directorio {file_path} creado exitosamente'
            else:
                # Crear directorio padre si no existe
                parent_dir = os.path.dirname(full_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)

                # Crear archivo
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                message = f'Archivo {file_path} creado exitosamente'

            return jsonify({
                'success': True,
                'message': message,
                'file_path': file_path,
                'is_directory': is_directory
            })
        except Exception as e:
            logging.error(f"Error al crear archivo/directorio: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al crear: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error en endpoint de creación: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/delete', methods=['DELETE'])
def delete_file():
    """API para eliminar un archivo o directorio del workspace del usuario."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        file_path = data.get('file_path')
        user_id = data.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa y limpiar para evitar path traversal
        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        # Verificar que el archivo existe
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo o directorio no encontrado'
            }), 404

        try:
            # Eliminar archivo o directorio
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                message = f'Directorio {file_path} eliminado exitosamente'
            else:
                os.remove(full_path)
                message = f'Archivo {file_path} eliminado exitosamente'

            return jsonify({
                'success': True,
                'message': message,
                'file_path': file_path,
                'is_directory': os.path.isdir(full_path)
            })
        except Exception as e:
            logging.error(f"Error al eliminar: {str(e)}")
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

@app.route('/api/files/download', methods=['GET'])
def download_file():
    """API para descargar un archivo desde el workspace del usuario."""
    try:
        file_path = request.args.get('file_path')
        user_id = request.args.get('user_id', 'default')

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa y limpiar para evitar path traversal
        file_path = file_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, file_path)

        # Verificar que el archivo existe
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404

        if os.path.isdir(full_path):
            return jsonify({
                'success': False,
                'error': 'La ruta especificada es un directorio. Use api/files/download-dir para descargar directorios.'
            }), 400

        # Enviar el archivo para descarga
        return send_from_directory(
            os.path.dirname(full_path),
            os.path.basename(full_path),
            as_attachment=True
        )

    except Exception as e:
        logging.error(f"Error en descarga de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/download-dir', methods=['GET'])
def download_directory():
    """API para descargar un directorio como ZIP desde el workspace del usuario."""
    try:
        dir_path = request.args.get('dir_path')
        user_id = request.args.get('user_id', 'default')

        if not dir_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de directorio'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta completa y limpiar para evitar path traversal
        dir_path = dir_path.replace('..', '').strip('/')
        full_path = os.path.join(user_workspace, dir_path)

        # Verificar que el directorio existe
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'error': 'Directorio no encontrado'
            }), 404

        if not os.path.isdir(full_path):
            return jsonify({
                'success': False,
                'error': 'La ruta especificada no es un directorio'
            }), 400

        # Crear archivo ZIP en memoria
        import io
        import zipfile

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Recorrer el directorio recursivamente
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_path)
                    zipf.write(file_path, arcname)

        # Mover el puntero al inicio del archivo
        memory_file.seek(0)

        # Crear nombre para el archivo ZIP
        zip_filename = f"{os.path.basename(dir_path)}.zip"

        # Devolver el archivo ZIP
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        logging.error(f"Error en descarga de directorio: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """API para subir un archivo al workspace del usuario."""
    try:
        user_id = request.form.get('user_id', 'default')
        directory = request.form.get('directory', '.')

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó archivo'
            }), 400

        uploaded_file = request.files['file']

        if uploaded_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nombre de archivo vacío'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Construir ruta destino
        directory = directory.replace('..', '').strip('/')
        target_dir = os.path.join(user_workspace, directory)

        # Crear directorio destino si no existe
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # Guardar archivo con nombre seguro
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(target_dir, filename)

        uploaded_file.save(file_path)

        relative_path = os.path.join(directory, filename) if directory != '.' else filename

        return jsonify({
            'success': True,
            'message': f'Archivo {filename} subido exitosamente',
            'file_path': relative_path
        })

    except Exception as e:
        logging.error(f"Error en subida de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/repo/clone', methods=['POST'])
def clone_repository():
    """API para clonar un repositorio Git en el workspace del usuario."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        repo_url = data.get('repo_url')
        user_id = data.get('user_id', 'default')
        target_dir = data.get('target_dir')

        if not repo_url:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó URL del repositorio'
            }), 400

        # Obtener el workspace del usuario
        user_workspace = get_user_workspace(user_id)

        # Si no se especifica directorio destino, usar el nombre del repositorio
        if not target_dir:
            # Extraer nombre del repositorio de la URL
            repo_name = repo_url.split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_dir = repo_name

        # Limpiar ruta destino
        target_dir = target_dir.replace('..', '').strip('/')
        full_target_path = os.path.join(user_workspace, target_dir)

        # Verificar si ya existe
        if os.path.exists(full_target_path):
            return jsonify({
                'success': False,
                'error': f'Ya existe un directorio con el nombre {target_dir}'
            }), 400

        # Crear directorio padre si no existe
        os.makedirs(os.path.dirname(full_target_path), exist_ok=True)

        # Instalar git si no está instalado
        try:
            subprocess.run(['git', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            return jsonify({
                'success': False,
                'error': 'Git no está instalado en el sistema'
            }), 500

        # Clonar el repositorio con manejo de errores mejorado
        try:
            process = subprocess.run(
                ['git', 'clone', repo_url, full_target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if process.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Error al ejecutar comando: {process.stderr}'
                }), 500

            # Procesamos la salida del comando como respuesta
            stdout_response = process.stdout

            logging.info(f"Repositorio clonado exitosamente: {repo_url} -> {full_target_path}")

            return jsonify({
                'success': True,
                'message': f'Repositorio clonado exitosamente en {target_dir}',
                'output': stdout_response,
                'target_dir': target_dir
            })
        except Exception as e:
            logging.error(f"Error al ejecutar git clone: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error al clonar repositorio: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error al clonar repositorio: {str(e)}")
        logging.error(traceback.format_exc())  # Añadir traza completa para mejor depuración
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def extract_json_from_gemini(text):
    """Extrae JSON de una respuesta de Gemini."""
    import re
    json_match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            return {"correctedCode": "", "changes": [], "explanation": "Error al procesar la respuesta JSON de Gemini."}
    else:
        return {"correctedCode": "", "changes": [], "explanation": "No se encontró JSON en la respuesta de Gemini."}

def extract_json_from_gemini(text):
    """Extrae JSON de una respuesta de Gemini."""
    import re
    json_match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            return {"correctedCode": "", "changes": [], "explanation": "Error al procesar la respuesta JSON de Gemini."}
    else:
        return {"correctedCode": "", "changes": [], "explanation": "No se encontró JSON en la respuesta de Gemini."}

def extract_json_from_claude(text):
    """Extrae JSON de una respuesta de Claude."""
    import re
    try:
        # Primero intentamos ver si toda la respuesta es JSON directamente
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # Si no es JSON válido, buscamos dentro de bloques de código
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                # Si aún falla, creamos una estructura básica con la respuesta completa
                return {
                    "correctedCode": "",
                    "changes": [],
                    "explanation": "Error al procesar la respuesta JSON. Respuesta recibida: " + text[:200] + "..."
                }
        else:
            # Si no encontramos bloques JSON, construimos una respuesta informativa
            return {
                "correctedCode": "",
                "changes": [],
                "explanation": "No se encontró formato JSON en la respuesta. Intente de nuevo o use otro modelo."
            }```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                # Si aún falla, creamos una estructura básica con la respuesta completa
                return {
                    "correctedCode": "",
                    "changes": [],
                    "explanation": "Error al procesar la respuesta JSON de Claude. Respuesta recibida: " + text[:200] + "..."
                }
        else:
            # Si no encontramos bloques JSON, construimos una respuesta informativa
            return {
                "correctedCode": "",
                "changes": [],
                "explanation": "Claude no respondió en el formato esperado. Intente de nuevo o use otro modelo."
            }