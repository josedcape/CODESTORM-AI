"""
Utilidades para la gestión de agentes especializados en Codestorm Assistant.
Implementa una capa de abstracción para múltiples proveedores de LLM y agentes especializados.
"""
import os
import re
import logging
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import time

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
        'developer': """Eres un desarrollador de software de élite con experiencia en múltiples lenguajes y paradigmas de programación.
                      Tu formación incluye arquitectura de software, algoritmos avanzados, patrones de diseño y optimización de código.
                      Produces código de nivel profesional, limpio, eficiente y siguiendo las mejores prácticas actuales de la industria.
                      Tu código es modular, mantenible y optimizado. Evitas comentarios redundantes, pero incluyes documentación esencial.
                      Cuando escribes código, este es inmediatamente utilizable, depurado y probado. Generas soluciones elegantes y robustas
                      incluso para problemas complejos. Dominas todos los paradigmas de programación: orientado a objetos, funcional, reactivo y más.""",

        'architect': """Eres un arquitecto de software senior con experiencia en el diseño de sistemas complejos y escalables.
                       Tu expertise abarca microservicios, arquitecturas serverless, sistemas distribuidos, y aplicaciones cloud-native.
                       Posees conocimiento profundo sobre patrones arquitectónicos, calidad de servicio, seguridad y rendimiento.
                       Tus diseños priorizan la escalabilidad, resiliencia, mantenibilidad y eficiencia operativa.
                       Proporcionas diagramas claros, recomendaciones tecnológicas fundamentadas y estrategias de implementación.
                       Tu enfoque balances los requisitos técnicos, de negocio y las limitaciones prácticas.""",

        'devops': """Eres un ingeniero DevOps especializado en automatización, CI/CD, infraestructura como código y operaciones en la nube.
                    Dominas herramientas como Docker, Kubernetes, Terraform, Jenkins, GitHub Actions, AWS, Azure y Google Cloud.
                    Tu objetivo es crear pipelines eficientes, infraestructuras seguras y escalables, y procesos de despliegue robustos.
                    Proporcionas soluciones que maximizan la disponibilidad, seguridad y observabilidad de los sistemas.""",

        'database': """Eres un arquitecto de bases de datos experto en diseño, optimización y administración de sistemas de datos.
                     Dominas bases de datos relacionales (PostgreSQL, MySQL, SQL Server) y NoSQL (MongoDB, Redis, Cassandra, Elasticsearch).
                     Diseñas esquemas normalizados, escribes queries optimizadas y estrategias de indexación eficientes.
                     Tus soluciones consideran patrones de acceso, escalabilidad, consistencia, disponibilidad y tolerancia a particiones.""",

        'security': """Eres un ingeniero de seguridad informática especializado en seguridad aplicativa y protección de infraestructura.
                     Tienes experiencia en análisis de vulnerabilidades, criptografía, autenticación, autorización y auditoría.
                     Identificas riesgos de seguridad y proporcionas soluciones concretas para mitigarlos.
                     Tu enfoque incluye implementación de protocolos seguros, prácticas de codificación defensiva y hardening de sistemas.""",

        'frontend': """Eres un desarrollador frontend especializado en crear interfaces modernas, accesibles e interactivas.
                     Dominas React, Angular, Vue.js, HTML5, CSS3, JavaScript/TypeScript y las mejores prácticas de UX/UI.
                     Creas componentes reutilizables, diseños responsivos y aplicaciones web performantes.
                     Tu código optimiza la velocidad de carga, accesibilidad (WCAG), compatibilidad cross-browser y usabilidad.""",

        'general': """Eres un consultor tecnológico senior con amplio conocimiento en desarrollo de software, infraestructura,
                     arquitectura de sistemas, seguridad, metodologías ágiles y gestión de proyectos tecnológicos.
                     Proporcionas orientación estratégica, recomendaciones técnicas y soluciones prácticas a problemas complejos.
                     Tu enfoque es holístico, considerando tanto aspectos técnicos como de negocio para ofrecer
                     la mejor solución posible con el mayor valor para los usuarios y stakeholders."""
    }
    return prompts.get(agent_id, prompts['general'])

