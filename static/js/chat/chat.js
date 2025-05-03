/**
 * Codestorm Assistant - Módulo de Chat
 * Versión: 2.0.1 (Optimizado)
 * Fecha: 25-04-2025
 */

// Namespace principal para la aplicación
window.app = window.app || {};
window.app.chat = window.app.chat || {};

// Asegurarse de que los endpoints API estén definidos
if (!window.app.apiEndpoints && !window.app.chat.apiEndpoints) {
    window.app.apiEndpoints = {
        chat: '/api/assistant/chat', // Corrected endpoint
        fallback: '/api/generate',
        health: '/api/health',
        processCode: '/api/process_code',
        execute: '/api/execute_command',
        files: '/api/files'
    };

    // Asignar endpoints al chat
    window.app.chat.apiEndpoints = window.app.apiEndpoints;
    console.log('Endpoints API inicializados:', window.app.chat.apiEndpoints);
}

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

    // Intentar encontrar el elemento de entrada con diferentes IDs posibles
    const messageInput = document.getElementById('message-input') || 
                         document.getElementById('assistant-chat-input') || 
                         document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button') || 
                       document.getElementById('send-assistant-message');

    if (!messageInput) {
        console.error("Elemento de entrada de mensaje no encontrado");
        addSystemMessage("Error: El elemento de entrada de mensaje no se encuentra. Por favor, recarga la página.");
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
    showLoadingIndicator();

    try {
        // Verificar que el endpoint existe y usar uno que funcione
        const apiEndpoint = '/api/chat'; // Usar directamente el endpoint correcto

        console.log('Enviando mensaje al endpoint:', apiEndpoint);

        // Enviar solicitud al servidor
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Error de servidor (${response.status}): ${errorData.message || response.statusText}`);
        }

        const data = await response.json();
        silentLog('Respuesta recibida:', data);

        // Eliminar indicador de carga
        removeLoadingIndicator();

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
        removeLoadingIndicator();
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.style.opacity = '1';
        }
        silentLog('Error al enviar mensaje:', error);
        addSystemMessage(`Error de conexión: ${error.message}`);
    }
}

/**
 * Añade un mensaje del usuario al chat
 * @param {string} message - El contenido del mensaje
 */
function addUserMessage(message) {
    if (!message) return;

    // Generar ID único para el mensaje
    const messageId = `msg-${Date.now()}-${window.app.chat.chatMessageId++}`;

    // HTML del mensaje
    const messageHTML = `
        <div id="${messageId}" class="message user-message">
            <div class="message-sender">Tú</div>
            <div class="message-content">${escapeHtml(message)}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;

    // Añadir al chat y al contexto
    appendMessageToChat(messageHTML);
    window.app.chat.context.push({
        role: 'user',
        content: message
    });

    // Scroll automático
    scrollToBottom();
}

/**
 * Añade un mensaje del agente al chat
 * @param {string} message - El contenido del mensaje
 * @param {string} agentId - El ID del agente que responde
 */
function addAgentMessage(message, agentId) {
    if (!message) return;

    // Obtener información del agente
    const agentName = getAgentName(agentId || window.app.chat.activeAgent);

    // Generar ID único para el mensaje
    const messageId = `msg-${Date.now()}-${window.app.chat.chatMessageId++}`;

    // Formatear el mensaje (procesar código, enlaces, etc.)
    const formattedMessage = formatMessage(message);

    // HTML del mensaje
    const messageHTML = `
        <div id="${messageId}" class="message assistant-message">
            <div class="message-sender">${agentName}</div>
            <div class="message-content">${formattedMessage}</div>
            <div class="message-actions">
                <button id="copy-btn-${messageId}" class="copy-button" onclick="copyToClipboard('${messageId}')">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;

    // Añadir al chat y al contexto
    appendMessageToChat(messageHTML);
    window.app.chat.context.push({
        role: 'assistant',
        content: message
    });

    // Aplicar highlight.js a bloques de código
    try {
        if (window.hljs) {
            document.querySelectorAll(`#${messageId} pre code`).forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    } catch (error) {
        console.warn('Error al aplicar highlight.js:', error);
    }

    // Scroll automático
    scrollToBottom();
}

/**
 * Añade un mensaje del sistema al chat
 * @param {string} message - El contenido del mensaje
 */
function addSystemMessage(message) {
    if (!message) return;

    // Generar ID único para el mensaje
    const messageId = `system-${Date.now()}-${window.app.chat.chatMessageId++}`;

    // HTML del mensaje
    const messageHTML = `
        <div id="${messageId}" class="message system-message">
            <div class="message-content">${message}</div>
        </div>
    `;

    // Añadir al chat
    appendMessageToChat(messageHTML);

    // Scroll automático
    scrollToBottom();
}

