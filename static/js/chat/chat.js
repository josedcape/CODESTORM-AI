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

/**
 * Carga highlight.js para resaltado de sintaxis
 * @returns {Promise} Promesa que se resuelve cuando highlight.js está listo
 */
function loadHighlightJS() {
    return new Promise((resolve, reject) => {
        silentLog('Cargando highlight.js para resaltado de sintaxis...');

        // Verificar si highlight.js ya está cargado
        if (window.hljs) {
            silentLog('highlight.js ya está cargado.');
            resolve(window.hljs);
            return;
        }

        try {
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
                    resolve(window.hljs);
                } else {
                    reject(new Error('highlight.js no se inicializó correctamente'));
                }
            };
            highlightScript.onerror = function(e) {
                reject(new Error('Error al cargar highlight.js: ' + e.message));
            };
            document.head.appendChild(highlightScript);
        } catch (error) {
            reject(error);
        }
    });
}

/**
 * Configura las referencias a elementos UI y sus eventos
 */
function setupUIElements() {
    // No es necesario reinicializar window.app.chat aquí ya que lo hacemos en initializeChat

    // Elementos principales con manejo de errores
    try {
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

        // Configurar eventos principales con verificación
        if (sendButton) {
            sendButton.addEventListener('click', sendMessage);
        } else {
            silentLog('Advertencia: Elemento sendButton no encontrado');
        }

        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
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
        } else {
            silentLog('Advertencia: Elemento messageInput no encontrado');
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
        } else {
            silentLog('Advertencia: Elemento modelSelect no encontrado');
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
        } else {
            silentLog('Advertencia: Elemento agentSelect no encontrado');
        }

        // Actualizar info del agente inicial
        updateAgentInfo(window.app.chat.activeAgent);
    } catch (error) {
        console.error('Error al configurar elementos de UI:', error);
        addSystemMessage('Error al configurar interfaz. Por favor, recarga la página.');
    }
}

/**
 * Actualiza la información mostrada del agente seleccionado
 * @param {string} agentId - ID del agente seleccionado
 */
function updateAgentInfo(agentId) {
    try {
        const agent = window.app.chat.availableAgents[agentId];
        if (!agent) {
            silentLog(`Agente no encontrado: ${agentId}`);
            return;
        }

        const { agentInfo, agentCapabilities, agentBadge } = window.app.chat.elements;

        if (agentInfo) {
            agentInfo.textContent = agent.description || '';
        }

        if (agentBadge) {
            agentBadge.innerHTML = `<i class="bi bi-${agent.icon}"></i> ${agent.name}`;
        }

        if (agentCapabilities) {
            // Limpiar capacidades anteriores
            agentCapabilities.innerHTML = '';

            // Añadir nuevas capacidades
            if (agent.capabilities && Array.isArray(agent.capabilities)) {
                const ul = document.createElement('ul');
                ul.className = 'list-unstyled small';

                agent.capabilities.forEach(capability => {
                    const li = document.createElement('li');
                    li.innerHTML = `<i class="bi bi-check2-circle text-success me-1"></i> ${capability}`;
                    ul.appendChild(li);
                });

                agentCapabilities.appendChild(ul);
            }
        }
    } catch (error) {
        silentLog('Error al actualizar información del agente:', error);
    }
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
    // Configuración silenciosa con manejo de errores
    try {
        // Registrar eventos de arrastrar y soltar para archivos
        const dropZone = document.getElementById('chat-container');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileDrop(files);
                }
            });
        }

        silentLog('Características de documentos inicializadas');
    } catch (error) {
        silentLog('Error al configurar características de documentos:', error);
    }
}

/**
 * Maneja archivos soltados en la zona de chat
 * @param {FileList} files - Lista de archivos
 */
