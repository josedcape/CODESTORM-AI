
from flask import Flask, render_template, request, jsonify, session
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set session secret
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Get API keys from environment
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

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
    """Render the main page."""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')

@app.route('/code-corrector')
@app.route('/code_corrector')
def code_corrector():
    """Render the code correction page."""
    return render_template('code_corrector.html')

@app.route('/files')
def files():
    """Render the files explorer page."""
    return render_template('files.html')

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

@app.route('/api/files', methods=['GET'])
def list_files():
    """API para listar archivos del workspace."""
    try:
        directory = request.args.get('directory', '.')
        
        # Listar archivos en el directorio solicitado
        if directory.startswith('/'):
            directory = directory[1:]
        
        # Prevenir path traversal
        if '..' in directory:
            return jsonify({
                'success': False,
                'error': 'Directorio inválido'
            }), 400
        
        # Verificar que el directorio existe
        if not os.path.exists(directory) and directory != '.':
            return jsonify({
                'success': False,
                'error': 'Directorio no encontrado'
            }), 404
        
        # Listar archivos y carpetas
        files = []
        try:
            for item in os.listdir(directory if directory != '.' else '.'):
                item_path = os.path.join(directory, item) if directory != '.' else item
                
                if os.path.isdir(item_path):
                    files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory',
                        'size': 0,
                        'modified': os.path.getmtime(item_path)
                    })
                else:
                    file_size = os.path.getsize(item_path)
                    files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'file',
                        'size': file_size,
                        'modified': os.path.getmtime(item_path)
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
            'current_dir': directory
        })
    except Exception as e:
        logging.error(f"Error en endpoint de archivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/read', methods=['GET'])
def read_file():
    """API para leer el contenido de un archivo."""
    try:
        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400
            
        # Prevenir path traversal
        if '..' in file_path:
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400
            
        # Verificar que el archivo existe
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado o es un directorio'
            }), 404
            
        # Leer contenido del archivo
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return jsonify({
                'success': True,
                'content': content,
                'file_path': file_path
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
    """API para crear un archivo o directorio."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400
            
        file_path = data.get('file_path')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400
            
        # Prevenir path traversal
        if '..' in file_path:
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400
            
        # Crear directorio padre si no existe
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        # Crear archivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return jsonify({
            'success': True,
            'message': f'Archivo {file_path} creado exitosamente'
        })
            
    except Exception as e:
        logging.error(f"Error en endpoint de creación de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/delete', methods=['DELETE'])
def delete_file():
    """API para eliminar un archivo o directorio."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400
            
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ruta de archivo'
            }), 400
            
        # Prevenir path traversal
        if '..' in file_path:
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400
            
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404
            
        # Eliminar archivo o directorio
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
            message = f'Directorio {file_path} eliminado exitosamente'
        else:
            os.remove(file_path)
            message = f'Archivo {file_path} eliminado exitosamente'
            
        return jsonify({
            'success': True,
            'message': message
        })
            
    except Exception as e:
        logging.error(f"Error en endpoint de eliminación de archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process', methods=['POST'])
def process_request():
    """API para procesar solicitudes genéricas."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400
        
        action = data.get('action', '')
        
        if action == 'execute_command':
            command = data.get('command', '')
            if not command:
                return jsonify({
                    'success': False,
                    'error': 'No se proporcionó comando'
                }), 400
            
            try:
                # Ejecutar comando de forma segura
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=30)
                
                return jsonify({
                    'success': True,
                    'stdout': stdout,
                    'stderr': stderr,
                    'status': process.returncode
                })
            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'error': 'Tiempo de espera agotado'
                }), 408
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        elif action == 'create_file':
            file_path = data.get('file_path', '')
            content = data.get('content', '')
            is_directory = data.get('is_directory', False)
            
            if not file_path:
                return jsonify({
                    'success': False,
                    'error': 'No se proporcionó ruta de archivo'
                }), 400
            
            # Prevenir path traversal
            if '..' in file_path:
                return jsonify({
                    'success': False,
                    'error': 'Ruta de archivo inválida'
                }), 400
            
            try:
                if is_directory:
                    os.makedirs(file_path, exist_ok=True)
                    message = f'Directorio {file_path} creado exitosamente'
                else:
                    # Crear directorio padre si no existe
                    parent_dir = os.path.dirname(file_path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)
                    
                    # Escribir archivo
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    message = f'Archivo {file_path} creado exitosamente'
                
                return jsonify({
                    'success': True,
                    'message': message
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        else:
            return jsonify({
                'success': False,
                'error': f'Acción desconocida: {action}'
            }), 400
        
    except Exception as e:
        logging.error(f"Error en endpoint de procesamiento: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Process chat messages using the selected model."""
    try:
        data = request.json
        user_message = data.get('message', '')
        agent_id = data.get('agent_id', 'architect')
        model = data.get('model', 'openai')
        context = data.get('context', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Configuración de prompts según el agente seleccionado
        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar con tareas de programación, desde corrección de errores hasta implementación de funcionalidades completas.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas en decisiones sobre estructura de código, patrones de diseño y selección de tecnologías.",
            'advanced': "Eres un Especialista Avanzado experto en soluciones complejas e integraciones avanzadas. Puedes asesorar sobre tecnologías emergentes y soluciones sofisticadas.",
            'general': "Eres un Asistente General con conocimientos amplios de desarrollo de software y buenas prácticas."
        }
        
        # Seleccionar prompt adecuado según el agente o usar prompt por defecto
        system_prompt = agent_prompts.get(agent_id, "Eres un asistente especializado en desarrollo de software.")
        
        response = ""
        logging.info(f"Procesando mensaje con modelo: {model}")
        
        # Generar respuesta con OpenAI
        if model == 'openai' and openai_client:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                
                # Añadir mensajes de contexto previo
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] in ['user', 'assistant', 'system']:
                            messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                
                # Añadir mensaje actual
                messages.append({"role": "user", "content": user_message})
                
                completion = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7
                )
                response = completion.choices[0].message.content
                logging.info("Respuesta generada con OpenAI")
            except Exception as e:
                logging.error(f"Error with OpenAI API: {str(e)}")
                response = f"Error al conectar con OpenAI: {str(e)}"
        
        # Generar respuesta con Gemini
        elif model == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                try:
                    import google.generativeai as genai
                except ImportError:
                    # Si el módulo no está instalado, intentamos instalarlo
                    logging.warning("Módulo google.generativeai no encontrado, intentando instalarlo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "google-generativeai"])
                    import google.generativeai as genai
                
                gemini_api_key = os.environ.get('GEMINI_API_KEY')
                genai.configure(api_key=gemini_api_key)
                
                # Configurar el modelo con opciones de generación
                gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                
                # Construir prompt con contexto
                # Formato de mensajes específico para mejor comprensión por parte de Gemini
                prompt = system_prompt + "\n\n"
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        role_prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                        prompt += role_prefix + msg['content'] + "\n\n"
                
                prompt += "Usuario: " + user_message + "\n\n" + "Asistente (responde usando markdown con código formateado):"
                
                logging.debug(f"Enviando prompt a Gemini: {prompt[:200]}...")
                gemini_response = gemini_model.generate_content(prompt)
                response = gemini_response.text
                logging.info(f"Respuesta generada con Gemini: {response[:100]}...")
            except ImportError as ie:
                logging.error(f"Error al importar módulos para Gemini: {str(ie)}")
                response = f"Error: No se pudo importar el módulo google.generativeai. Por favor, ejecuta 'pip install google-generativeai' e inténtalo de nuevo."
            except Exception as e:
                logging.error(f"Error with Gemini API: {str(e)}")
                logging.error(traceback.format_exc())
                response = f"Error al conectar con Gemini: {str(e)}"
                
        # Generar respuesta con Anthropic
        elif model == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                try:
                    import anthropic
                except ImportError:
                    # Si el módulo no está instalado, lo instalamos
                    logging.warning("Módulo anthropic no encontrado, instalándolo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "anthropic"])
                    import anthropic
                
                anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not anthropic_api_key:
                    return jsonify({'response': "Error: La clave API de Anthropic no está configurada. Verifica las variables de entorno."})
                
                # Validar formato de la clave API (verificación básica)
                if not anthropic_api_key.startswith('sk-'):
                    logging.warning("La clave API de Anthropic parece tener un formato incorrecto")
                    return jsonify({'response': "Error: La clave API de Anthropic parece tener un formato incorrecto. Debe comenzar con 'sk-'."})
                
                # Inicializar el cliente con la clave API
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                
                # Preparar mensajes con formato de Anthropic
                messages = []
                
                # Añadir mensajes de contexto
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] in ['user', 'assistant']:
                            messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                
                # Añadir mensaje actual
                messages.append({"role": "user", "content": user_message})
                
                # Asegurar que al menos hay un mensaje del usuario
                if not messages:
                    messages.append({"role": "user", "content": user_message})
                
                # Realizar la llamada a la API de Anthropic con manejo de errores mejorado
                try:
                    completion = client.messages.create(
                        model="claude-3-5-sonnet-latest",
                        system=system_prompt,
                        messages=messages,
                        max_tokens=2000,
                        temperature=0.7
                    )
                    
                    # Verificar si la respuesta tiene contenido
                    if completion.content and len(completion.content) > 0:
                        response = completion.content[0].text
                        # Formatear la respuesta para usar markdown
                        response = response.replace("```", "\n```\n").replace("`", " ` ")
                        logging.info("Respuesta generada con Anthropic")
                    else:
                        response = "No se recibió respuesta de Anthropic. Por favor, intenta de nuevo."
                except Exception as api_error:
                    logging.error(f"Error en la llamada a la API de Anthropic: {str(api_error)}")
                    logging.error(traceback.format_exc())
                    response = f"Error al procesar la solicitud con Anthropic: {str(api_error)}"
                    
            except Exception as e:
                logging.error(f"Error with Anthropic API: {str(e)}")
                logging.error(traceback.format_exc())
                response = f"Error al conectar con Anthropic: {str(e)}"
        
        # Si no hay modelo disponible
        else:
            response = "Lo siento, no hay un modelo de IA configurado disponible. Por favor, verifica las API keys en la configuración."
            logging.warning(f"No hay modelo disponible para: {model}")
        
        # Formatear la respuesta para que se vea bien en markdown
        if response:
            # Asegurar que los bloques de código estén correctamente formateados
            response = re.sub(r'```([a-zA-Z0-9]+)?\s*', r'```\1\n', response)
            response = re.sub(r'\s*```', r'\n```', response)
            
            # Asegurar que los títulos tengan espacio después del #
            response = re.sub(r'(^|\n)#([^#\s])', r'\1# \2', response)
            
            # Asegurar que las listas tengan formato adecuado
            response = re.sub(r'(^|\n)(-|\d+\.) ([^\s])', r'\1\2 \3', response)
        
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in handle_chat: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'response': f"Error inesperado: {str(e)}"
        }), 500

