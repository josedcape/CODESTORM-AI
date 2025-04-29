from flask import Flask, render_template, request, jsonify, session, redirect, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
import json
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import subprocess
import time
import shutil
from pathlib import Path
import traceback


# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25, logger=True, engineio_logger=True)

# Configure API keys
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

if openai_api_key:
    openai.api_key = openai_api_key
    logging.info(f"OpenAI API key configurada: {openai_api_key[:5]}...{openai_api_key[-5:]}")

if anthropic_api_key:
    logging.info(f"Anthropic API key configurada: {anthropic_api_key[:5]}...{anthropic_api_key[-5:]}")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    logging.info(f"Gemini API key configurada: {gemini_api_key[:5]}...{gemini_api_key[-5:]}")


class FileSystemManager:
    def __init__(self, socketio):
        self.socketio = socketio

    def get_user_workspace(self, user_id='default'):
        """Get or create a workspace directory for the user."""
        workspace_path = Path("./user_workspaces") / user_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        return workspace_path

    def notify_terminals(self, user_id, data, exclude_terminal=None):
        """Notify all terminals of a user about command execution."""
        self.socketio.emit('command_result', data, room=user_id)

    def execute_command(self, command, user_id='default', notify=True, terminal_id=None):
        """Ejecuta un comando en el workspace del usuario."""
        try:
            workspace_dir = self.get_user_workspace(user_id)
            current_dir = os.getcwd()
            os.chdir(workspace_dir)

            logging.info(f"Ejecutando comando: '{command}' en workspace: {workspace_dir}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            os.chdir(current_dir)

            output = result.stdout if result.returncode == 0 else result.stderr
            success = result.returncode == 0

            if notify and terminal_id:
                self.notify_terminals(user_id, {
                    'output': output,
                    'success': success,
                    'command': command,
                    'terminal_id': terminal_id
                })

            file_modifying_commands = ['mkdir', 'touch', 'rm', 'cp', 'mv']
            if any(cmd in command.split() for cmd in file_modifying_commands):
                self.socketio.emit('file_system_changed', {
                    'user_id': user_id,
                    'command': command,
                    'timestamp': time.time()
                }, room=user_id)

            return {
                'output': output,
                'success': success,
                'command': command
            }

        except subprocess.TimeoutExpired:
            logging.error(f"Timeout al ejecutar comando: {command}")
            return {
                'output': 'Error: El comando tardó demasiado tiempo en ejecutarse',
                'success': False,
                'command': command
            }
        except Exception as e:
            logging.error(f"Error al ejecutar comando: {str(e)}")
            return {
                'output': f'Error: {str(e)}',
                'success': False,
                'command': command
            }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Render the chat page with specialized agents."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint para manejar solicitudes de chat."""
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            logging.warning("No se recibieron datos JSON válidos")
            return jsonify({
                'error': 'Invalid JSON data',
                'response': 'Error: Los datos enviados no son JSON válido'
            }), 400

        logging.debug(f"Datos recibidos: {json.dumps(data)}")

        user_message = data.get('message')
        agent_id = data.get('agent_id', 'general')
        model_choice = data.get('model', 'gemini')
        context = data.get('context', [])

        if not user_message:
            return jsonify({'error': 'No se proporcionó un mensaje'}), 400

        # Configurar prompts específicos según el agente seleccionado
        agent_prompts = {
            'developer': "Eres un Agente de Desarrollo experto en optimización y edición de código en tiempo real. Tu objetivo es ayudar a los usuarios con tareas de programación, desde la corrección de errores hasta la implementación de funcionalidades completas.",
            'architect': "Eres un Agente de Arquitectura especializado en diseñar arquitecturas escalables y optimizadas. Ayudas a los usuarios a tomar decisiones sobre la estructura del código, patrones de diseño y selección de tecnologías.",
            'advanced': "Eres un Agente Avanzado de Software con experiencia en integraciones complejas y funcionalidades avanzadas. Puedes asesorar sobre tecnologías emergentes, optimización de rendimiento y soluciones a problemas técnicos sofisticados.",
            'general': "Eres un asistente de desarrollo de software experto y útil. Respondes preguntas y ayudas con tareas de programación de manera clara y concisa."
        }

        system_prompt = agent_prompts.get(agent_id, agent_prompts['general'])

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

        response = ""

        # Usar el modelo seleccionado para generar la respuesta
        if model_choice == 'openai' and openai_api_key:
            try:
                messages = [{"role": "system", "content": system_prompt}]

                # Añadir mensajes de contexto
                for msg in formatted_context:
                    messages.append({"role": msg['role'], "content": msg['content']})

                # Añadir el mensaje actual del usuario
                messages.append({"role": "user", "content": user_message})

                completion = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )

                response = completion.choices[0].message.content
                logging.info(f"Respuesta generada con OpenAI: {response[:100]}...")

            except Exception as e:
                logging.error(f"Error con API de OpenAI: {str(e)}")
                return jsonify({
                    'error': f"Error con OpenAI: {str(e)}",
                    'agent': agent_id,
                    'model': model_choice
                }), 500

        elif model_choice == 'anthropic' and anthropic_api_key:
            try:
                # Importar anthropic si es necesario
                import anthropic
                from anthropic import Anthropic

                # Inicializar cliente
                client = Anthropic(api_key=anthropic_api_key)

                messages = [{"role": "system", "content": system_prompt}]

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
                logging.info(f"Respuesta generada con Anthropic: {response[:100]}...")

            except Exception as e:
                logging.error(f"Error con API de Anthropic: {str(e)}")
                return jsonify({
                    'error': f"Error con Anthropic: {str(e)}",
                    'agent': agent_id,
                    'model': model_choice
                }), 500

        elif model_choice == 'gemini' and gemini_api_key:
            try:

                model = genai.GenerativeModel('gemini-1.5-pro')

                # Construir el prompt con contexto
                full_prompt = system_prompt + "\n\n"

                # Añadir el contexto de la conversación
                for msg in formatted_context:
                    role_prefix = "Usuario: " if msg['role'] == 'user' else "Asistente: "
                    full_prompt += role_prefix + msg['content'] + "\n\n"

                # Añadir el mensaje actual
                full_prompt += "Usuario: " + user_message + "\n\nAsistente: "

                # Generar respuesta
                gemini_response = model.generate_content(full_prompt)
                response = gemini_response.text
                logging.info(f"Respuesta generada con Gemini: {response[:100]}...")

            except Exception as e:
                logging.error(f"Error con API de Gemini: {str(e)}")
                return jsonify({
                    'error': f"Error con Gemini: {str(e)}",
                    'agent': agent_id,
                    'model': model_choice
                }), 500
        else:
            # Si ningún modelo está disponible o no se ha seleccionado uno válido
            return jsonify({
                'error': f"Modelo {model_choice} no soportado o API no configurada",
                'agent': agent_id,
                'model': model_choice
            }), 400

        # Registrar la petición para depuración
        logging.info(f"Mensaje procesado: {user_message} por agente {agent_id} usando {model_choice}")

        # Devolver respuesta
        return jsonify({
            'response': response,
            'agent': agent_id,
            'model': model_choice
        })
    except Exception as e:
        logging.error(f"Error en API de chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/xterm_terminal')
def xterm_terminal_route():
    """Render the XTerm terminal page directly."""
    # En lugar de redireccionar, renderizamos la plantilla directamente
    return render_template('xterm_terminal.html')

# Ruta adicional para asegurar compatibilidad con solicitudes a /xterm/xterm_terminal
@app.route('/xterm/xterm_terminal')
def xterm_terminal_alt():
    """Ruta alternativa para acceder a la terminal XTerm."""
    return render_template('xterm_terminal.html')

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
        if model == 'openai' and openai_api_key:
            try:
                # Usar OpenAI para corregir el código
                response = openai.ChatCompletion.create(
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

        elif model == 'gemini' and gemini_api_key:
            try:
                # Usar genai para procesar con Gemini

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

@app.route('/api/process_natural', methods=['POST'])
def process_natural_command():
    """Process natural language input and return corresponding command."""
    try:
        data = request.json
        text = data.get('text', '')
        user_id = data.get('user_id', 'default')

        if not text:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó texto'
            }), 400

        command = process_natural_language_to_command(text)

        # Si se generó un comando, verificamos si es un comando que modifica archivos
        if command:
            # Lista de comandos que modifican el sistema de archivos
            file_modifying_commands = ['mkdir', 'touch', 'rm', 'cp', 'mv', 'ls']

            # Verificar si el comando es uno que modifica archivos
            is_file_command = any(cmd in command for cmd in file_modifying_commands)

            # Ejecutar el comando real en el sistema
            try:
                workspace_dir = get_user_workspace(user_id)
                current_dir = os.getcwd()
                os.chdir(workspace_dir)

                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                os.chdir(current_dir)

                command_output = result.stdout if result.returncode == 0 else result.stderr
                command_success = result.returncode == 0
            except Exception as cmd_error:
                logging.error(f"Error al ejecutar comando: {str(cmd_error)}")
                command_output = f"Error: {str(cmd_error)}"
                command_success = False

            # Si es un comando de archivos, enviar notificación por WebSocket
            if is_file_command:
                # Determinar el tipo de cambio
                change_type = 'unknown'
                file_path = ''

                if 'mkdir' in command:
                    change_type = 'create'
                    file_path = command.split('mkdir ')[1].strip()
                elif 'touch' in command:
                    change_type = 'create'
                    file_path = command.split('touch ')[1].strip()
                elif 'rm' in command:
                    change_type = 'delete'
                    parts = command.split('rm ')
                    if len(parts) > 1:
                        file_path = parts[1].replace('-rf', '').strip()

                # Enviar múltiples notificaciones para garantizar la actualización
                try:
                    # Notificación específica del cambio
                    socketio.emit('file_change', {
                        'type': change_type,
                        'file': {'path': file_path},
                        'timestamp': time.time()
                    }, broadcast=True)

                    # Notificación genérica de actualización
                    socketio.emit('file_sync', {
                        'refresh': True,
                        'timestamp': time.time()
                    }, broadcast=True)

                    # Notificación para terminales
                    socketio.emit('file_command', {
                        'command': command,
                        'type': change_type,
                        'file': file_path,
                        'timestamp': time.time()
                    }, broadcast=True)

                    # Notificación de comando ejecutado
                    socketio.emit('command_executed', {
                        'command': command,
                        'output': command_output,
                        'success': command_success,
                        'timestamp': time.time()
                    }, broadcast=True)

                    logging.info(f"Notificaciones de cambio enviadas: {change_type} - {file_path}")
                except Exception as ws_error:
                    logging.error(f"Error al enviar notificación WebSocket: {str(ws_error)}")

            return jsonify({
                'success': True,
                'command': command,
                'refresh_explorer': is_file_command,
                'output': command_output,
                'success': command_success
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo generar un comando para esa instrucción'
            }), 400

    except Exception as e:
        logging.error(f"Error processing natural language: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process_instructions', methods=['POST'])
def process_instructions():
    """Process natural language instructions and convert to terminal commands."""
    try:
        data = request.json
        instruction = data.get('message', '') or data.get('instruction', '')
        model_choice = data.get('model', 'openai')  # Default to OpenAI

        if not instruction:
            return jsonify({'error': 'No instruction provided'}), 400

        # For handling command-only responses
        command_only = data.get('command_only', False)

        # Process the instruction to generate a command
        try:
            # Simple mapping for common commands
            command_map = {
                "listar": "ls -la",
                "mostrar archivos": "ls -la",
                "mostrar directorio": "ls -la",
                "ver archivos": "ls -la",
                "archivos": "ls -la",
                "dir": "ls -la",
                "fecha": "date",
                "hora": "date +%H:%M:%S",
                "calendario": "cal",
                "quien soy": "whoami",
                "donde estoy": "pwd",
                "limpiar": "clear",
                "sistema": "uname -a",
                "memoria": "free -h",
                "espacio": "df -h",
                "procesos": "ps aux"
            }
            
            instruction_lower = instruction.lower()
            terminal_command = None
            missing_info = None
            
            # Check for exact matches first
            for key, cmd in command_map.items():
                if key in instruction_lower:
                    terminal_command = cmd
                    break
                    
            # If no direct match, use pattern matching
            if not terminal_command:
                if "crear" in instruction_lower and "carpeta" in instruction_lower:
                    folder_name = instruction_lower.split("carpeta")[-1].strip()
                    if not folder_name:
                        missing_info = "Falta especificar el nombre de la carpeta"
                    else:
                        terminal_command = f"mkdir -p {folder_name}"
                
                elif "crear" in instruction_lower and "archivo" in instruction_lower:
                    file_name = instruction_lower.split("archivo")[-1].strip()
                    if not file_name:
                        missing_info = "Falta especificar el nombre del archivo"
                    else:
                        terminal_command = f"touch {file_name}"
                
                elif "eliminar" in instruction_lower or "borrar" in instruction_lower:
                    target = instruction_lower.replace("eliminar", "").replace("borrar", "").strip()
                    if not target:
                        missing_info = "Falta especificar qué elemento eliminar"
                    else:
                        terminal_command = f"rm -rf {target}"
                
                else:
                    # Default command if nothing else matches
                    terminal_command = "echo 'Comando no reconocido'"
            
            # Log the generated command
            if terminal_command:
                logging.info(f"Instrucción: '{instruction}' → Comando: '{terminal_command}'")
            
            # Return just the command or with additional context
            if missing_info:
                return jsonify({
                    'error': missing_info,
                    'needs_more_info': True
                })
            elif command_only:
                return jsonify({'command': terminal_command})
            else:
                return jsonify({
                    'command': terminal_command,
                    'original_instruction': instruction,
                    'model_used': model_choice
                })
                
        except Exception as e:
            logging.error(f"Error generating command: {str(e)}")
            return jsonify({'error': f"Error generating command: {str(e)}"}), 500

    except Exception as e:
        logging.error(f"Error processing instructions: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for the application."""
    try:
        # Check API configurations
        apis = {
            "openai": "ok" if openai_api_key else "not configured",
            "anthropic": "ok" if anthropic_api_key else "not configured",
            "gemini": "ok" if gemini_api_key else "not configured"
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

        return send_file(full_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        logging.error(f"Error al descargar archivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error al descargar archivo: {str(e)}'
        }), 500


@app.route('/api_status')
def api_status():
    """Muestra el estado de las claves API configuradas."""
    openai_key = os.environ.get('OPENAI_API_KEY', 'No configurada')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', 'No configurada')
    gemini_key = os.environ.get('GEMINI_API_KEY', 'No configurada')

    # Ocultar la mayoría de los caracteres para seguridad
    if openai_key != 'No configurada':
        openai_key = openai_key[:5] + "..." + openai_key[-5:] if len(openai_key) > 10 else "***configurada***"

    if anthropic_key != 'No configurada':
        anthropic_key = anthropic_key[:5] + "..." + anthropic_key[-5:] if len(anthropic_key) > 10 else "***configurada***"

    if gemini_key != 'No configurada':
        gemini_key = gemini_key[:5] + "..." + gemini_key[-5:] if len(gemini_key) > 10 else "***configurada***"

    return jsonify({
        'openai': openai_key,
        'anthropic': anthropic_key,
        'gemini': gemini_key,
        'message': 'Visita esta URL para verificar el estado de las APIs'
    })

@socketio.on('connect')
def handle_connect():
    """Manejar conexión de cliente Socket.IO."""
    logging.info(f"Cliente Socket.IO conectado: {request.sid}")
    emit('server_info', {'status': 'connected', 'sid': request.sid})

@socketio.on('execute_command')
def handle_execute_command(data):
    """Ejecuta un comando en la terminal y devuelve el resultado."""
    command = data.get('command', '')
    user_id = data.get('user_id', 'default')
    terminal_id = data.get('terminal_id', request.sid)

    if not command:
        emit('command_error', {
            'error': 'No se proporcionó un comando',
            'terminal_id': terminal_id
        }, room=terminal_id)
        return

    file_system_manager = FileSystemManager(socketio)
    result = file_system_manager.execute_command(
        command=command,
        user_id=user_id,
        notify=True,
        terminal_id=terminal_id
    )

    emit('command_result', {
        'output': result.get('output', ''),
        'success': result.get('success', False),
        'command': command,
        'terminal_id': terminal_id
    }, room=terminal_id)

    socketio.emit('file_sync', {
        'refresh': True,
        'user_id': user_id,
        'command': command
    }, room=user_id)

def process_natural_language_to_command(text):
    #  This is a placeholder.  A more robust implementation would be needed here.
    return text


#Manejadores de eventos SocketIO para xterm
@socketio.on('connect')
def handle_connect():
    """Maneja la conexión de un cliente."""
    client_id = request.sid
    app.logger.info(f"Cliente conectado: {client_id}")

@socketio.on('execute_command')
def handle_execute_command(data):
    """Ejecuta un comando y devuelve el resultado."""
    command = data.get('command', '')
    terminal_id = data.get('terminal_id', '')
    user_id = data.get('user_id', 'default')

    if not command:
        emit('command_result', {
            'success': False,
            'terminal_id': terminal_id,
            'output': 'No se proporcionó ningún comando'
        })
        return

    try:
        # Obtener workspace del usuario
        workspace_path = os.path.join('user_workspaces', user_id)
        os.makedirs(workspace_path, exist_ok=True)

        # Ejecutar comando
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=workspace_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        # Emitir resultado
        emit('command_result', {
            'success': process.returncode == 0,
            'terminal_id': terminal_id,
            'command': command,
            'output': stdout if process.returncode == 0 else stderr
        })

    except Exception as e:
        app.logger.error(f"Error al ejecutar comando: {str(e)}")
        emit('command_result', {
            'success': False,
            'terminal_id': terminal_id,
            'command': command,
            'output': f"Error: {str(e)}"
        })

def handle_chat_internal(request_data):
    # This function is a placeholder and should contain the existing chat handling logic.  It's not included in the provided original code
    # so a basic placeholder will be used instead.  In a real implementation, this function will process the chat request and return a response.
    return {'response': 'This is a placeholder response from handle_chat_internal', 'error': None}

@socketio.on('user_message')
def handle_user_message(data):
    """Manejar mensajes del usuario a través de Socket.IO."""
    try:
        logging.info(f"Mensaje recibido vía Socket.IO: {data}")
        user_message = data.get('message', '')
        agent_id = data.get('agent', 'developer')  # Cambiado a developer por defecto
        model = data.get('model', 'openai')  # Cambiado a openai por defecto
        document = data.get('document', '')
        terminal_id = data.get('terminal_id', '')

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

        # Intentar procesar mediante API directa primero para mejor rendimiento
        try:
            if model == 'openai' and openai_api_key:
                # Usar OpenAI directamente
                messages = [
                    {"role": "system", "content": f"Eres un asistente de {agent_id} experto y útil."},
                    {"role": "user", "content": user_message}
                ]

                completion = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )

                response = completion.choices[0].message.content
                logging.info(f"Respuesta generada directamente con OpenAI: {response[:100]}...")

                emit('agent_response', {
                    'response': response,
                    'agent': agent_id,
                    'model': model,
                    'error': None
                })
                return
        except Exception as api_error:
            logging.warning(f"Error en API directa: {str(api_error)}, usando handle_chat_internal")
            # Continuar con el método alternativo

        # Procesar el mensaje usando la lógica existente
        result = handle_chat_internal(request_data)

        # Enviar respuesta al cliente
        logging.info(f"Enviando respuesta Socket.IO: '{result.get('response', '')[:30]}...'")
        emit('agent_response', {
            'response': result.get('response', ''),
            'agent': agent_id,
            'model': model,
            'error': result.get('error', None),
            'terminal_id': terminal_id
        })

    except Exception as e:
        logging.error(f"Error en Socket.IO user_message: {str(e)}")
        logging.error(traceback.format_exc())
        emit('error', {'message': str(e)})

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

        # Intentar iniciar el hilo de observación de archivos si existe la función
        try:
            import threading
            if 'watch_workspace_files' in globals():
                file_watcher_thread = threading.Thread(target=watch_workspace_files, daemon=True)
                file_watcher_thread.start()
                logging.info("Observador de archivos iniciado correctamente")
        except Exception as watcher_error:
            logging.warning(f"No se pudo iniciar el observador de archivos: {str(watcher_error)}")

        # Configurar el servidor para usar web sockets
        logging.info("Servidor listo para recibir conexiones en puerto 5000")

        # Start the SocketIO server with engineio ping configurations
        # CORS is already configured when creating the SocketIO instance
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            allow_unsafe_werkzeug=True  # Required for newer Werkzeug versions
        )
    except Exception as e:
        logging.critical(f"Error fatal al iniciar el servidor: {str(e)}")
        logging.critical(traceback.format_exc())