/**
 * Añade un HTML de mensaje al contenedor de chat
 * @param {string} messageHTML - El HTML del mensaje a añadir
 */
function appendMessageToChat(messageHTML) {
    const messagesContainer = window.app.chat.elements.messagesContainer || 
                             document.getElementById('messages-container') || 
                             document.getElementById('chat-messages');

    if (messagesContainer) {
        // Añadir mensaje al final del contenedor
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    } else {
        console.error('No se encontró el contenedor de mensajes');
    }
}

/**
 * Formatea un mensaje para mostrar código, enlaces, etc.
 * @param {string} message - El mensaje a formatear
 * @returns {string} - El mensaje formateado con HTML
 */
function formatMessage(message) {
    if (!message) return '';

    // Escapar HTML para evitar inyección de código
    let formatted = escapeHtml(message);

    // Formatear bloques de código
    formatted = formatted.replace(/```([\s\S]+?)```/g, function(match, code) {
        // Detectar lenguaje si está especificado
        const langMatch = code.match(/^([a-zA-Z]+)\n([\s\S]+)$/);

        if (langMatch) {
            const language = langMatch[1];
            const codeContent = langMatch[2];
            return `<pre><code class="language-${language}">${codeContent}</code></pre>`;
        } else {
            return `<pre><code>${code}</code></pre>`;
        }
    });

    // Formatear código en línea
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Formatear enlaces
    formatted = formatted.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');

    // Convertir saltos de línea en <br>
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

/**
 * Hacer scroll al final del contenedor de mensajes
 */
function scrollToBottom() {
    const messagesContainer = window.app.chat.elements.messagesContainer || 
                             document.getElementById('messages-container') || 
                             document.getElementById('chat-messages');

    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

/**
 * Obtiene el nombre del agente a partir de su ID
 * @param {string} agentId - ID del agente
 * @returns {string} - Nombre del agente
 */
function getAgentName(agentId) {
    const agents = window.app.chat.availableAgents || {};
    return (agents[agentId] && agents[agentId].name) || 'Asistente';
}

/**
 * Escapa caracteres HTML para evitar inyección de código
 * @param {string} text - Texto a escapar
 * @returns {string} - Texto escapado
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Obtiene la hora actual formateada
 * @returns {string} - Hora actual formateada
 */
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

/**
 * Carga highlight.js para resaltado de código
 */
function loadHighlightJS() {
    // Verificar si ya está cargado
    if (window.hljs) {
        silentLog('highlight.js ya está cargado');
        return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
        try {
            // Crear script para highlight.js
            const highlightScript = document.createElement('script');
            highlightScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js';
            const codeBlockRegex = /```([a-z]*)\n([\s\S]+?)```/g;

            // Callback cuando el script se carga
            highlightScript.onload = function() {
                // Crear link para CSS de highlight.js
                const highlightCSS = document.createElement('link');
                highlightCSS.rel = 'stylesheet';
                highlightCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css';

                // Añadir CSS
                document.head.appendChild(highlightCSS);

                silentLog('highlight.js cargado correctamente');

                // Aplicar highlight a todos los bloques de código existentes
                document.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });

                resolve();
            };

            // Manejar errores
            highlightScript.onerror = function(err) {
                console.error('Error al cargar highlight.js:', err);
                reject(err);
            };

            // Añadir script al DOM
            document.head.appendChild(highlightScript);

        } catch (error) {
            console.error('Error al configurar highlight.js:', error);
            reject(error);
        }
    });
}

/**
 * Configurar elementos de la UI y referencias
 */
function setupUIElements() {
    // Inicializar el objeto elements si no existe
    if (!window.app.chat.elements) {
        window.app.chat.elements = {};
    }

    // Obtener referencias a los elementos de la UI
    window.app.chat.elements.messagesContainer = document.getElementById('messages-container') || 
                                              document.getElementById('assistant-chat-messages') || 
                                              document.getElementById('chat-messages');
    window.app.chat.elements.messageInput = document.getElementById('message-input') || 
                                         document.getElementById('assistant-chat-input');
    window.app.chat.elements.sendButton = document.getElementById('send-button') || 
                                       document.getElementById('send-assistant-message');

    // Verificar si los elementos necesarios están presentes
    const missingElements = [];
    if (!window.app.chat.elements.panel) missingElements.push('panel');
    if (!window.app.chat.elements.button) missingElements.push('botón de chat');
    if (!window.app.chat.elements.input) missingElements.push('campo de entrada');
    if (!window.app.chat.elements.send) missingElements.push('botón de enviar');
    if (!window.app.chat.elements.messages) missingElements.push('contenedor de mensajes');

    console.log('Elementos encontrados:', window.app.chat.elements);

    // Agregar manejadores de eventos solo si los elementos existen
    if (window.app.chat.elements.sendButton) {
        window.app.chat.elements.sendButton.addEventListener('click', sendMessage);
    }

    if (window.app.chat.elements.messageInput) {
        window.app.chat.elements.messageInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });

        // Ajustar altura inicial del textarea
        adjustTextareaHeight(window.app.chat.elements.messageInput);
    }

    silentLog('Elementos de la UI configurados');
}