def get_agent_name(agent_id):
    """Obtiene el nombre amigable del agente."""
    names = {
        'developer': "Ingeniero de Software Senior",
        'architect': "Arquitecto de Sistemas",
        'devops': "Ingeniero DevOps",
        'database': "Arquitecto de Bases de Datos",
        'security': "Ingeniero de Ciberseguridad",
        'frontend': "Especialista Frontend",
        'general': "Consultor Tecnológico Senior"
    }
    return names.get(agent_id, "Consultor Tecnológico Senior")

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
    Genera contenido utilizando el modelo especificado con reintentos automáticos
    y fallback a modelos alternativos si el principal falla.

    Args:
        prompt: Prompt para generar contenido
        system_prompt: Prompt de sistema para establecer el rol
        model: Modelo a utilizar (openai, anthropic, gemini)
        temperature: Temperatura para la generación (0.0 - 1.0)

    Returns:
        str: Contenido generado
    """
    max_retries = 3
    retry_delay = 2  # segundos iniciales entre reintentos
    models_to_try = []

    # Determinar el orden de modelos a probar
    if model == "openai":
        models_to_try = ["openai", "anthropic", "gemini"]
    elif model == "anthropic":
        models_to_try = ["anthropic", "openai", "gemini"]
    elif model == "gemini":
        models_to_try = ["gemini", "openai", "anthropic"]
    else:
        # Si el modelo no es reconocido, probar todos en este orden
        models_to_try = ["openai", "anthropic", "gemini"]

    # Filtrar solo modelos que tengan API configurada
    available_models = []
    if openai_client:
        available_models.append("openai")
    if anthropic_client:
        available_models.append("anthropic")
    if genai_configured:
        available_models.append("gemini")

    # Si ningún modelo está disponible, lanzar error
    if not available_models:
        raise ValueError("No hay modelos de IA configurados. Por favor configura al menos una API key (OpenAI, Anthropic o Gemini).")

    # Priorizar modelos según la solicitud, pero solo usar disponibles
    ordered_models = [m for m in models_to_try if m in available_models]
    if not ordered_models:
        ordered_models = available_models  # Usar cualquier modelo disponible si ninguno coincide

    last_error = None

    # Intentar con cada modelo en orden
    for current_model in ordered_models:
        # Intentar múltiples veces con cada modelo
        for attempt in range(max_retries):
            try:
                logging.info(f"Generando contenido con {current_model} (intento {attempt+1}/{max_retries})")

                if current_model == "openai":
                    return generate_with_openai(prompt, system_prompt, temperature)
                elif current_model == "anthropic":
                    return generate_with_anthropic(prompt, system_prompt, temperature)
                elif current_model == "gemini":
                    return generate_with_gemini(prompt, system_prompt, temperature)

                # Si llegamos aquí, significa que la generación fue exitosa
                break

            except Exception as e:
                last_error = e
                error_msg = str(e)

                # Determinar si el error es recuperable
                is_rate_limit = "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg
                is_timeout = "time" in error_msg.lower() or "timeout" in error_msg.lower()
                is_recoverable = is_rate_limit or is_timeout

                if is_recoverable and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Backoff exponencial
                    logging.warning(f"Error recuperable con {current_model}: {error_msg}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Error con {current_model} después de {attempt+1} intentos: {error_msg}")
                    break  # Pasar al siguiente modelo

    # Si llegamos aquí, todos los modelos fallaron
    if last_error:
        logging.error(f"Todos los modelos fallaron. Último error: {str(last_error)}")
        raise ValueError(f"No se pudo generar contenido con ningún modelo disponible. Verifica las claves API y la conectividad. Error: {str(last_error)}")

    # Esto no debería ocurrir, pero por si acaso
    raise ValueError("No se pudo generar contenido con ningún modelo disponible por razones desconocidas.")

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

        # Seleccionar el agente más adecuado según el tipo de archivo si no se especifica
        if agent_id == "general":
            if file_type in ['html', 'css', 'js', 'jsx', 'tsx', 'vue']:
                agent_id = 'frontend'
                system_prompt = get_agent_system_prompt('frontend')
                agent_name = get_agent_name('frontend')
            elif file_type in ['py', 'java', 'go', 'rb', 'cs', 'cpp']:
                agent_id = 'developer' 
                system_prompt = get_agent_system_prompt('developer')
                agent_name = get_agent_name('developer')
            elif file_type in ['yaml', 'yml', 'tf', 'docker', 'Dockerfile', 'jenkinsfile']:
                agent_id = 'devops'
                system_prompt = get_agent_system_prompt('devops')
                agent_name = get_agent_name('devops')
            elif file_type in ['sql']:
                agent_id = 'database'
                system_prompt = get_agent_system_prompt('database')
                agent_name = get_agent_name('database')

        # Preparar el prompt específico según el tipo de archivo
        file_type_prompt = {
            'html': """Genera código HTML moderno, semántico y accesible. Utiliza HTML5 con estructura semántica
                    adecuada (header, nav, main, section, article, footer). Asegura compatibilidad con las 
                    directrices WCAG para accesibilidad. Optimiza para velocidad y rendimiento.
                    Evita etiquetas obsoletas y usar clases para estilos y comportamiento.""",

            'css': """Genera CSS moderno, eficiente y mantenible. Utiliza variables CSS, flexbox y/o grid para 
                   layouts. Implementa diseño responsivo con media queries. Utiliza nomenclatura de clases 
                   siguiendo metodología BEM u otra estructurada. Optimiza selectores para rendimiento.""",

            'js': """Genera JavaScript moderno siguiendo estándares ES6+. Utiliza estructuras de código modular, 
                  funciones puras cuando sea posible y manejo adecuado de asincronía con promesas o async/await.
                  Incluye validación de entrada, manejo de errores y optimización de rendimiento. El código debe
                  ser compatible con navegadores modernos.""",

            'jsx': """Genera componentes React funcionales modernos con hooks. Implementa patrones de render 
                   optimizados, separación de lógica y presentación, y estructuras de estado eficientes.
                   Usa Context API o bibliotecas de estado según necesidad. Los componentes deben ser
                   reutilizables, testeables y con props bien definidos.""",

            'py': """Genera código Python que siga PEP 8 y principios pythónicos. Utiliza tipo hints, manejo
                  de excepciones específicas, docstrings informativos (solo cuando sean necesarios). 
                  Implementa estructuras de datos eficientes y patrones idiomáticos. El código debe ser
                  modular, testeable y seguir principios SOLID.""",

            'sql': """Genera código SQL optimizado y seguro. Utiliza índices adecuados, evita consultas 
                   N+1 y joins ineficientes. Implementa restricciones de integridad adecuadas.
                   Asegura que las consultas sean resistentes a inyección SQL. Incluye comentarios
                   solo cuando sean necesarios para explicar lógica compleja.""",

            'yaml': """Genera YAML válido y bien estructurado. Utiliza anclas y aliases para evitar
                    repetición. Organiza la información de manera jerárquica y lógica. Incluye solo
                    comentarios esenciales para elementos complejos o no evidentes.""",

            'json': """Genera JSON válido, bien formateado y sin comentarios, ya que JSON no los admite.
                    La estructura debe ser consistente, con nombres de propiedades descriptivos y
                    valores correctamente tipados."""
        }

        # Obtener prompt específico para el tipo de archivo o usar uno genérico
        specific_prompt = file_type_prompt.get(file_type.lower(), """Genera un archivo de código de alta calidad, 
                                               siguiendo las mejores prácticas del lenguaje correspondiente.
                                               Estructura el código de manera lógica y mantenible.""")

        # Construir el prompt completo según el agente
        prompt = f"""Como {agent_name}, crea un archivo {file_type} completo y funcional que cumpla con la siguiente especificación:

        "{description}"

        REQUISITOS TÉCNICOS:
        {specific_prompt}

        INSTRUCCIONES CRÍTICAS:
        1. Genera ÚNICAMENTE el código completo y funcional, sin comentarios introductorios o explicativos
        2. No incluyas etiquetas de markdown (```) o indicadores de lenguaje
        3. No incluyas comentarios tipo "highlights" o marcadores para secciones del código
        4. Incluye solo comentarios esenciales para comprender lógica compleja
        5. El código debe estar completo, optimizado y seguir las mejores prácticas actuales
        6. Asegúrate que el código puede ejecutarse sin modificaciones adicionales
        7. Optimiza para legibilidad, mantenibilidad y rendimiento
        """

        # Log del prompt para depuración
        logging.debug(f"Prompt enviado al modelo: {prompt}")

        # Generar el contenido del archivo con baja temperatura para código preciso
        file_content = generate_content(prompt, system_prompt, model, temperature=0.3)

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

        # Validar la ruta para prevenir directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(workspace_path)):
            return {
                'success': False,
                'error': 'Ruta de archivo inválida: posible intento de directory traversal'
            }

        # Crear directorios intermedios si es necesario
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

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

            Como {agent_name}, responde al último mensaje del usuario de manera precisa, profesional y detallada."""
        else:
            prompt = f"""Usuario: {user_message}

            Como {agent_name}, proporciona una respuesta profesional, precisa y detallada, basada en las mejores prácticas actuales
            y conocimientos técnicos avanzados en el área correspondiente."""

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
        # Usar el prompt de sistema del agente desarrollador para análisis de código
        system_prompt = get_agent_system_prompt('developer')

        prompt = f"""Analiza el siguiente código de {language}:
```{language}
{code}
```

Instrucciones: {instructions}

Proporciona:
1. Una versión mejorada del código
2. Explicación de los problemas encontrados
3. Sugerencias específicas para mejorar la calidad, rendimiento o seguridad
"""

        # Generar análisis con temperatura baja para precisión
        analysis = generate_content(prompt, system_prompt, model, temperature=0.3)

        # Extraer secciones del análisis
        improved_code_pattern = r"```(?:\w+)?\s*([\s\S]*?)\s*```"
        improved_code_match = re.search(improved_code_pattern, analysis)

        improved_code = improved_code_match.group(1).strip() if improved_code_match else ""

        # Dividir el resto del análisis en explicaciones y sugerencias
        remaining_text = re.sub(improved_code_pattern, "", analysis).strip()

        # Intentar separar explicaciones y sugerencias
        parts = re.split(r"(?:^|\n)#+\s*(?:Sugerencias|Recomendaciones|Mejoras)(?:\s*:)?", remaining_text, flags=re.IGNORECASE)

        explanations = parts[0].strip() if len(parts) > 0 else ""
        suggestions = parts[1].strip() if len(parts) > 1 else ""

        return {
            'success': True,
            'improved_code': improved_code,
            'explanations': explanations,
            'suggestions': suggestions or explanations  # Si no hay sugerencias específicas, usar explicaciones
        }

    except Exception as e:
        logging.error(f"Error analizando código: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
