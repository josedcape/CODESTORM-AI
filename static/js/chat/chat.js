/**
 * Codestorm Assistant - Módulo de Chat
 * Versión: 2.0.1 (Optimizado)
 * Fecha: 25-04-2025
 */

// Namespace principal para la aplicación
window.app = window.app || {};
window.app.chat = window.app.chat || {};

// Configuración de endpoints de API
window.app.chat.apiEndpoints = {
    chat: '/api/chat',
    fallback: '/api/generate',
    health: '/api/health',
    processCode: '/api/process_code',
    execute: '/api/execute_command',
    files: '/api/files'
};

/**
 * Función para logging silencioso (debug)
 * @param {...any} args - Argumentos a loggear
 */
function silentLog(...args) {
    if (window.app && window.app.chat && window.app.chat.debugMode) {
        console.log('[Chat]', ...args);
    }
}

/**
 * Función para copiar el contenido de un mensaje al portapapeles
 * @param {string} messageId - El id del mensaje a copiar
 */
function copyToClipboard(messageId, messageType) {
    try {
        const messageContent = document.querySelector(`#${messageId} .message-content`);
        if (!messageContent) {
            throw new Error('No se encontró el contenido del mensaje');
        }

        // Crear un elemento de texto temporal para copiar el contenido
        const textArea = document.createElement('textarea');
        textArea.value = messageContent.innerText || messageContent.textContent;
        document.body.appendChild(textArea);

        // Seleccionar y copiar el contenido del área de texto
        textArea.select();
        document.execCommand('copy');

        // Eliminar el área de texto temporal
        document.body.removeChild(textArea);

        // Proveer feedback al usuario (por ejemplo, cambiar el texto del botón)
        const copyButton = document.getElementById(`copy-btn-${messageId}`);
        if (copyButton) {
            copyButton.innerHTML = '<i class="bi bi-check"></i> Copiado';
            setTimeout(() => {
                copyButton.innerHTML = '<i class="bi bi-clipboard"></i>';
            }, 2000); // Restablecer el ícono después de 2 segundos
        }

        silentLog(`Mensaje copiado: ${textArea.value}`);
    } catch (error) {
        console.error('Error al copiar el mensaje:', error);
        alert('Error al copiar el mensaje');
    }
}

/**
 * Inicializa el chat y configura los manejadores de eventos
 */
