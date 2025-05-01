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

// Asegurarse de que los endpoints estén definidos y accesibles
console.log("API Endpoints configurados:", window.app.chat.apiEndpoints);

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

// Función para copiar código al portapapeles
window.copyCode = function(button) {
    const preElement = button.closest('.code-block-container').querySelector('pre');
    const codeElement = preElement.querySelector('code');
    const textToCopy = codeElement.textContent;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = button.textContent;
        button.textContent = '¡Copiado!';
        button.style.backgroundColor = 'rgba(40, 167, 69, 0.3)';
        button.style.borderColor = 'rgba(40, 167, 69, 0.5)';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = '';
            button.style.borderColor = '';
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar texto: ', err);
        button.textContent = 'Error al copiar';
        button.style.backgroundColor = 'rgba(220, 53, 69, 0.3)';
        button.style.borderColor = 'rgba(220, 53, 69, 0.5)';

        setTimeout(() => {
            button.textContent = 'Copiar';
            button.style.backgroundColor = '';
            button.style.borderColor = '';
        }, 2000);
    });
}

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
        if (typeof loadHighlightJS === 'function') {
            loadHighlightJS();
        } else {
            // Si la función no existe, la implementamos aquí
            loadHighlightJS = function() {
                silentLog('Cargando highlight.js para resaltado de sintaxis...');

                // Verificar si highlight.js ya está cargado
                if (window.hljs) {
                    silentLog('highlight.js ya está cargado.');
                    return;
                }

                // Crear enlace para el CSS de highlight.js
                const highlightCSS = document.createElement('link');
                highlightCSS.rel = 'stylesheet';
                highlightCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css';
                document.head.appendChild(highlightCSS);

                // Crear script para highlight.js
                const highlightScript = document.createElement('script');
                highlightScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js';
                highlightScript.onload = function() {
                    silentLog('highlight.js cargado correctamente');
                    // Inicializar highlight.js
                    if (window.hljs) {
                        window.hljs.configure({
                            ignoreUnescapedHTML: true,
                            languages: ['javascript', 'html', 'css', 'python', 'java', 'php', 'ruby', 'bash', 'json']
                        });

                        // Resaltar bloques de código existentes
                        document.querySelectorAll('pre code').forEach(block => {
                            window.hljs.highlightElement(block);
                        });
                    }
                };
                document.head.appendChild(highlightScript);
            };

            // Llamar a la función recién creada
            loadHighlightJS();
        }
    };
/**
 * Configura las referencias a elementos UI y sus eventos
 */
function setupUIElements() {
    // No es necesario reinicializar window.app.chat aquí ya que lo hacemos en initializeChat

    // Elementos principales
    window.app.chat.elements = {
        chatContainer: document.getElementById('chat-container'),
        messagesContainer: document.getElementById('messages-container'),
        messageInput: document.getElementById('message-input'),
        sendButton: document.getElementById('send-button'),
        modelSelect: document.getElementById('model-select'),
        agentSelect: document.getElementById('agent-select'),
        agentInfo: document.getElementById('agent-info'),
        agentCapabilities: document.getElementById('agent-capabilities'),
        agentBadge: document.getElementById('agent-badge'),
        statusIndicator: document.getElementById('status-indicator')
    };

    const {messageInput, sendButton, modelSelect, agentSelect} = window.app.chat.elements;

    // Configurar eventos principales
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            } else if (e.key === 'Enter' && e.shiftKey) {
                // Permitir saltos de línea con Shift+Enter
            }

            // Ajustar altura al contenido
            setTimeout(() => {
                adjustTextareaHeight(messageInput);
            }, 0);
        });

        // Ajustar altura al escribir
        messageInput.addEventListener('input', () => {
            adjustTextareaHeight(messageInput);
        });
    }

    // Cambiar modelo de IA
    if (modelSelect) {
        modelSelect.addEventListener('change', () => {
            window.app.chat.activeModel = modelSelect.value;
            silentLog('Modelo cambiado a:', window.app.chat.activeModel);
            let modelName = "desconocido";
            if (window.app.chat.availableModels && window.app.chat.activeModel in window.app.chat.availableModels) {
                modelName = window.app.chat.availableModels[window.app.chat.activeModel];
            } else {
                modelName = window.app.chat.activeModel;
            }
            addSystemMessage(`Modelo cambiado a: ${modelName}`);

            // Asegurarse de que el modelo se actualice en toda la aplicación
            localStorage.setItem('codestorm_active_model', window.app.chat.activeModel);
        });
    }

    // Cambiar agente
    if (agentSelect) {
        agentSelect.addEventListener('change', () => {
            const previousAgent = window.app.chat.activeAgent;
            window.app.chat.activeAgent = agentSelect.value;
            updateAgentInfo(window.app.chat.activeAgent);
            silentLog('Agente cambiado a:', window.app.chat.activeAgent);

            // Añadir notificación solo si realmente cambió
            if (previousAgent !== window.app.chat.activeAgent) {
                addSystemMessage(`Has cambiado al ${window.app.chat.availableAgents[window.app.chat.activeAgent].name}. ${window.app.chat.availableAgents[window.app.chat.activeAgent].description}`);
            }
        });
    }

    // Actualizar info del agente inicial
    updateAgentInfo(window.app.chat.activeAgent);
}
/**
 * Verifica los modelos disponibles y actualiza la interfaz
 */
