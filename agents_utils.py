"""
Utilidades para la gestión de agentes especializados en Codestorm Assistant.
"""
import os
import re
import logging
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar clientes de API
openai_client = None
anthropic_client = None
genai_configured = False

def setup_ai_clients():
    """Configura los clientes de las APIs de IA."""
    global openai_client, anthropic_client, genai_configured
    
    # Configurar OpenAI
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = openai.OpenAI(api_key=openai_api_key)
        logger.info(f"OpenAI API key configurada: {openai_api_key[:5]}...{openai_api_key[-5:]}")
    else:
        logger.warning("No se encontró la clave de API de OpenAI en las variables de entorno")
    
    # Configurar Anthropic
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        logger.info("Anthropic API key configured successfully.")
    else:
        logger.warning("No se encontró la clave de API de Anthropic en las variables de entorno")
    
    # Configurar Google Gemini
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        genai_configured = True
        logger.info("Gemini API key configured successfully.")
    else:
        logger.warning("No se encontró la clave de API de Google Gemini en las variables de entorno")

# Configurar los clientes al importar el módulo
setup_ai_clients()

def get_agent_system_prompt(agent_id):
    """Obtiene el prompt de sistema para el agente especificado."""
    prompts = {
        'developer': """Eres un desarrollador experto. Tu objetivo es ayudar con código, 
                      debugging y mejores prácticas de programación. Proporciona ejemplos 
                      de código claros y explicaciones concisas.""",
        'architect': """Eres un arquitecto de software experto. Tu objetivo es ayudar con 
                       diseño de sistemas, patrones y decisiones arquitectónicas.""",
        'general': """Eres un asistente general experto en tecnología y programación. 
                     Ayudas con cualquier tema relacionado con desarrollo de software."""
    }
    return prompts.get(agent_id, prompts['general'])

def get_agent_name(agent_id):
    """Obtiene el nombre amigable del agente."""
    names = {
        'developer': "Desarrollador Experto",
        'architect': "Arquitecto de Software",
        'general': "Asistente General"
    }
    return names.get(agent_id, "Asistente General")

def generate_with_openai(prompt, system_prompt, temperature=0.7):
    """
    Genera contenido utilizando la API de OpenAI.
    
    Args:
        prompt: Prompt para generar contenido
        system_prompt: Prompt de sistema para establecer el rol
        temperature: Temperatura para la generación (0.0 - 1.0)
        
    Returns:
        str: Contenido generado
    """
    if not openai_client:
        raise ValueError("Cliente de OpenAI no configurado. Verifica la clave API.")
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error en generate_with_openai: {str(e)}")
        raise

def generate_with_anthropic(prompt, system_prompt, temperature=0.7):
    """
    Genera contenido utilizando la API de Anthropic.
    
    Args:
        prompt: Prompt para generar contenido
        system_prompt: Prompt de sistema para establecer el rol
        temperature: Temperatura para la generación (0.0 - 1.0)
        
    Returns:
        str: Contenido generado
    """
    if not anthropic_client:
        raise ValueError("Cliente de Anthropic no configurado. Verifica la clave API.")
    
    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022", # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024.
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        return message.content[0].text
    except Exception as e:
        logger.error(f"Error en generate_with_anthropic: {str(e)}")
        raise