window.initializeChat = function() {
    // Inicializar la estructura completa de window.app
    window.app = window.app || {};
    window.app.chat = window.app.chat || {};

    // Inicializar propiedades básicas del chat
    window.app.chat.context = window.app.chat.context || [];
    window.app.chat.chatMessageId = window.app.chat.chatMessageId || 0;
    window.app.chat.debugMode = window.app.chat.debugMode || false;
    window.app.chat.elements = window.app.chat.elements || {};

    // Configurar modelos disponibles
    window.app.chat.availableModels = window.app.chat.availableModels || {
        'openai': 'GPT-4o - Modelo avanzado de OpenAI con excelente seguimiento de instrucciones',
        'anthropic': 'Claude 3.5 Sonnet - Especializado en desarrollo y automatización con alto contexto',
        'gemini': 'Gemini 1.5 Pro - Análisis de grandes bases de código con 1M de tokens'
    };

    // Modelos completos disponibles (para referencia futura)
    window.app.chat.fullModelList = {
        'gpt-4o': 'GPT-4o - Modelo avanzado de OpenAI con excelente seguimiento de instrucciones',
        'gpt-o3': 'GPT-o3 - Versión optimizada para generación y análisis de código',
        'claude-3-opus': 'Claude 3 Opus - Modelo premium de Anthropic con razonamiento avanzado',
        'claude-3.7-sonnet': 'Claude 3.7 Sonnet - Especializado en desarrollo y automatización con alto contexto',
        'claude-code': 'Claude Code - Experto en refactorización, debugging e integración Git',
        'gpt-4.1-std': 'GPT-4.1 Standard - Modelo principal de OpenAI con 1M de tokens de contexto',
        'gpt-4.1-mini': 'GPT-4.1 Mini - Versión más ligera y rápida de GPT-4.1',
        'gpt-4.1-nano': 'GPT-4.1 Nano - Versión ultraligera para respuestas rápidas',
        'gemini-1.5-pro': 'Gemini 1.5 Pro - Análisis de grandes bases de código con 1M de tokens',
        'gemini-2.0-flash': 'Gemini 2.0 Flash - Alta velocidad y eficiencia con entrada multimodal',
        'gemini-1.0-ultra': 'Gemini 1.0 Ultra - Especializado en tareas complejas y competencias de programación',
        'gemma': 'Gemma - Modelo ligero open source de Google para código y dispositivos'
    };

    // Configurar agentes disponibles
    window.app.chat.availableAgents = window.app.chat.availableAgents || {
        'developer': {
            name: 'Agente de Desarrollo',
            description: 'Experto en desarrollo frontend y soluciones de código profesionales',
            capabilities: [
                'Diseño y desarrollo de interfaces web responsivas',
                'Optimización de rendimiento y accesibilidad',
                'Integración de frameworks y librerías modernas',
                'Automatización y CI/CD para proyectos',
                'Generación de código escalable y mantenible'
            ],
            icon: 'code-slash'
        },
        'architect': {
            name: 'Agente de Arquitectura',
            description: 'Diseñador de arquitecturas escalables y optimizadas',
            capabilities: [
                'Definición de estructura del proyecto',
                'Selección de tecnologías y frameworks',
                'Asesoría en elección de bases de datos',
                'Implementación de microservicios',
                'Planificación de UI/UX y patrones de diseño'
            ],
            icon: 'diagram-3'
        },
        'advanced': {
            name: 'Agente Avanzado de Software',
            description: 'Especialista en integraciones complejas y funciones avanzadas',
            capabilities: [
                'Gestión de APIs y microservicios',
                'Optimización de backend',
                'Automatización avanzada de procesos',
                'Manejo de autenticación y autorización',
                'Conexiones a la nube y servicios de terceros'
            ],
            icon: 'gear-wide-connected'
        },
        'general': {
            name: 'Asistente General',
            description: 'Asistente versátil para diversas tareas de programación',
            capabilities: [
                'Resolución de consultas generales',
                'Asistencia en proyectos diversos',
                'Explicación de conceptos técnicos',
                'Recomendaciones de buenas prácticas',
                'Orientación en elección de tecnologías'
            ],
            icon: 'person-check'
        }
    };

    // Configurar valores por defecto
    window.app.chat.activeModel = window.app.chat.activeModel || 'gpt-4';
    window.app.chat.activeAgent = window.app.chat.activeAgent || 'general';

    // Inicializar logs silenciosamente
    silentLog('Inicializando chat con configuración optimizada...');

    // Configurar selectores y elementos de la UI
    setupUIElements();

    // Verificar conexión con el servidor - versión mejorada
    checkServerConnection();

    // Verificar modelos disponibles
    checkAvailableModels();

    // Inicializar características avanzadas
    setupDocumentFeatures();

    // Cargar highlight.js si es necesario
    loadHighlightJS();
};

// Función para enviar mensajes, configurar y manejar la lógica del chat
async function sendMessage() {
    // Asegurarse de que window.app y window.app.chat estén inicializados
    if (!window.app || !window.app.chat) {
        console.error("Error: window.app.chat no está inicializado");
        addSystemMessage("Error: Inicialización incompleta. Recargando interfaz...");
        // Reintentar setup
        setupUIElements();
    }

    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    if (!messageInput) {
        console.error("Elemento de entrada de mensaje no encontrado");
        return;
    }

    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    // Añadir mensaje del usuario al chat y contexto
    addUserMessage(userMessage);

    // Limpiar input y ajustar altura
    messageInput.value = '';
    adjustTextareaHeight(messageInput);
    messageInput.focus();

    // Deshabilitar botón mientras se procesa
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.style.opacity = '0.6';
    }

    // Mantener el contexto en un tamaño razonable (últimos 10 mensajes)
    const contextToSend = window.app.chat.context.slice(-10);

    // Preparar datos para enviar al servidor
    const requestData = {
        message: userMessage,
        agent_id: window.app.chat.activeAgent,
        model: window.app.chat.activeModel,
        context: contextToSend
    };

    // Mostrar indicador de carga
    const loadingMessageId = addLoadingMessage();

    try {
        const response = await fetch(window.app.chat.apiEndpoints.chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();
        silentLog('Respuesta recibida:', data);

        // Eliminar indicador de carga
        removeLoadingMessage(loadingMessageId);

        // Habilitar botón de envío
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.style.opacity = '1';
        }

        // Verificar diferentes formatos de respuesta
        if (data.response) {
            addAgentMessage(data.response, data.agent_id || window.app.chat.activeAgent);
        }
    } catch (error) {
        // Eliminar indicador de carga y habilitar botón
        removeLoadingMessage(loadingMessageId);
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.style.opacity = '1';
        }
        silentLog('Error al enviar mensaje:', error);
        addSystemMessage(`Error de conexión: ${error.message}`);
    }
}