async function checkAvailableModels() {
    const modelSelect = document.getElementById('model-select');
    const modelStatus = document.getElementById('model-status');

    if (!modelSelect || !modelStatus) return;

    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            const data = await response.json();
            const apis = data.apis || {};

            // Habilitar/deshabilitar opciones según disponibilidad
            let availableModels = [];
            for (const [model, status] of Object.entries(apis)) {
                const option = modelSelect.querySelector(`option[value="${model}"]`);
                if (option) {
                    if (status === 'ok') {
                        option.disabled = false;
                        availableModels.push(model);
                    } else {
                        option.disabled = true;
                        option.textContent += ' (no configurado)';
                    }
                }
            }

            if (availableModels.length > 0) {
                modelStatus.textContent = `Modelos disponibles: ${availableModels.join(', ')}`;
                modelStatus.className = 'mt-2 small text-success';

                // Seleccionar el primer modelo disponible
                const firstAvailable = Array.from(modelSelect.options).find(option => !option.disabled);
                if (firstAvailable && window.app.chat) {
                    firstAvailable.selected = true;
                    window.app.chat.activeModel = firstAvailable.value;
                }
            } else {
                modelStatus.textContent = 'No hay modelos disponibles. Configure al menos una API en el panel de Secrets.';
                modelStatus.className = 'mt-2 small text-danger';
            }
        }
    } catch (error) {
        console.error('Error al verificar modelos disponibles:', error);
        if (modelStatus) {
            modelStatus.textContent = 'Error al verificar disponibilidad de modelos';
            modelStatus.className = 'mt-2 small text-danger';
        }
    }
}

/**
 * Comprueba la conexión con el servidor de manera optimizada
 */
async function checkServerConnection() {
    silentLog('Verificando estado del servidor...');
    const statusIndicator = document.getElementById('status-indicator');

    // Asegurarse de que los endpoints estén definidos
    if (!window.app || !window.app.chat || !window.app.chat.apiEndpoints) {
        silentLog('Error: API endpoints no definidos');
        if (statusIndicator) {
            statusIndicator.style.backgroundColor = "#dc3545"; // rojo
            statusIndicator.title = "Error de configuración";
        }
        return;
    }

    try {
        // Verificar endpoints con timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(window.app.chat.apiEndpoints.health, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            if (data.status === 'ok') {
                if (statusIndicator) {
                    statusIndicator.style.backgroundColor = "#28a745"; // verde
                    statusIndicator.title = "Servidor conectado";
                }
                return;
            }
        }

        // Intentar endpoint alternativo
        throw new Error('Health check failed');
    } catch (error) {
        silentLog('Error en health check:', error);

        // Intentar endpoints alternativos
        try {
            const endpoints = [
                window.app.chat.apiEndpoints.chat,
                window.app.chat.apiEndpoints.fallback
            ];

            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint, { method: 'OPTIONS' });
                    if (response.ok || response.status === 204) {
                        if (statusIndicator) {
                            statusIndicator.style.backgroundColor = "#FFC107"; // amarillo
                            statusIndicator.title = "Conexión parcial (usando endpoint alternativo)";
                        }
                        return;
                    }
                } catch (e) {
                    continue;
                }
            }

            // Si llegamos aquí, todos los endpoints fallaron
            throw new Error('All endpoints failed');
        } catch (finalError) {
            if (statusIndicator) {
                statusIndicator.style.backgroundColor = "#dc3545"; // rojo
                statusIndicator.title = "Servidor desconectado";
            }
            addSystemMessage("Error de conexión: No se pudo conectar con el servidor.");
        }
    }
}