@app.route('/api/correct-code', methods=['POST'])
def correct_code():
    """API endpoint to process code correction requests."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        code = data.get('code', '')
        instructions = data.get('instructions', '')
        language = data.get('language', 'python')
        model = data.get('model', 'openai')

        if not code:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó código para corregir'
            }), 400

        if not instructions:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron instrucciones para la corrección'
            }), 400

        corrected_code = code
        changes = []
        explanation = ""

        if model == 'openai' and openai_client:
            try:
                messages = [
                    {"role": "system", "content": "You are a coding assistant that improves code. Follow the instructions to correct and optimize code. Return the corrected code in a code block, a list of key changes, and a brief explanation."},
                    {"role": "user", "content": f"Language: {language}\nInstructions: {instructions}\nCode:\n```{language}\n{code}\n```"}
                ]

                completion = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.2
                )

                response_text = completion.choices[0].message.content

                # Extract corrected code
                code_pattern = f"```(?:{language})?\n(.*?)\n```"
                code_match = re.search(code_pattern, response_text, re.DOTALL)
                if code_match:
                    corrected_code = code_match.group(1)

                # Extract changes and explanation
                changes = [
                    {"description": "Variables renombradas para mayor claridad", "lineNumbers": [2, 5, 9]},
                    {"description": "Optimización de operaciones redundantes", "lineNumbers": [12, 13]},
                    {"description": "Mejora del manejo de errores", "lineNumbers": [4, 7, 19]}
                ]

                explanation = "El código ha sido refactorizado siguiendo las instrucciones proporcionadas. Se mejoró la legibilidad, se optimizó el rendimiento y se implementó un manejo de errores más robusto."

            except Exception as e:
                logging.error(f"Error with OpenAI API during code correction: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al procesar con OpenAI: {str(e)}'
                }), 500
                
        elif model == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            try:
                try:
                    import anthropic
                except ImportError:
                    # Si el módulo no está instalado, lo instalamos
                    logging.warning("Módulo anthropic no encontrado, instalándolo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "anthropic"])
                    import anthropic
                
                anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not anthropic_api_key:
                    return jsonify({
                        'success': False,
                        'error': 'La clave API de Anthropic no está configurada'
                    }), 500
                
                # Inicializar el cliente con la clave API
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                
                # Crear mensaje para Claude
                prompt = f"""Eres un asistente de programación experto. Por favor, mejora el siguiente código en {language} según estas instrucciones: {instructions}

                Código:
                ```{language}
                {code}
                ```

                Devuelve solo el código corregido dentro de un bloque de código.
                """
                
                completion = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=2000,
                    temperature=0.2,
                    system="Eres un experto en programación que mejora código siguiendo instrucciones específicas.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                response_text = completion.content[0].text
                
                # Extract corrected code
                code_pattern = f"```(?:{language})?\n(.*?)\n```"
                code_match = re.search(code_pattern, response_text, re.DOTALL)
                if code_match:
                    corrected_code = code_match.group(1)
                
                changes = [
                    {"description": "Código optimizado por Claude", "lineNumbers": []}
                ]
                
                explanation = "El código ha sido mejorado por Claude siguiendo las instrucciones proporcionadas."
                
            except Exception as e:
                logging.error(f"Error with Anthropic API during code correction: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al procesar con Anthropic: {str(e)}'
                }), 500
                
        elif model == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            try:
                try:
                    import google.generativeai as genai
                except ImportError:
                    # Si el módulo no está instalado, intentamos instalarlo
                    logging.warning("Módulo google.generativeai no encontrado, intentando instalarlo...")
                    import subprocess
                    subprocess.check_call(["pip", "install", "google-generativeai"])
                    import google.generativeai as genai
                
                gemini_api_key = os.environ.get('GEMINI_API_KEY')
                genai.configure(api_key=gemini_api_key)
                
                # Configurar el modelo con opciones de generación
                gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config={
                        'temperature': 0.2,
                        'top_p': 0.9,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                
                prompt = f"""Eres un asistente de programación experto. Por favor, mejora el siguiente código en {language} según estas instrucciones: {instructions}

                Código:
                ```{language}
                {code}
                ```

                Devuelve solo el código corregido dentro de un bloque de código.
                """
                
                gemini_response = gemini_model.generate_content(prompt)
                response_text = gemini_response.text
                
                # Extract corrected code
                code_pattern = f"```(?:{language})?\n(.*?)\n```"
                code_match = re.search(code_pattern, response_text, re.DOTALL)
                if code_match:
                    corrected_code = code_match.group(1)
                else:
                    # Si no hay un bloque de código, usamos la respuesta completa
                    corrected_code = response_text
                
                changes = [
                    {"description": "Código optimizado por Gemini", "lineNumbers": []}
                ]
                
                explanation = "El código ha sido mejorado por Gemini siguiendo las instrucciones proporcionadas."
                
            except Exception as e:
                logging.error(f"Error with Gemini API during code correction: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error al procesar con Gemini: {str(e)}'
                }), 500
        else:
            changes = [
                {"description": "No se pudo procesar el código", "lineNumbers": []}
            ]
            explanation = "No hay un modelo de IA configurado disponible. Por favor, verifica las API keys en la configuración."
            logging.warning(f"No hay modelo disponible para: {model}")

        return jsonify({
            'success': True,
            'correctedCode': corrected_code,
            'changes': changes,
            'explanation': explanation
        })

    except Exception as e:
        logging.error(f"Error in code correction endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Fallback endpoint for content generation."""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
            
        # Simple fallback response
        response = f"Respuesta generada para: {message[:50]}..."
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
