import os
import re
import json
import logging
import traceback
import subprocess
import time
from pathlib import Path
from flask import Flask, request
from flask_socketio import SocketIO, emit
import openai
import anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Variables globales
workspaces_dir = os.path.join(os.getcwd(), 'user_workspaces')

def init_app(app, socketio):
    """Inicializa las rutas de socket.io para el terminal inteligente"""

    @socketio.on('connect')
    def handle_connect():
        logging.info('Cliente conectado a WebSocket')

    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info('Cliente desconectado de WebSocket')

    @socketio.on('natural_language')
    def handle_natural_language(data):
        """Procesa instrucciones en lenguaje natural con el asistente IA"""
        natural_text = data.get('text', '')
        model = data.get('model', 'openai')
        user_id = data.get('user_id', 'default')

        logging.info(f"Procesando lenguaje natural: '{natural_text}' con modelo {model}")

        # Obtener workspace del usuario
        workspace_path = get_user_workspace(user_id)

        # Procesar la instrucción según el modelo seleccionado
        result = process_natural_language(natural_text, model, workspace_path)

        # Emitir la respuesta del asistente
        emit('assistant_response', result)

        # Si la respuesta incluye un comando a ejecutar automáticamente
        if result.get('success') and result.get('command') and result.get('auto_execute', False):
            # Ejecutar el comando
            command_result = execute_command(result['command'], workspace_path)
            emit('command_result', command_result)

    @socketio.on('bash_command')
    def handle_bash_command(data):
        """Procesa comando bash directo"""
        bash_command = data.get('command', '')
        user_id = data.get('user_id', 'default')

        logging.info(f"Procesando comando bash: '{bash_command}'")

        # Obtener workspace del usuario
        workspace_path = get_user_workspace(user_id)

        # Validar y ejecutar el comando
        if validate_command(bash_command):
            result = execute_command(bash_command, workspace_path)
            emit('command_result', result)
        else:
            emit('command_result', {
                'success': False,
                'command': bash_command,
                'output': f"Comando no permitido: {bash_command}"
            })

    @socketio.on('list_directory')
    def handle_list_directory(data):
        """Lista contenido de un directorio"""
        path = data.get('path', '.')
        user_id = data.get('user_id', 'default')

        # Obtener workspace del usuario
        workspace_path = get_user_workspace(user_id)

        # Listar contenido del directorio
        try:
            # Construir ruta completa
            full_path = os.path.join(workspace_path, path)

            # Limpiar la ruta para evitar path traversal
            if ".." in full_path:
                emit('directory_contents', {
                    'success': False,
                    'path': path,
                    'error': 'Ruta no permitida'
                })
                return

            # Verificar que el directorio existe
            if not os.path.exists(full_path):
                emit('directory_contents', {
                    'success': False,
                    'path': path,
                    'error': 'Directorio no encontrado'
                })
                return

            # Obtener contenido
            contents = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                contents.append({
                    'name': item,
                    'is_directory': os.path.isdir(item_path),
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    'modified': os.path.getmtime(item_path)
                })

            emit('directory_contents', {
                'success': True,
                'path': path,
                'contents': contents
            })
        except Exception as e:
            logging.error(f"Error al listar directorio: {str(e)}")
            emit('directory_contents', {
                'success': False,
                'path': path,
                'error': str(e)
            })

def get_user_workspace(user_id='default'):
    """Obtiene o crea un workspace para el usuario"""
    workspace_dir = os.path.join(workspaces_dir, user_id)
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir

def validate_command(command):
    """Valida que el comando sea seguro para ejecutar"""
    # Lista de comandos prohibidos o patrones peligrosos
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # Borrado recursivo desde la raíz
        r'>`',            # Redireccionamiento destructivo
        r'>\s*/dev/sd',   # Escritura directa a dispositivos
        r'mkfs',          # Formateo de sistemas de archivos
        r'dd\s+if=',      # Operaciones dd potencialmente peligrosas
        r'wget.+\s+\|\s+bash', # Descarga y ejecución directa
        r'curl.+\s+\|\s+bash', # Descarga y ejecución directa
    ]

    # Verificar patrones peligrosos
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return False

    return True

def execute_command(command, workspace_path):
    """Ejecuta un comando en el workspace del usuario"""
    try:
        # Ejecutar comando con timeout para evitar bloqueos
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=workspace_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Establecer un timeout razonable (30 segundos)
        stdout, stderr = process.communicate(timeout=30)

        # Emitir eventos de sistema de archivos si el comando los modifica
        if re.match(r'(mkdir|touch|rm|cp|mv|git|echo)', command):
            # Enviar evento para alertar que hubo modificaciones en el sistema de archivos
            # El cliente recargará el explorador de archivos
            emit('file_system_changed', {
                'command': command,
                'workspace_path': workspace_path,
                'timestamp': time.time()
            })

        return {
            'success': process.returncode == 0,
            'command': command,
            'output': stdout + (f"\nError: {stderr}" if stderr else ""),
            'status': process.returncode
        }
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            'success': False,
            'command': command,
            'output': 'Timeout: El comando tardó demasiado en completarse',
            'status': -1
        }
    except Exception as e:
        logging.error(f"Error ejecutando comando: {str(e)}")
        return {
            'success': False,
            'command': command,
            'output': f"Error: {str(e)}",
            'status': -1
        }