/**
 * Configura funcionalidades relacionadas con documentos
 */
function setupDocumentFeatures() {
    // Configuración silenciosa
    silentLog('Características de documentos inicializadas');
}

/**
 * Envía un mensaje al servidor y procesa la respuesta
 */
async function sendMessage() {
    // Asegurarse de que window.app y window.app.chat estén inicializados
    if (!window.app || !window.app.chat) {
        console.error("Error: window.app.chat no está inicializado");
        addSystemMessage("Error: Inicialización incompleta. Recargando interfaz...");

        // Inicializar objetos necesarios si no existen
        window.app = window.app || {};
        window.app.chat = window.app.chat || {};
        window.app.chat.elements = window.app.chat.elements || {};
        window.app.chat.context = window.app.chat.context || [];
        window.app.chat.apiEndpoints = window.app.chat.apiEndpoints || {
            chat: '/api/chat',
            fallback: '/api/generate',
            health: '/api/health',
            processCode: '/api/process_code',
            execute: '/api/execute_command',
            files: '/api/files'
        };

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

    // Asegurarse de que el contexto exista
    window.app.chat.context = window.app.chat.context || [];
    window.app.chat.context.push({
        role: 'user',
        content: userMessage
    });

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

    // Asegurarse de que los valores predeterminados estén disponibles
    const activeAgent = window.app.chat.activeAgent || 'general';
    const activeModel = window.app.chat.activeModel || 'gpt-4o';

    // Preparar datos para enviar al servidor
    const requestData = {
        message: userMessage,
        agent_id: activeAgent,
        model: activeModel,
        context: contextToSend
    };

    // Mostrar indicador de carga
    const loadingMessageId = addLoadingMessage();

    try {
        // No mostrar el debug en la interfaz
        silentLog('Enviando mensaje al servidor:', requestData);

        // Asegurarse de usar la API endpoint correcta y tener un respaldo
        const apiEndpoints = window.app.chat.apiEndpoints || {
            chat: '/api/chat',
            fallback: '/api/generate'
        };

        const apiUrl = apiEndpoints.chat || '/api/chat';

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        // Verificar si hubo error HTTP
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                error: `${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.error || `Error del servidor: ${response.status} ${response.statusText}`);
        }

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
            // Formato estándar: data.response
            // Añadir respuesta al contexto
            window.app.chat.context.push({
                role: 'assistant',
                content: data.response
            });

            // Añadir mensaje del agente al chat
            addAgentMessage(data.response, data.agent_id || data.agent || activeAgent);
        } else if (data.message && data.success) {
            // Formato alternativo: data.message con data.success
            window.app.chat.context.push({
                role: 'assistant',
                content: data.message
            });
            addAgentMessage(data.message, data.agent_id || activeAgent);
        } else if (data.error) {
            addSystemMessage(`Error: ${data.error}`);

            // Sugerir probar otro modelo si hay error de API
            if (data.error.includes("API") || data.error.includes("OpenAI") || 
                data.error.includes("Anthropic") || data.error.includes("Gemini")) {

                addSystemMessage(`Sugerencia: Prueba con otro modelo de IA desde el menú de selección o verifica la configuración de la API.`);
            }
        } else {
            addSystemMessage("El servidor respondió pero no envió ningún mensaje");
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

        // Intentar con el endpoint de respaldo si el principal falla
        try {
            addSystemMessage("Intentando con servidor de respaldo...");
            const fallbackUrl = (window.app.chat.apiEndpoints || {}).fallback || '/api/generate';

            const fallbackResponse = await fetch(fallbackUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    model: activeModel
                })
            });

            if (fallbackResponse.ok) {
                const fallbackData = await fallbackResponse.json();
                if (fallbackData.response) {
                    // Añadir respuesta al contexto
                    window.app.chat.context.push({
                        role: 'assistant',
                        content: fallbackData.response
                    });

                    // Añadir mensaje del agente al chat
                    addAgentMessage(fallbackData.response, activeAgent);
                    addSystemMessage("Respuesta generada por el servidor de respaldo");
                }
            } else {
                throw new Error("El servidor de respaldo también falló");
            }
        } catch (fallbackError) {
            silentLog('Error en servidor de respaldo:', fallbackError);
            addSystemMessage("No se pudo conectar con ningún servidor. Por favor, intenta más tarde.");
        }
    }
}


// Función para copiar el contenido de un mensaje
function copyMessageContent(messageElement) {
    // Obtener el contenido del mensaje (excluyendo los botones y otros elementos de UI)
    const messageContent = messageElement.querySelector('.message-content');

    if (messageContent) {
        // Crear un elemento temporal para obtener el texto plano
        const tempElement = document.createElement('div');
        tempElement.innerHTML = messageContent.innerHTML;

        // Eliminar los botones de copiar de los bloques de código
        tempElement.querySelectorAll('.code-toolbar').forEach(toolbar => {
            toolbar.remove();
        });

        // Obtener el texto del mensaje
        const textToCopy = tempElement.innerText || tempElement.textContent;

        // Copiar al portapapeles
        navigator.clipboard.writeText(textToCopy).then(() => {
            showCopyNotification();
        }).catch(err => {
            console.error('Error al copiar texto: ', err);
            alert('No se pudo copiar el texto. Por favor, inténtalo de nuevo.');
        });
    }
}


/**
 * Añade mensaje del usuario al chat
 * @param {string} message - Mensaje a mostrar
 */
function addUserMessage(message) {
    const messageId = `msg-${++window.app.chat.chatMessageId}`;
    const messageHTML = `
        <div class="message-container user-message" id="${messageId}">
            <div class="message-header">
                <span class="message-author">Tú</span>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
            <div class="message-content">
                ${formatMessageContent(message)}
            </div>
        </div>
    `;

    appendMessageToChat(messageHTML);
    scrollToBottom();
}

/**
 * Añade mensaje del agente al chat
 * @param {string} message - Mensaje a mostrar
 * @param {string} agentId - ID del agente
 */
function addAgentMessage(message, agentId) {
    const agent = window.app.chat.availableAgents[agentId] || window.app.chat.availableAgents.general;
    const messageId = `msg-${++window.app.chat.chatMessageId}`;
    const copyBtnId = `copy-btn-${messageId}`;
    const formattedMessage = formatMessageContent(message);

    const messageHTML = `
        <div class="message-container agent-message" id="${messageId}">
            <div class="message-header">
                <span class="message-author">
                    <i class="bi bi-${agent.icon}"></i> 
                    ${agent.name}
                </span>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
            <div class="message-content">
                ${formattedMessage}
            </div>
            <div class="message-actions">
                <button id="${copyBtnId}" class="btn btn-sm btn-icon" onclick="copyToClipboard('${messageId}', 'message', null, '${copyBtnId}')" data-message-id="${messageId}" title="Copiar mensaje">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </div>
    `;

    appendMessageToChat(messageHTML);

    // Procesar elementos especiales (código, HTML, etc)
    processCodeBlocks(messageId);
    processHTMLPreview(messageId);

    scrollToBottom();
}

/**
 * Añade mensaje del sistema al chat (notificaciones, etc)
 * @param {string} message - Mensaje a mostrar
 */
function addSystemMessage(message) {
    const messageId = `msg-${++window.app.chat.chatMessageId}`;
    const messageHTML = `
        <div class="message-container system-message" id="${messageId}">
            <div class="message-content">
                <i class="bi bi-info-circle"></i> ${message}
            </div>
        </div>
    `;

    appendMessageToChat(messageHTML);
    scrollToBottom();
}

/**
 * Añade un mensaje de carga al chat
 * @returns {string} ID del mensaje de carga
 */
function addLoadingMessage() {
    const messageId = `loading-${Date.now()}`;
    const messageHTML = `
        <div class="message-container loading-message" id="${messageId}">
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    appendMessageToChat(messageHTML);
    scrollToBottom();

    return messageId;
}

/**
 * Elimina un mensaje de carga
 * @param {string} messageId - ID del mensaje a eliminar
 */
function removeLoadingMessage(messageId) {
    if (messageId) {
        const loadingElement = document.getElementById(messageId);
        if (loadingElement) {
            loadingElement.remove();
        }
    } else {
        // Si no se especifica ID, eliminar todos los indicadores de carga
        const loadingElements = document.querySelectorAll('.loading-message');
        loadingElements.forEach(el => el.remove());
    }
}

/**
 * Procesa bloques de código en el mensaje
 * @param {string} messageId - ID del elemento del mensaje
 */
function processCodeBlocks(messageId) {
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;

    const codeBlocks = messageElement.querySelectorAll('pre code');
    if (!codeBlocks.length) return;

    // Cargar highlight.js si es necesario
    loadHighlightJS().then(() => {
        codeBlocks.forEach((codeBlock, index) => {
            const codeContent = codeBlock.textContent;
            const copyButtonId = `copy-code-${messageId}-${index}`;

            // Detectar lenguaje de programación
            let language = 'plaintext';
            const codeClasses = codeBlock.className.split(' ');
            for (const cls of codeClasses) {
                if (cls.startsWith('language-')) {
                    language = cls.replace('language-', '');
                    break;
                }
            }

            // Crear contenedor para el bloque de código con botón de copiar
            const codeContainer = document.createElement('div');
            codeContainer.className = 'code-block-container';

            // Barra de herramientas
            const toolbar = document.createElement('div');
            toolbar.className = 'code-toolbar';

            // Etiqueta de lenguaje
            const langLabel = document.createElement('span');
            langLabel.className = 'code-language';
            langLabel.textContent = language;
            toolbar.appendChild(langLabel);

            // Botón de copiar
            const copyButton = document.createElement('button');
            copyButton.id = copyButtonId;
            copyButton.className = 'btn btn-sm btn-dark code-copy-btn';
            copyButton.innerHTML = '<i class="bi bi-clipboard"></i>';
            copyButton.title = 'Copiar código';
            copyButton.onclick = function() {
                // Asegurarse de que codeContent contiene el texto completo del código
                // y no solo una referencia o un ID
                copyToClipboard(null, 'code', codeContent, copyButtonId);
            };
            toolbar.appendChild(copyButton);

            codeContainer.appendChild(toolbar);


            // Conservar el bloque de código original
            const newCodeBlock = document.createElement('pre');
            newCodeBlock.className = codeBlock.parentElement.className;
            newCodeBlock.appendChild(codeBlock.cloneNode(true));
            codeContainer.appendChild(newCodeBlock);

            // Reemplazar el bloque original con el contenedor mejorado
            codeBlock.parentElement.replaceWith(codeContainer);

            // Aplicar highlight.js al nuevo bloque de código
            try {
                if (window.hljs) {
                    const codeElements = codeContainer.querySelectorAll('code');
                    codeElements.forEach(el => {
                        window.hljs.highlightElement(el);
                    });
                }
            } catch (e) {
                silentLog('Error al aplicar highlight.js:', e);
            }
        });
    }).catch(err => {
        silentLog('No se pudo cargar highlight.js:', err);
    });
}

/**
 * Procesa previsualizaciones HTML en el mensaje
 * @param {string} messageId - ID del elemento del mensaje
 */
function processHTMLPreview(messageId) {
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;

    const codeBlocks = messageElement.querySelectorAll('pre code.language-html');

    codeBlocks.forEach((codeBlock, index) => {
        const htmlContent = codeBlock.textContent;

        // Solo añadir vista previa si el HTML tiene suficiente contenido
        if (htmlContent.length > 50) {
            const previewButtonId = `preview-${messageId}-${index}`;

            // Crear botón de vista previa
            const previewButton = document.createElement('button');
            previewButton.id = previewButtonId;
            previewButton.className = 'btn btn-sm btn-primary mt-2';
            previewButton.innerHTML = '<i class="bi bi-eye"></i> Ver HTML';
            previewButton.onclick = function() {
                showHTMLPreview(htmlContent);
            };

            // Añadir botón después del bloque de código
            codeBlock.parentElement.parentElement.appendChild(previewButton);
        }
    });
}

/**
 * Muestra una previsualización de código HTML
 * @param {string} htmlContent - Contenido HTML a previsualizar
 */
function showHTMLPreview(htmlContent) {
    // Crear una ventana emergente para la vista previa
    const previewWindow = window.open('', '_blank', 'width=800,height=600');

    if (previewWindow) {
        previewWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Vista Previa HTML</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <!-- Bootstrap CSS -->
                <link href([a-zA-Z]*)\n([\s\S]+?)