function handleFileDrop(files) {
    try {
        const fileNames = Array.from(files).map(file => file.name);
        addSystemMessage(`Archivos recibidos: ${fileNames.join(', ')}`);

        // Implementar aquí la lógica para procesar archivos
        // Por ahora solo mostramos los nombres
    } catch (error) {
        console.error('Error al procesar archivos:', error);
        addSystemMessage('Error al procesar los archivos');
    }
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

/**
 * Añade mensaje del usuario al chat
 * @param {string} message - Mensaje a mostrar
 */
function addUserMessage(message) {
    const messageId = `msg-${++window.app.chat.chatMessageId}`;

    const messageHTML = `
        <div id="${messageId}" class="message user-message">
            <div class="message-header">
                <div class="message-avatar">
                    <i class="bi bi-person-circle"></i>
                </div>
                <div class="message-info">
                    <span class="message-sender">Tú</span>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
                <div class="message-actions">
                    <button id="copy-btn-${messageId}" class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('${messageId}', 'message', null, 'copy-btn-${messageId}')">
                        <i class="bi bi-clipboard"></i>
                    </button>
                </div>
            </div>
            <div class="message-content">${formatMessageContent(message)}</div>
        </div>
    `;

    appendMessageToChat(messageHTML);
    scrollToBottom();
}

/**
 * Ajusta la altura de un textarea para mostrar todo su contenido
 * @param {HTMLTextAreaElement} textarea - El elemento textarea
 */
function adjustTextareaHeight(textarea) {
    if (!textarea) return;

    // Restablecer altura para obtener una medida precisa
    textarea.style.height = 'auto';
    // Establecer altura basada en el contenido
    textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
}

/**
 * Obtiene la hora actual formateada
 * @returns {string} Hora actual en formato HH:MM
 */
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}


                             /**
                              * Promesa para cargar highlight.js
                              * @returns {Promise} Promesa que se resuelve cuando highlight.js está cargado
                              */
                             function loadHighlightJS() {
                                 return new Promise((resolve, reject) => {
                                     silentLog('Cargando highlight.js para resaltado de sintaxis...');

                                     // Si ya está cargado, resolver inmediatamente
                                     if (window.hljs) {
                                         silentLog('highlight.js ya está cargado.');
                                         resolve();
                                         return;
                                     }

                                     try {
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
                                             resolve();
                                         };
                                         highlightScript.onerror = function(error) {
                                             silentLog('Error al cargar highlight.js:', error);
                                             reject(error);
                                         };
                                         document.head.appendChild(highlightScript);
                                     } catch (error) {
                                         silentLog('Error al configurar highlight.js:', error);
                                         reject(error);
                                     }
                                 });
                             }

                             /**
                              * Copia contenido al portapapeles
                              * @param {string} elementId - ID del elemento que contiene el texto (opcional)
                              * @param {string} type - Tipo de contenido ('message' o 'code')
                              * @param {string} content - Contenido a copiar (opcional)
                              * @param {string} buttonId - ID del botón de copiar (para feedback visual)
                              */
                             function copyToClipboard(elementId, type, content, buttonId) {
                                 try {
                                     let textToCopy = content;

                                     if (!textToCopy && elementId) {
                                         const element = document.getElementById(elementId);
                                         if (!element) {
                                             throw new Error(`Elemento con ID ${elementId} no encontrado`);
                                         }

                                         if (type === 'message') {
                                             const messageContent = element.querySelector('.message-content');
                                             if (messageContent) {
                                                 // Crear un elemento temporal para obtener el texto plano
                                                 const tempElement = document.createElement('div');
                                                 tempElement.innerHTML = messageContent.innerHTML;

                                                 // Eliminar elementos de UI internos
                                                 tempElement.querySelectorAll('.code-toolbar, .message-actions').forEach(el => el.remove());

                                                 textToCopy = tempElement.innerText || tempElement.textContent;
                                             }
                                         } else if (type === 'code') {
                                             const codeElement = element.querySelector('code');
                                             if (codeElement) {
                                                 textToCopy = codeElement.textContent;
                                             }
                                         }
                                     }

                                     if (!textToCopy) {
                                         throw new Error('No se encontró contenido para copiar');
                                     }

                                     // Copiar al portapapeles
                                     navigator.clipboard.writeText(textToCopy).then(() => {
                                         showCopyNotification(buttonId);
                                     }).catch(err => {
                                         throw err;
                                     });
                                 } catch (error) {
                                     console.error('Error al copiar al portapapeles:', error);
                                     alert(`No se pudo copiar el texto: ${error.message}`);
                                 }
                             }

                             /**
                              * Muestra una notificación de éxito al copiar
                              * @param {string} buttonId - ID del botón que inició la copia
                              */
                             function showCopyNotification(buttonId) {
                                 if (buttonId) {
                                     const button = document.getElementById(buttonId);
                                     if (button) {
                                         const originalHTML = button.innerHTML;
                                         const originalBgColor = button.style.backgroundColor;
                                         const originalBorderColor = button.style.borderColor;

                                         // Cambiar apariencia del botón para mostrar confirmación
                                         button.innerHTML = '<i class="bi bi-check"></i> Copiado';
                                         button.style.backgroundColor = 'rgba(40, 167, 69, 0.3)';
                                         button.style.borderColor = 'rgba(40, 167, 69, 0.5)';

                                         // Restaurar apariencia original después de 2 segundos
                                         setTimeout(() => {
                                             button.innerHTML = originalHTML;
                                             button.style.backgroundColor = originalBgColor;
                                             button.style.borderColor = originalBorderColor;
                                         }, 2000);
                                     }
                                 } else {
                                     // Mostrar una notificación flotante genérica
                                     const notification = document.createElement('div');
                                     notification.className = 'copy-notification';
                                     notification.innerHTML = '<i class="bi bi-clipboard-check"></i> Contenido copiado al portapapeles';

                                     document.body.appendChild(notification);

                                     // Animar la notificación
                                     setTimeout(() => {
                                         notification.classList.add('show');

                                         setTimeout(() => {
                                             notification.classList.remove('show');
                                             setTimeout(() => {
                                                 notification.remove();
                                             }, 300);
                                         }, 2000);
                                     }, 10);
                                 }
                             }

                             /**
                              * Formatea el contenido de un mensaje para ser mostrado en el chat
                              * @param {string} content - Contenido del mensaje
                              * @returns {string} Contenido formateado con HTML
                              */
                             function formatMessageContent(content) {
                                 if (!content) return '';

                                 // Escapar HTML para prevenir XSS
                                 let formattedContent = escapeHTML(content);

                                 // Convertir saltos de línea en <br>
                                 formattedContent = formattedContent.replace(/\n/g, '<br>');

                                 // Procesar bloques de código con markdown
                                 formattedContent = processCodeBlocks(formattedContent);

                                 // Procesamiento adicional (negritas, cursivas, enlaces, etc.)
                                 formattedContent = processMarkdown(formattedContent);

                                 return formattedContent;
                             }

                             /**
                              * Escapa caracteres especiales HTML para prevenir XSS
                              * @param {string} text - Texto a escapar
                              * @returns {string} Texto escapado
                              */
                             function escapeHTML(text) {
                                 const div = document.createElement('div');
                                 div.textContent = text;
                                 return div.innerHTML;
                             }

                             /**
                              * Procesa bloques de código markdown en el texto
                              * @param {string} text - Texto a procesar
                              * @returns {string} Texto con bloques de código HTML
                              */
                             function processCodeBlocks(text) {
                                 // Reemplazar bloques de código con ```
                                 const codeBlockRegex = /```([a-z]*)\n([\s\S]+?)```/g;
                                 return text.replace(codeBlockRegex, function(match, language, code) {
                                     language = language || 'plaintext';
                                     return `<pre><code class="language-${language}">${code}</code></pre>`;
                                 });
                             }

                             /**
                              * Procesa sintaxis markdown básica
                              * @param {string} text - Texto a procesar
                              * @returns {string} Texto con formato HTML
                              */
                             function processMarkdown(text) {
                                 // Negritas
                                 text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

                                 // Cursiva
                                 text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

                                 // Enlaces
                                 text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

                                 return text;
                             }