def generate_with_gemini(prompt, system_prompt, temperature=0.7):
    """
    Genera contenido utilizando la API de Google Gemini.
    
    Args:
        prompt: Prompt para generar contenido
        system_prompt: Prompt de sistema para establecer el rol
        temperature: Temperatura para la generación (0.0 - 1.0)
        
    Returns:
        str: Contenido generado
    """
    if not genai_configured:
        raise ValueError("Google Gemini no configurado. Verifica la clave API.")
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={"temperature": temperature}
        )
        
        # Combinar system prompt y user prompt para Gemini
        combined_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = model.generate_content(combined_prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Error en generate_with_gemini: {str(e)}")
        raise

def generate_content(prompt, system_prompt, model="openai", temperature=0.7):
    """
    Genera contenido utilizando el modelo especificado.
    
    Args:
        prompt: Prompt para generar contenido
        system_prompt: Prompt de sistema para establecer el rol
        model: Modelo a utilizar (openai, anthropic, gemini)
        temperature: Temperatura para la generación (0.0 - 1.0)
        
    Returns:
        str: Contenido generado
    """
    try:
        if model == "openai":
            return generate_with_openai(prompt, system_prompt, temperature)
        elif model == "anthropic":
            return generate_with_anthropic(prompt, system_prompt, temperature)
        elif model == "gemini":
            return generate_with_gemini(prompt, system_prompt, temperature)
        else:
            # Por defecto, usar OpenAI
            return generate_with_openai(prompt, system_prompt, temperature)
    except Exception as e:
        logger.error(f"Error en generate_content con modelo {model}: {str(e)}")
        
        # Intentar con modelo alternativo si falla el primero
        try:
            if model != "openai" and openai_client:
                logger.info(f"Intentando con OpenAI como alternativa")
                return generate_with_openai(prompt, system_prompt, temperature)
            elif model != "anthropic" and anthropic_client:
                logger.info(f"Intentando con Anthropic como alternativa")
                return generate_with_anthropic(prompt, system_prompt, temperature)
            elif model != "gemini" and genai_configured:
                logger.info(f"Intentando con Gemini como alternativa")
                return generate_with_gemini(prompt, system_prompt, temperature)
            else:
                raise ValueError(f"No se pudo generar contenido con ningún modelo disponible")
        except Exception as fallback_error:
            logger.error(f"Error en fallback: {str(fallback_error)}")
            raise

def create_file_with_agent(description, file_type, filename, agent_id, workspace_path, model="openai"):
    """
    Crea un archivo utilizando un agente especializado.
    
    Args:
        description: Descripción del archivo a generar
        file_type: Tipo de archivo (html, css, js, py, json, md, txt)
        filename: Nombre del archivo
        agent_id: ID del agente especializado
        workspace_path: Ruta del workspace del usuario
        model: Modelo de IA a utilizar (openai, anthropic, gemini)
        
    Returns:
        dict: Resultado de la operación con claves success, file_path y content
    """
    try:
        # Debug logs
        logging.debug(f"Generando archivo con agente: {agent_id}")
        logging.debug(f"Tipo de archivo: {file_type}")
        logging.debug(f"Nombre de archivo: {filename}")
        logging.debug(f"Modelo: {model}")
        logging.debug(f"Descripción: {description}")
        
        # Obtener el prompt de sistema y nombre según el agente
        system_prompt = get_agent_system_prompt(agent_id)
        agent_name = get_agent_name(agent_id)
        
        # Preparar el prompt específico según el tipo de archivo
        file_type_prompt = ""
        if file_type == 'html' or '.html' in filename:
            file_type_prompt = """Genera un archivo HTML moderno y atractivo. 
            Usa las mejores prácticas de HTML5, CSS responsivo y, si es necesario, JavaScript moderno.
            Asegúrate de que el código sea válido, accesible y optimizado para móviles.
            El archivo debe usar Bootstrap para estilos y ser visualmente atractivo.
            Asegúrate de que el código esté completo y sea funcional, sin fragmentos o explicaciones adicionales."""
        elif file_type == 'css' or '.css' in filename:
            file_type_prompt = """Genera un archivo CSS moderno y eficiente.
            Utiliza las mejores prácticas, variables CSS, y enfoques responsivos.
            El código debe ser compatible con navegadores modernos, estar bien comentado,
            y seguir una estructura clara y mantenible.
            Asegúrate de que el código esté completo y sea funcional, sin fragmentos o explicaciones adicionales."""
        elif file_type == 'js' or '.js' in filename:
            file_type_prompt = """Genera un archivo JavaScript moderno y eficiente.
            Utiliza ES6+ con las mejores prácticas actuales. El código debe ser bien estructurado,
            comentado apropiadamente, y seguir patrones de diseño adecuados.
            Proporciona manejo de errores adecuado y optimización de rendimiento.
            Asegúrate de que el código esté completo y sea funcional, sin fragmentos o explicaciones adicionales."""
        elif file_type == 'py' or '.py' in filename:
            file_type_prompt = """Genera un archivo Python moderno y bien estructurado.
            Sigue PEP 8 y las mejores prácticas de Python. El código debe incluir docstrings,
            manejo de errores apropiado, y una estructura clara de funciones/clases.
            Utiliza enfoques Pythonic y aprovecha las características modernas del lenguaje.
            Asegúrate de que el código esté completo y sea funcional, sin fragmentos o explicaciones adicionales."""
        else:
            file_type_prompt = """Genera un archivo de texto plano con el contenido solicitado,
            bien estructurado y formateado de manera clara y legible.
            Asegúrate de que el contenido esté completo, sin fragmentos o explicaciones adicionales."""
            
        # Construir el prompt completo según el agente
        prompt = f"""Como {agent_name}, crea un archivo {file_type} completo y funcional que cumpla con el siguiente requerimiento:
        
        "{description}"
        
        {file_type_prompt}
        
        IMPORTANTE: 
        - Genera SOLO el código completo sin explicaciones, comentarios introductorios o conclusiones.
        - NO uses bloques de código markdown (```), solo genera el contenido directo del archivo.
        - Incluye todas las funcionalidades solicitadas y crea un diseño profesional si corresponde.
        - Si es un archivo HTML, asegúrate de incluir todos los elementos necesarios (DOCTYPE, html, head, body, etc.)
        - El código debe estar completo, compilar y funcionar correctamente.
        """
        
        # Log del prompt para depuración
        logging.debug(f"Prompt enviado al modelo: {prompt}")
        
        # Generar el contenido del archivo
        file_content = generate_content(prompt, system_prompt, model)
        
        # Verificar que se haya generado contenido
        if not file_content:
            return {
                'success': False,
                'error': 'El modelo no generó contenido para el archivo'
            }
            
        # Log del contenido generado para depuración
        logging.debug(f"Contenido generado (primeros 200 caracteres): {file_content[:200]}")
        
        # Extraer código del contenido si el modelo aún incluye markdown u otros elementos
        code_pattern = r"```(?:\w+)?\s*([\s\S]*?)\s*```"
        code_match = re.search(code_pattern, file_content)
        
        if code_match:
            file_content = code_match.group(1).strip()
            logging.debug("Se limpió el contenido usando el patrón de código")
            
        # Crear el archivo en el workspace del usuario
        file_path = os.path.join(workspace_path, filename)
        
        # Crear directorios intermedios si es necesario
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        # Obtener la ruta relativa para mostrar al usuario
        relative_path = os.path.relpath(file_path, workspace_path)
        
        return {
            'success': True,
            'file_path': relative_path,
            'content': file_content
        }
            
    except Exception as e:
        logging.error(f"Error generando contenido del archivo: {str(e)}")
        return {
            'success': False,
            'error': f'Error generando contenido del archivo: {str(e)}'
        }

def generate_response(user_message, agent_id="general", context=None, model="openai"):
    """
    Genera una respuesta usando el modelo de IA especificado.
    """
    try:
        system_prompt = get_agent_system_prompt(agent_id)
        agent_name = get_agent_name(agent_id)
        
        # Formatear el contexto y el mensaje para el prompt
        if context:
            context_str = "\n".join([
                f"{'Usuario' if msg['role'] == 'user' else agent_name}: {msg['content']}" 
                for msg in context
            ])
            prompt = f"""Historial de conversación:
            {context_str}
            
            Usuario: {user_message}
            
            Como {agent_name}, responde al último mensaje del usuario."""
        else:
            prompt = f"""Usuario: {user_message}
            
            Como {agent_name}, responde al mensaje del usuario."""
        
        # Generar respuesta según el modelo seleccionado
        if model == "anthropic" and os.environ.get('ANTHROPIC_API_KEY'):
            response = generate_with_anthropic(prompt, system_prompt)
        elif model == "gemini" and os.environ.get('GEMINI_API_KEY'):
            response = generate_with_gemini(prompt, system_prompt)
        else:
            # OpenAI por defecto
            response = generate_with_openai(prompt, system_prompt)
            
        return {
            'success': True,
            'response': response
        }
        
    except Exception as e:
        logging.error(f"Error generando respuesta: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def analyze_code(code, language="python", instructions="Mejorar el código", model="openai"):
    """
    Analiza y mejora código existente.
    
    Args:
        code: Código a analizar
        language: Lenguaje del código
        instructions: Instrucciones específicas para el análisis
        model: Modelo de IA a utilizar
        
    Returns:
        dict: Resultado del análisis con claves success, improved_code, explanations, suggestions
    """
    try:
        system_prompt = f"""Eres un experto programador de {language} especializado en revisar, mejorar y explicar código.
Tu tarea es analizar el código proporcionado, mejorarlo según las instrucciones, y explicar tus cambios.
Debes respetar la intención original del código, manteniendo su funcionalidad mientras lo mejoras."""
        
        prompt = f"""Analiza el siguiente código de {language}:
```{language}
{code}
```

Instrucciones específicas: {instructions}

Proporciona:
1. Una versión mejorada del código completo (no solo fragmentos)
2. Explicaciones claras de los cambios realizados
3. Sugerencias adicionales para futuras mejoras

IMPORTANTE: Tu respuesta debe tener este formato JSON:
{{
    "improved_code": "El código mejorado completo",
    "explanations": ["Explicación 1", "Explicación 2", ...],
    "suggestions": ["Sugerencia 1", "Sugerencia 2", ...]
}}
"""
        
        response = generate_content(prompt, system_prompt, model, temperature=0.3)
        
        # Intentar extraer JSON de la respuesta
        try:
            # Buscar un bloque JSON en la respuesta
            json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
            json_match = re.search(json_pattern, response)
            
            if json_match:
                import json
                result = json.loads(json_match.group(1))
            else:
                # Intentar parsear toda la respuesta como JSON
                import json
                result = json.loads(response)
                
            # Verificar que tenga las claves esperadas
            for key in ['improved_code', 'explanations', 'suggestions']:
                if key not in result:
                    result[key] = []
                    
            return {
                'success': True,
                'improved_code': result['improved_code'],
                'explanations': result['explanations'],
                'suggestions': result['suggestions']
            }
        except Exception as json_error:
            logging.error(f"Error parseando JSON de respuesta: {str(json_error)}")
            
            # Fallback: extraer código mejorado usando regex
            code_pattern = r"```(?:\w+)?\s*([\s\S]*?)\s*```"
            code_match = re.search(code_pattern, response)
            
            if code_match:
                improved_code = code_match.group(1).strip()
            else:
                improved_code = code  # Usar el código original si no se encuentra mejorado
                
            return {
                'success': True,
                'improved_code': improved_code,
                'explanations': ["Se procesó el código pero hubo un error al estructurar la respuesta."],
                'suggestions': ["Revisa el código manualmente para confirmar las mejoras."]
            }
                
    except Exception as e:
        logging.error(f"Error analizando código: {str(e)}")
        return {
            'success': False,
            'error': f'Error analizando código: {str(e)}'
        }

def process_natural_language_command(text, workspace_path, model="openai"):
    """
    Procesa una instrucción en lenguaje natural y determina la acción a realizar.
    
    Args:
        text: Texto de la instrucción
        workspace_path: Ruta del workspace del usuario
        model: Modelo de IA a utilizar
        
    Returns:
        dict: Resultado del procesamiento con la acción determinada
    """
    try:
        system_prompt = """Eres un asistente especializado en interpretar instrucciones en lenguaje natural 
y convertirlas en acciones específicas para un entorno de desarrollo. 
Tu tarea es determinar qué acción debe realizarse basándote en el texto proporcionado."""
        
        prompt = f"""Analiza la siguiente instrucción y determina qué acción debe realizarse:
"{text}"

Las posibles acciones son:
1. create_file - Crear un archivo
2. execute_command - Ejecutar un comando en terminal
3. answer_question - Responder una pregunta
4. unknown - La instrucción no corresponde a ninguna acción específica

Responde en formato JSON con la siguiente estructura:
{{
    "action": "La acción determinada (create_file, execute_command, answer_question, unknown)",
    "details": {{
        // Para create_file:
        "file_name": "Nombre del archivo a crear",
        "file_type": "Tipo de archivo (py, js, html, etc.)",
        "content_description": "Descripción del contenido a generar"
        
        // Para execute_command:
        "command": "El comando a ejecutar"
        
        // Para answer_question:
        "question": "La pregunta a responder"
    }}
}}
"""
        
        response = generate_content(prompt, system_prompt, model, temperature=0.3)
        
        # Extraer JSON de la respuesta
        try:
            # Buscar un bloque JSON en la respuesta
            json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
            json_match = re.search(json_pattern, response)
            
            if json_match:
                import json
                result = json.loads(json_match.group(1))
            else:
                # Intentar parsear toda la respuesta como JSON
                import json
                result = json.loads(response)
                
            action = result.get('action', 'unknown')
            details = result.get('details', {})
            
            # Procesar según la acción determinada
            if action == 'create_file':
                file_name = details.get('file_name', 'unnamed.txt')
                file_type = details.get('file_type', 'txt')
                content_description = details.get('content_description', text)
                
                # Asegurar que el nombre de archivo tenga la extensión correcta
                if not file_name.endswith('.' + file_type):
                    file_name += '.' + file_type
                
                # Usar la función de creación de archivo para generar el contenido
                result = create_file_with_agent(
                    description=content_description,
                    file_type=file_type,
                    filename=file_name,
                    agent_id='developer',  # Usar agente desarrollador por defecto
                    workspace_path=workspace_path,
                    model=model
                )
                
                if result['success']:
                    return {
                        'success': True,
                        'action': 'create_file',
                        'file_path': result['file_path'],
                        'content': result['content']
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error']
                    }
            
            elif action == 'execute_command':
                command = details.get('command', '')
                
                if not command:
                    return {
                        'success': False,
                        'error': 'No se pudo determinar el comando a ejecutar'
                    }
                
                import subprocess
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=workspace_path
                )
                
                stdout, stderr = process.communicate(timeout=30)
                status = process.returncode
                
                return {
                    'success': True,
                    'action': 'execute_command',
                    'command': command,
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                    'status': status
                }
            
            elif action == 'answer_question':
                question = details.get('question', text)
                
                # Generar respuesta a la pregunta
                response_result = generate_response(
                    user_message=question,
                    agent_id='general',  # Usar agente general para preguntas
                    model=model
                )
                
                if response_result['success']:
                    return {
                        'success': True,
                        'action': 'answer_question',
                        'question': question,
                        'answer': response_result['response']
                    }
                else:
                    return {
                        'success': False,
                        'error': response_result['error']
                    }
            
            else:  # unknown o cualquier otro caso
                return {
                    'success': False,
                    'error': 'No se pudo determinar una acción específica para esta instrucción'
                }
                
        except Exception as json_error:
            logging.error(f"Error parseando respuesta: {str(json_error)}")
            return {
                'success': False,
                'error': f'Error procesando la instrucción: {str(json_error)}'
            }
                
    except Exception as e:
        logging.error(f"Error procesando instrucción en lenguaje natural: {str(e)}")
        return {
            'success': False,
            'error': f'Error procesando instrucción: {str(e)}'
        }