def process_natural_language(text, model, workspace_path):
    """
    Procesa una instrucción en lenguaje natural y la convierte en un comando ejecutable.

    Args:
        text: Texto de la instrucción en lenguaje natural
        model: Modelo de IA a utilizar (openai, anthropic, gemini)
        workspace_path: Ruta del workspace del usuario

    Returns:
        dict: Resultado con comando sugerido y explicación
    """
    try:
        # Primero intentar con reglas simples para comandos comunes
        command = simple_nl_to_command(text)
        if command:
            return {
                'success': True,
                'command': command,
                'explanation': f"He interpretado tu instrucción como el comando: {command}",
                'auto_execute': True
            }

        # Si no coincide con reglas simples, usar el modelo de IA seleccionado
        if model == 'openai' and os.environ.get('OPENAI_API_KEY'):
            return process_with_openai(text, workspace_path)
        elif model == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
            return process_with_anthropic(text, workspace_path)
        elif model == 'gemini' and os.environ.get('GEMINI_API_KEY'):
            return process_with_gemini(text, workspace_path)
        else:
            return {
                'success': False,
                'error': f"Modelo {model} no disponible o API key no configurada."
            }

    except Exception as e:
        logging.error(f"Error procesando lenguaje natural: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'error': f"Error al procesar la instrucción: {str(e)}"
        }