function addLoadingMessage() {
    const messageId = `loading-${Date.now()}-${window.app.chat.chatMessageId++}`;
    const messageHTML = `
        <div id="${messageId}" class="message loading-message">
            <div class="message-content">Cargando...</div>
        </div>
    `;
    appendMessageToChat(messageHTML);
    scrollToBottom();
    return messageId;
}

function removeLoadingMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

// Verificar conexión con el servidor
function checkServerConnection() {
    // Intentar primero el endpoint principal, luego el simple si falla
    return fetch('/api/health')
        .then(response => {
            if (!response.ok) {
                console.warn(`Health check returned status: ${response.status}, trying simple endpoint`);
                // Si falla, intentar con el endpoint simple
                return fetch('/health').then(r => {
                    if (!r.ok) {
                        console.error('Both health checks failed');
                        throw new Error('Error de conexión al servidor: ' + response.status);
                    }
                    return r.json();
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status !== 'ok' && data.status !== 'limited') {
                throw new Error('Servidor no disponible: ' + data.status);
            }
            // También aceptar estado 'limited' para funcionalidad básica
            return data;
        })
        .catch(error => {
            console.error('Error al verificar la conexión con el servidor:', error);
            // Si falla todo, intentar continuar con funcionalidad limitada
            window.serverOffline = true;
            throw error;
        });
}

function checkAvailableModels() {
    //Simulación de verificación de modelos.  En un entorno real, se haría una llamada a la API.
    silentLog('Modelos disponibles:', window.app.chat.availableModels);
}

function setupDocumentFeatures() {
    //Añadir cualquier característica adicional al documento aquí.
    silentLog('Características del documento configuradas');
}

function adjustTextareaHeight(textarea) {
    if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
    }
}

// Función para mostrar el indicador de carga en lugar de "Cargando..."
function showLoadingIndicator() {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;

    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'message-container loading-message';
    loadingMessage.id = 'loading-indicator';

    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';

    // Crear los tres puntos de animación
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        typingIndicator.appendChild(dot);
    }

    loadingMessage.appendChild(typingIndicator);
    messagesContainer.appendChild(loadingMessage);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Configurar el selector de agentes personalizado
function setupAgentSelector() {
    const agentOptions = document.querySelectorAll('.agent-option');
    const agentSelect = document.getElementById('agent-select');

    if (!agentOptions.length || !agentSelect) return;

    agentOptions.forEach(option => {
        option.addEventListener('click', function() {
            const value = this.dataset.value;

            // Actualizar la opción seleccionada visualmente
            agentOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');

            // Actualizar el select oculto
            agentSelect.value = value;

            // Disparar el evento change para que se actualice el agente
            const event = new Event('change');
            agentSelect.dispatchEvent(event);

            // Mostrar notificación
            showNotification(`Agente cambiado a: ${this.querySelector('.agent-option-text').textContent}`);
        });
    });
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const notificationContainer = document.createElement('div');
    notificationContainer.className = 'toast-notification';

    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';

    notificationContainer.innerHTML = `
        <i class="bi bi-${icon}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notificationContainer);

    // Remover después de la animación
    setTimeout(() => {
        notificationContainer.remove();
    }, 3000);
}

function initializeChat() {
    console.log("Iniciando chat...");

    // Configurar el entorno del chat
    setupEventListeners();
    checkAPIStatus();

    // Actualizar la UI con el agente inicial
    const initialAgent = document.getElementById('agent-select').value;
    setActiveAgent(initialAgent);

    // Reemplazar la función de mostrar carga en los mensajes
    window.showLoadingIndicator = showLoadingIndicator;
}

// Placeholder functions -  These would need to be implemented based on your actual application logic.
function setupEventListeners() {
    // Add your event listeners here
    console.log('Event listeners setup')
}

function checkAPIStatus() {
    //Check API status here
    console.log('API status checked')
}

function setActiveAgent(agentId) {
    // Set the active agent
    console.log(`Active agent set to: ${agentId}`)
}


// Verificar que el script de chat se cargó correctamente y esperar si es necesario
function checkAndInitializeChat() {
    if (typeof initializeChat === 'function') {
        console.log("Iniciando chat...");
        initializeChat();
        setupAgentSelector();
    } else {
        console.warn("Esperando a que la función initializeChat esté disponible...");
        setTimeout(checkAndInitializeChat, 200);
    }
}

checkAndInitializeChat();