/**
 * Codestorm Assistant - Módulo de Chat
 * Versión: 2.0.1
 * Fecha: 25-04-2025
 */

// Namespace principal para la aplicación
window.app = window.app || {};
window.app.chat = window.app.chat || {};
window.app.chat.apiEndpoints = {
    chat: '/api/chat',
    fallback: '/api/generate',
    health: '/api/health'
};

// Configuración del módulo de chat
window.app.chat = {
    context: [], // Historial de mensajes para mantener contexto
    chatMessageId: 0, // Contador de ID para mensajes
    activeModel: 'gemini', // Modelo predeterminado
    activeAgent: 'architect', // Agente predeterminado
    debugMode: false, // Desactivar modo debug por defecto
    availableAgents: {
        'developer': {
            name: 'Agente de Desarrollo',
            description: 'Especialista en optimización y edición de código en tiempo real',
            capabilities: [
                'Programación en múltiples lenguajes',
                'Depuración de código y resolución de errores',
                'Implementación de funcionalidades',
                'Pruebas y optimización de rendimiento',
                'Gestión de dependencias y librerías'
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
            name: 'Agente Avanzado',
            description: 'Experto en integraciones complejas y soluciones avanzadas',
            capabilities: [
                'Implementación de IA y aprendizaje automático',
                'Arquitecturas distribuidas y serverless',
                'Optimización de sistemas a gran escala',
                'Estrategias de seguridad y encriptación',
                'DevOps y automatización de procesos'
            ],
            icon: 'cpu'
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
    },
    // Modelos de IA disponibles
    availableModels: {
        'openai': 'OpenAI (GPT-4o)',
        'anthropic': 'Anthropic (Claude)',
        'gemini': 'Google (Gemini)'
    }
};

/**
 * Inicializa el chat y configura los manejadores de eventos
 */
function initializeChat() {
    // Inicializar logs silenciosamente
    silentLog('Inicializando chat con configuración optimizada...');

    // Configurar selectores y elementos de la UI
    setupUIElements();

    // Verificar conexión con el servidor - versión simplificada
    checkServerConnection();

    // Inicializar características avanzadas
    setupDocumentFeatures();
}

/**
 * Configura las referencias a elementos UI y sus eventos
 */
function setupUIElements() {
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
            addSystemMessage(`Modelo cambiado a: ${window.app.chat.availableModels[window.app.chat.activeModel]}`);
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
 * Comprueba la conexión con el servidor de manera simplificada
 */
function checkServerConnection() {
    // Check health endpoint with robust error handling
    silentLog('Verificando estado del servidor...');

    // Asegurarse de que los endpoints estén definidos
    if (!window.app || !window.app.chat || !window.app.chat.apiEndpoints) {
        silentLog('Error: API endpoints no definidos');
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) {
            statusIndicator.style.backgroundColor = "#dc3545"; // rojo
            statusIndicator.title = "Error de configuración";
        }
        return;
    }

    fetch(window.app.chat.apiEndpoints.health)
        .then(response => {
            if (!response.ok) {
                silentLog(`Health endpoint returned status: ${response.status}`);
                // Try to test the chat endpoint directly
                return fetch(window.app.chat.apiEndpoints.chat, {
                    method: 'OPTIONS'
                }).then(chatResponse => {
                    if (chatResponse.ok || chatResponse.status === 204) {
                        silentLog('Chat endpoint is available');
                        const statusIndicator = document.getElementById('status-indicator');
                        if (statusIndicator) {
                            statusIndicator.style.backgroundColor = "#FFC107"; // amarillo
                            statusIndicator.title = "Conexión parcial (endpoints limitados)";
                        }
                        return { status: 'partial', message: 'Chat endpoint available but health check failed' };
                    } else {
                        throw new Error('All endpoints unavailable');
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok' || data.status === 'partial') {
                silentLog('Server check passed:', data.status);
                const statusIndicator = document.getElementById('status-indicator');
                if (statusIndicator) {
                    statusIndicator.style.backgroundColor = "#28a745"; // verde
                    statusIndicator.title = "Servidor conectado";
                }
            } else {
                throw new Error('Server health check failed');
            }
        })
        .catch(error => {
            console.error('Server health check failed:', error);
            // Solo mostrar mensaje de sistema en caso de error total
            const statusIndicator = document.getElementById('status-indicator');
            if (statusIndicator) {
                statusIndicator.style.backgroundColor = "#dc3545"; // rojo
                statusIndicator.title = "Servidor desconectado";
            }

            // Try a ping to fallback endpoint as last resort
            fetch(window.app.chat.apiEndpoints.fallback, {
                method: 'OPTIONS'
            }).then(fallbackResponse => {
                if (fallbackResponse.ok || fallbackResponse.status === 204) {
                    silentLog('Fallback endpoint is available');
                    if (statusIndicator) {
                        statusIndicator.style.backgroundColor = "#FFC107"; // amarillo
                        statusIndicator.title = "Usando conexión de respaldo";
                    }
                }
            }).catch(() => {
                silentLog('All endpoints unavailable');
                addSystemMessage("Error de conexión: No se pudo conectar con el servidor.");
            });
        });
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
    const {messageInput, sendButton} = window.app.chat.elements;

    if (!messageInput) return;

    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    // Añadir mensaje del usuario al chat y contexto
    addUserMessage(userMessage);
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
        // No mostrar el debug en la interfaz
        silentLog('Enviando mensaje al servidor:', requestData);

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        // Verificar si hubo error HTTP
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
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

        if (data.response) {
            // Añadir respuesta al contexto
            window.app.chat.context.push({
                role: 'assistant',
                content: data.response
            });

            // Añadir mensaje del agente al chat
            addAgentMessage(data.response, window.app.chat.activeAgent);
        } else if (data.error) {
            addSystemMessage(`Error: ${data.error}`);
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
                <button class="btn btn-sm btn-icon" onclick="copyToClipboard('${messageId}', 'message')" title="Copiar mensaje">
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
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    .preview-container { border: 1px solid #dee2e6; padding: 20px; border-radius: 6px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="row mb-3">
                        <div class="col">
                            <h3>Vista Previa HTML</h3>
                            <p class="text-muted">Generado por Codestorm Assistant</p>
                        </div>
                    </div>
                    <div class="preview-container">
                        ${htmlContent}
                    </div>
                </div>
            </body>
            </html>
        `);
        previewWindow.document.close();
    } else {
        alert('No se pudo abrir la vista previa. Verifica que no estén bloqueadas las ventanas emergentes.');
    }
}

/**
 * Copia el contenido al portapapeles
 * @param {string} elementId - ID del elemento que contiene el contenido
 * @param {string} type - Tipo de contenido ('message' o 'code')
 * @param {string} content - Contenido a copiar (opcional, solo para 'code')
 * @param {string} buttonId - ID del botón de copiar (opcional)
 */
function copyToClipboard(elementId, type, content, buttonId) {
    let textToCopy = '';

    if (type === 'code' && content) {
        textToCopy = content;
    } else if (type === 'message' && elementId) {
        const messageElement = document.getElementById(elementId);
        if (messageElement) {
            const contentElement = messageElement.querySelector('.message-content');
            if (contentElement) {
                // Obtener el texto plano, manteniendo saltos de línea pero sin HTML
                textToCopy = contentElement.innerText;
            }
        }
    }

    if (textToCopy) {
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                // Mostrar confirmación
                if (buttonId) {
                    const button = document.getElementById(buttonId);
                    if (button) {
                        const originalHTML = button.innerHTML;
                        button.innerHTML = '<i class="bi bi-check"></i>';
                        button.classList.add('btn-success');

                        setTimeout(() => {
                            button.innerHTML = originalHTML;
                            button.classList.remove('btn-success');
                        }, 2000);
                    }
                } else {
                    addSystemMessage('Contenido copiado al portapapeles');
                }
            })
            .catch(err => {
                console.error('Error al copiar:', err);
                addSystemMessage('No se pudo copiar al portapapeles');
            });
    }
}

/**
 * Formatea el contenido del mensaje (markdown, código, etc)
 * @param {string} content - Contenido a formatear
 * @returns {string} Contenido formateado con HTML
 */
function formatMessageContent(content) {
    if (!content) return '';

    // Reemplazar titulares de markdown
    let formattedContent = content
        // Titulares
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')

        // Enlaces
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

        // Negrita
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/__([^_]+)__/g, '<strong>$1</strong>')

        // Cursiva
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')

        // Listas
        .replace(/^\s*\* (.*$)/gm, '<li>$1</li>')
        .replace(/^\s*- (.*$)/gm, '<li>$1</li>')
        .replace(/^\s*\d+\. (.*$)/gm, '<li>$1</li>')

        // Citas
        .replace(/^\> (.*$)/gm, '<blockquote>$1</blockquote>')

        // Bloques de código en línea
        .replace(/`([^`]+)`/g, '<code>$1</code>')

        // Líneas horizontales
        .replace(/^\s*[\-=_]{3,}\s*$/gm, '<hr>');

    // Envolver listas en <ul> o <ol>
    formattedContent = formattedContent
        .replace(/<li>.*?<\/li>/g, function(match) {
            return '<ul>' + match + '</ul>';
        })
        .replace(/<ul><\/li><li>/g, '<ul><li>')
        .replace(/<\/li><li><\/ul>/g, '</li></ul>')
        .replace(/<\/ul><ul>/g, '');

    // Manejar bloques de código con sintaxis ```
    const codeBlockRegex = /```([a-zA-Z]*)\n([\s\S]+?)```/g;
    formattedContent = formattedContent.replace(codeBlockRegex, (match, language, code) => {
        language = language || 'plaintext';
        // Limpiar el código para prevenir problemas de HTML
        const cleanedCode = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // Crear contenedor de código con highlighting
        return `<pre><code class="language-${language}">${cleanedCode}</code></pre>`;
    });

    // Preservar saltos de línea (después de procesar todo lo demás)
    formattedContent = formattedContent.replace(/\n/g, '<br>');

    return formattedContent;
}

/**
 * Actualiza la información del agente seleccionado
 * @param {string} agentId - ID del agente
 */
function updateAgentInfo(agentId) {
    const agent = window.app.chat.availableAgents[agentId] || window.app.chat.availableAgents.general;
    const {agentInfo, agentCapabilities, agentBadge} = window.app.chat.elements;

    // Actualizar información del agente
    if (agentInfo) {
        agentInfo.innerHTML = `
            <i class="bi bi-${agent.icon} agent-icon"></i>
            <div>
                <h3>${agent.name}</h3>
                <p>${agent.description}</p>
            </div>
        `;
    }

    // Actualizar lista de capacidades
    if (agentCapabilities) {
        agentCapabilities.innerHTML = '';
        agent.capabilities.forEach(capability => {
            const item = document.createElement('li');
            item.textContent = capability;
            agentCapabilities.appendChild(item);
        });
    }

    // Actualizar badge del agente
    if (agentBadge) {
        agentBadge.textContent = agent.name;
    }
}

/**
 * Ajusta la altura del textarea automáticamente
 * @param {HTMLTextAreaElement} textarea - Elemento textarea
 */
function adjustTextareaHeight(textarea) {
    if (!textarea) return;

    // Restablecer altura para obtener la correcta
    textarea.style.height = 'auto';

    // Calcular nueva altura (con límite máximo)
    const maxHeight = 200; // altura máxima en px
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);

    // Establecer nueva altura
    textarea.style.height = `${newHeight}px`;

    // Añadir/quitar clase de scroll si es necesario
    if (textarea.scrollHeight > maxHeight) {
        textarea.classList.add('scrollable');
    } else {
        textarea.classList.remove('scrollable');
    }
}

/**
 * Añade un mensaje al contenedor de chat
 * @param {string} messageHTML - HTML del mensaje
 */
function appendMessageToChat(messageHTML) {
    const {messagesContainer} = window.app.chat.elements;
    if (!messagesContainer) return;

    // Crear elemento temporal para insertar HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = messageHTML;

    // Añadir el nodo al contenedor
    messagesContainer.appendChild(tempDiv.firstElementChild);
}

/**
 * Desplaza el chat hasta abajo
 */
function scrollToBottom() {
    const {messagesContainer} = window.app.chat.elements;
    if (!messagesContainer) return;

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Obtiene la hora actual formateada (HH:MM)
 * @returns {string} Hora formateada
 */
function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();

    // Añadir ceros iniciales si es necesario
    hours = hours < 10 ? '0' + hours : hours;
    minutes = minutes < 10 ? '0' + minutes : minutes;

    return `${hours}:${minutes}`;
}

/**
 * Registra información en la consola sin mostrarla en la interfaz
 * @param {string} message - Mensaje a registrar
 * @param {any} data - Datos adicionales (opcional)
 */
function silentLog(message, data) {
    console.log(`[INFO] ${message}`, data !== undefined ? data : '');
}


function addMessageToChat(sender, content, timestamp = null) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');

    // Determinar clase CSS según el remitente
    let messageClass = 'message-bubble';
    if (sender === 'Tú') {
        messageClass += ' user-message';
    } else {
        messageClass += ' agent-message';
    }

    // Formatear timestamp
    let timeStr = '';
    if (timestamp) {
        const date = new Date(timestamp);
        timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    } else {
        const now = new Date();
        timeStr = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    // Intentar formatear el contenido como markdown si no es del usuario
    let formattedContent = content;
    if (sender !== 'Tú') {
        try {
            // Cargar marked.js si no está cargado
            if (typeof marked === 'undefined') {
                // Usamos marked desde CDN si no está disponible
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
                document.head.appendChild(script);

                // Esperamos a que se cargue antes de formatear
                script.onload = () => {
                    formattedContent = marked.parse(content);
                    updateMessage();
                };
            } else {
                formattedContent = marked.parse(content);
            }
        } catch (e) {
            console.error('Error al formatear markdown:', e);
        }
    }

    // Construir HTML del mensaje
    messageDiv.className = 'message-container ' + (sender === 'Tú' ? 'user-container' : 'agent-container');

    function updateMessage() {
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${sender}</strong>
                <span class="message-time">${timeStr}</span>
            </div>
            <div class="${messageClass}">
                ${formattedContent}
            </div>
        `;
    }

    updateMessage();

    // Añadir al contenedor de mensajes
    chatMessages.appendChild(messageDiv);

    // Scroll al final
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Aplicar resaltado de sintaxis a bloques de código
    if (sender !== 'Tú') {
        setTimeout(() => {
            const codeBlocks = messageDiv.querySelectorAll('pre code');
            if (codeBlocks.length > 0) {
                // Cargar highlight.js si no está cargado
                if (typeof hljs === 'undefined') {
                    const highlightScript = document.createElement('script');
                    highlightScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js';
                    document.head.appendChild(highlightScript);

                    const highlightCss = document.createElement('link');
                    highlightCss.rel = 'stylesheet';
                    highlightCss.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css';
                    document.head.appendChild(highlightCss);

                    highlightScript.onload = () => {
                        codeBlocks.forEach(block => {
                            hljs.highlightElement(block);
                        });
                    };
                } else {
                    codeBlocks.forEach(block => {
                        hljs.highlightElement(block);
                    });
                }
            }
        }, 100);
    }
}

// Inicializar el chat cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.app.chat.chatMessageId = 0;  // Reiniciar contador de mensajes
    initializeChat();

    // Añadir mensaje de bienvenida del sistema
    addSystemMessage('¡Bienvenido a([a-zA-Z0-9]+)?/g, function(match, lang) {
            return '