def simple_nl_to_command(text):
    """
    Convierte instrucciones simples en comandos bash utilizando reglas predefinidas.
    """
    text = text.lower()

    # Reglas para crear archivos y directorios
    if re.search(r'crea(?:r)?\s+(?:un\s+)?(?:archivo|fichero)\s+(?:llamado\s+)?["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text):
        file_name = re.search(r'crea(?:r)?\s+(?:un\s+)?(?:archivo|fichero)\s+(?:llamado\s+)?["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text).group(1)
        return f"touch {file_name}"

    if re.search(r'crea(?:r)?\s+(?:una\s+)?(?:carpeta|directorio)\s+(?:llamad[oa]\s+)?["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text):
        dir_name = re.search(r'crea(?:r)?\s+(?:una\s+)?(?:carpeta|directorio)\s+(?:llamad[oa]\s+)?["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text).group(1)
        return f"mkdir -p {dir_name}"

    # Reglas para listar archivos
    if re.search(r'(?:lista|muestra|ver|visualiza)(?:r)?\s+(?:archivos|ficheros|contenido|contenidos|directorio)', text):
        if 'detalle' in text or 'detallada' in text:
            return "ls -la"
        else:
            return "ls -l"

    # Reglas para eliminar archivos o directorios
    if re.search(r'(?:elimina|borra|remueve)(?:r)?\s+(?:el\s+)?(?:archivo|fichero)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text):
        file_name = re.search(r'(?:elimina|borra|remueve)(?:r)?\s+(?:el\s+)?(?:archivo|fichero)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text).group(1)
        return f"rm {file_name}"

    if re.search(r'(?:elimina|borra|remueve)(?:r)?\s+(?:la\s+)?(?:carpeta|directorio)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text):
        dir_name = re.search(r'(?:elimina|borra|remueve)(?:r)?\s+(?:la\s+)?(?:carpeta|directorio)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text).group(1)
        return f"rm -r {dir_name}"

    # Reglas para mostrar contenido de archivos
    if re.search(r'(?:muestra|ver|visualiza|cat)(?:r)?\s+(?:el\s+)?contenido\s+(?:del\s+)?(?:archivo|fichero)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text):
        file_name = re.search(r'(?:muestra|ver|visualiza|cat)(?:r)?\s+(?:el\s+)?contenido\s+(?:del\s+)?(?:archivo|fichero)\s+["\'`]?([a-zA-Z0-9_\-\.\/]+)["\'`]?', text).group(1)
        return f"cat {file_name}"

    # Si no coincide con ninguna regla simple, retornar None
    return None

def process_with_openai(text, workspace_path):
    """Procesa instrucción con OpenAI"""
    try:
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """Eres un asistente especializado en interpretar instrucciones en lenguaje natural y convertirlas en comandos bash para un terminal.
Tu tarea es analizar la instrucción del usuario y determinar el comando bash que mejor la satisface.
Debes responder en formato JSON con los siguientes campos:
- command: el comando bash ejecutable para realizar la acción solicitada
- explanation: explicación clara de lo que hace el comando
- auto_execute: booleano que indica si el comando es seguro para ejecutar automáticamente (true) o requiere confirmación (false)"""},
                {"role": "user", "content": f"Instrucción: {text}"}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        # Procesar respuesta de OpenAI
        result = json.loads(response.choices[0].message.content)

        # Validación básica del resultado
        if 'command' not in result:
            return {
                'success': False,
                'error': "La respuesta del modelo no contiene un comando válido."
            }

        # Sanitizar y validar el comando resultante
        command = result.get('command', '').strip()
        if not command or not validate_command(command):
            return {
                'success': False,
                'error': f"El comando sugerido '{command}' no es válido o seguro para ejecutar."
            }

        return {
            'success': True,
            'command': command,
            'explanation': result.get('explanation', 'Comando generado basado en tu instrucción.'),
            'auto_execute': result.get('auto_execute', False)
        }

    except Exception as e:
        logging.error(f"Error con OpenAI: {str(e)}")
        return {
            'success': False,
            'error': f"Error al procesar con OpenAI: {str(e)}"
        }

def process_with_anthropic(text, workspace_path):
    """Procesa instrucción con Anthropic Claude"""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1000,
            temperature=0.2,
            system="""Eres un asistente especializado en interpretar instrucciones en lenguaje natural y convertirlas en comandos bash para un terminal.
Tu tarea es analizar la instrucción del usuario y determinar el comando bash que mejor la satisface.
Debes responder en formato JSON con los siguientes campos:
- command: el comando bash ejecutable para realizar la acción solicitada
- explanation: explicación clara de lo que hace el comando
- auto_execute: booleano que indica si el comando es seguro para ejecutar automáticamente (true) o requiere confirmación (false)""",
            messages=[
                {"role": "user", "content": f"Instrucción: {text}"}
            ]
        )

        # Extraer respuesta de Claude (puede estar en formato JSON directo o en un bloque de código)
        content = response.content[0].text

        try:
            # Primero intentar con JSON directo
            result = json.loads(content)
        except json.JSONDecodeError:
            # Buscar bloque JSON en la respuesta
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': "No se pudo parsear la respuesta JSON de Claude."
                    }
            else:
                return {
                    'success': False,
                    'error': "Claude no devolvió una respuesta en formato JSON válido."
                }

        # Validación básica del resultado
        if 'command' not in result:
            return {
                'success': False,
                'error': "La respuesta del modelo no contiene un comando válido."
            }

        # Sanitizar y validar el comando resultante
        command = result.get('command', '').strip()
        if not command or not validate_command(command):
            return {
                'success': False,
                'error': f"El comando sugerido '{command}' no es válido o seguro para ejecutar."
            }

        return {
            'success': True,
            'command': command,
            'explanation': result.get('explanation', 'Comando generado basado en tu instrucción.'),
            'auto_execute': result.get('auto_execute', False)
        }

    except Exception as e:
        logging.error(f"Error con Anthropic: {str(e)}")
        return {
            'success': False,
            'error': f"Error al procesar con Claude: {str(e)}"
        }

def process_with_gemini(text, workspace_path):
    """Procesa instrucción con Google Gemini"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')

        prompt = f"""
        Instrucción del usuario: {text}

        Analiza esta instrucción y conviértela en un comando bash que pueda ejecutarse en un terminal.
        Debes responder ÚNICAMENTE en formato JSON con estos campos:
        - command: el comando bash ejecutable para realizar la acción solicitada
        - explanation: explicación clara de lo que hace el comando
        - auto_execute: booleano que indica si el comando es seguro para ejecutar automáticamente (true) o requiere confirmación (false)
        """

        response = model.generate_content(prompt)

        # Extraer JSON de la respuesta
        content = response.text

        try:
            # Buscar bloque JSON en la respuesta
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Intentar extraer JSON sin formato de bloque
                json_pattern = r'({.*})'
                json_match = re.search(json_pattern, content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    return {
                        'success': False,
                        'error': "Gemini no devolvió una respuesta en formato JSON válido."
                    }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': "No se pudo parsear la respuesta JSON de Gemini."
            }

        # Validación básica del resultado
        if 'command' not in result:
            return {
                'success': False,
                'error': "La respuesta del modelo no contiene un comando válido."
            }

        # Sanitizar y validar el comando resultante
        command = result.get('command', '').strip()
        if not command or not validate_command(command):
            return {
                'success': False,
                'error': f"El comando sugerido '{command}' no es válido o seguro para ejecutar."
            }

        return {
            'success': True,
            'command': command,
            'explanation': result.get('explanation', 'Comando generado basado en tu instrucción.'),
            'auto_execute': result.get('auto_execute', False)
        }

    except Exception as e:
        logging.error(f"Error con Gemini: {str(e)}")
        return {
            'success': False,
            'error': f"Error al procesar con Gemini: {str(e)}"
        }

# Exportar función de inicialización
def init_terminal(app, socketio):
    """Inicializa el terminal inteligente en la aplicación Flask"""
    init_app(app, socketio)
    return True