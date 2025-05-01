
// Módulo para la interacción con el agente de desarrollo en el chat
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const assistantPanel = document.getElementById('assistant-chat-panel');
    const chatButton = document.getElementById('toggle-assistant-chat');
    const closeButton = document.getElementById('close-assistant-chat');
    const chatInput = document.getElementById('assistant-chat-input');
    const sendButton = document.getElementById('send-assistant-message');
    const messagesContainer = document.getElementById('assistant-chat-messages');
    const interventionToggle = document.getElementById('intervention-mode');

    // Verificar que los elementos existan
    if (!assistantPanel || !chatButton || !chatInput || !sendButton || !messagesContainer) {
        console.error('Elementos del chat no encontrados');
        return;
    }

    // Estado del chat
    let chatActive = false;
    let isSending = false;
    let chatContext = [];

    // Abrir/cerrar panel de chat
    chatButton.addEventListener('click', function() {
        if (assistantPanel.style.display === 'none' || assistantPanel.style.display === '') {
            assistantPanel.style.display = 'flex';
            chatActive = true;
            chatInput.focus();
            
            // Mostrar mensaje de bienvenida si el chat está vacío
            if (messagesContainer.querySelectorAll('.message').length === 0) {
                addSystemMessage("¡Bienvenido al asistente interactivo! Puedo ayudarte a modificar funciones específicas mientras trabajas en tu proyecto. Ejemplos de cosas que puedes pedirme:");
                addSystemMessage(`
                    <ul>
                        <li>Agregar una función para validar formularios</li>
                        <li>Modificar el estilo CSS de los botones</li>
                        <li>Crear un componente de contador</li>
                        <li>Convertir una función a async/await</li>
                        <li>Optimizar una consulta a base de datos</li>
                    </ul>
                    <p>¿En qué puedo ayudarte hoy?</p>
                `);
            }
        } else {
            assistantPanel.style.display = 'none';
            chatActive = false;
        }
    });

    closeButton.addEventListener('click', function() {
        assistantPanel.style.display = 'none';
        chatActive = false;
    });

    // Enviar mensaje con Enter
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Enviar mensaje con botón
    sendButton.addEventListener('click', sendMessage);

    // Función para enviar mensaje
    function sendMessage() {
        if (isSending) return;
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Agregar mensaje del usuario a la UI
        addUserMessage(message);
        
        // Limpiar input
        chatInput.value = '';
        
        // Obtener contexto relevante
        const projectId = window.projectId || null;
        const activeStage = document.getElementById('current-stage')?.textContent || null;
        const progress = document.getElementById('progress-bar')?.getAttribute('aria-valuenow') || 0;
        
        // Preparar datos para la API
        const requestData = {
            message: message,
            context: {
                projectId: projectId,
                mode: interventionToggle.checked ? 'intervention' : 'information',
                currentStage: activeStage,
                progress: progress,
                chatHistory: chatContext.slice(-5) // Últimos 5 mensajes para contexto
            }
        };
        
        // Mostrar indicador de escritura
        const typingIndicator = addTypingIndicator();
        
        // Marcar como enviando
        isSending = true;
        
        // Enviar al servidor
        fetch('/api/assistant/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // Quitar indicador de escritura
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Procesar respuesta
            if (data.success) {
                // Agregar respuesta a la UI
                addAgentMessage(data.response);
                
                // Actualizar contexto
                chatContext.push({ role: 'user', content: message });
                chatContext.push({ role: 'assistant', content: data.response });
                
                // Procesar acciones si existen
                if (data.actions && data.actions.length > 0) {
                    processAgentActions(data.actions);
                }
            } else {
                // Mostrar error
                addSystemMessage(`Error: ${data.error || 'No se pudo procesar tu solicitud'}`);
            }
            
            // Restaurar estado
            isSending = false;
        })
        .catch(error => {
            console.error('Error al comunicarse con el asistente:', error);
            
            // Quitar indicador de escritura
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Mostrar error
            addSystemMessage('Error de conexión: No se pudo contactar al servidor');
            
            // Restaurar estado
            isSending = false;
        });
    }

    // Agregar mensaje del usuario
    function addUserMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message user-message';
        messageEl.innerHTML = `
            <div class="message-content">${message.replace(/\n/g, '<br>')}</div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        messagesContainer.appendChild(messageEl);
        scrollToBottom();
    }

    // Agregar mensaje del agente
    function addAgentMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant-message';
        
        // Formatear el mensaje (código, etc.) si está disponible la función
        const formattedMessage = window.formatCodeResponse 
            ? window.formatCodeResponse(message)
            : message.replace(/\n/g, '<br>');
        
        messageEl.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-time">${getCurrentTime()}</div>
            <div class="message-actions">
                <button class="btn btn-sm btn-icon copy-message" title="Copiar mensaje">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        `;
        
        // Agregar evento para copiar mensaje
        const copyBtn = messageEl.querySelector('.copy-message');
        if (copyBtn) {
            copyBtn.addEventListener('click', function() {
                const content = messageEl.querySelector('.message-content').innerText;
                navigator.clipboard.writeText(content)
                    .then(() => {
                        this.innerHTML = '<i class="bi bi-check"></i>';
                        setTimeout(() => {
                            this.innerHTML = '<i class="bi bi-clipboard"></i>';
                        }, 2000);
                    })
                    .catch(err => console.error('Error al copiar:', err));
            });
        }
        
        messagesContainer.appendChild(messageEl);
        
        // Aplicar resaltado de sintaxis si existe hljs
        if (window.hljs) {
            messageEl.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }
        
        scrollToBottom();
    }

    // Agregar mensaje del sistema
    function addSystemMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message system-message';
        messageEl.innerHTML = `<div class="message-content">${message}</div>`;
        messagesContainer.appendChild(messageEl);
        scrollToBottom();
    }

    // Agregar indicador de escritura
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(indicator);
        scrollToBottom();
        return indicator;
    }

    // Procesar acciones del agente
    function processAgentActions(actions) {
        actions.forEach(action => {
            // Mostrar notificación de acción
            addActionMessage(`${getActionDescription(action)}`);
            
            // Ejecutar la acción en el proyecto
            executeAction(action);
        });
    }

    // Obtener descripción de la acción
    function getActionDescription(action) {
        switch (action.type) {
            case 'add_file':
                return `Añadiendo archivo: ${action.filename}`;
            case 'modify_file':
                return `Modificando archivo: ${action.filename}`;
            case 'delete_file':
                return `Eliminando archivo: ${action.filename}`;
            case 'add_feature':
                return `Añadiendo característica: ${action.feature}`;
            case 'modify_config':
                return `Modificando configuración: ${action.config_name}`;
            case 'restart_stage':
                return `Reiniciando etapa: ${action.stage_name}`;
            case 'notification':
                return `${action.message}`;
            default:
                return `Ejecutando acción: ${action.type}`;
        }
    }

    // Ejecutar acción
    function executeAction(action) {
        if (!window.projectId) {
            console.error('No hay un proyecto activo');
            addSystemMessage('Error: No hay un proyecto activo para aplicar los cambios');
            return;
        }

        fetch('/api/assistant/execute-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: window.projectId,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addActionMessage(`✅ Acción completada: ${data.message || ''}`);
                
                // Actualizar UI si es necesario
                if (data.new_progress) {
                    updateProgressUI(data.new_progress);
                }
            } else {
                addActionMessage(`❌ Error en acción: ${data.error || 'Error desconocido'}`);
            }
        })
        .catch(error => {
            console.error('Error al ejecutar acción:', error);
            addActionMessage(`❌ Error de comunicación`);
        });
    }

    // Actualizar barra de progreso
    function updateProgressUI(progress) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar && progress) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.textContent = `${progress}%`;
        }
        
        if (progressText && progress) {
            progressText.textContent = `${progress}% completado`;
        }
    }

    // Agregar mensaje de acción
    function addActionMessage(message) {
        const actionEl = document.createElement('div');
        actionEl.className = 'action-message';
        actionEl.innerHTML = `<i class="bi bi-gear-fill me-1"></i> ${message}`;
        messagesContainer.appendChild(actionEl);
        scrollToBottom();
    }

    // Hora actual formateada
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();
        
        // Añadir ceros iniciales si es necesario
        hours = hours < 10 ? '0' + hours : hours;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        
        return `${hours}:${minutes}`;
    }

    // Desplazar al final del chat
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Verificar si el modo intervención está activo al iniciar
    if (interventionToggle) {
        interventionToggle.addEventListener('change', function() {
            if (this.checked) {
                chatButton.classList.add('intervention-active');
                
                // Notificar cambio de modo si hay un proyecto activo
                if (window.projectId) {
                    notifyInterventionMode(window.projectId, true);
                }
            } else {
                chatButton.classList.remove('intervention-active');
                
                // Notificar cambio de modo si hay un proyecto activo
                if (window.projectId) {
                    notifyInterventionMode(window.projectId, false);
                }
            }
        });
    }

    // Notificar al servidor sobre el cambio de modo intervención
    function notifyInterventionMode(projectId, isIntervening) {
        fetch('/api/assistant/intervention-mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: projectId,
                is_intervening: isIntervening
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isIntervening) {
                    addSystemMessage('Modo intervención activado. Puedo modificar el proyecto en desarrollo.');
                } else {
                    addSystemMessage('Modo intervención desactivado. Ahora solo puedo proporcionarte información.');
                }
            } else {
                console.error('Error al cambiar modo intervención:', data.error);
            }
        })
        .catch(error => {
            console.error('Error de comunicación:', error);
        });
    }

    // Inicializar
    console.log('Asistente de chat interactivo inicializado');
});
/**
 * Maneja la interacción con el asistente de desarrollo
 */
class DevelopmentAssistant {
    constructor() {
        this.chatInput = document.getElementById('assistant-chat-input');
        this.chatMessages = document.getElementById('assistant-chat-messages');
        this.sendButton = document.getElementById('send-assistant-message');
        this.interventionMode = document.getElementById('intervention-mode');
        
        this.isWaitingResponse = false;
        this.sessionId = this.generateSessionId();
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Enviar mensaje al hacer clic en el botón
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enviar mensaje al presionar Enter
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    /**
     * Envía el mensaje al asistente
     */
    sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isWaitingResponse) return;
        
        // Añadir mensaje del usuario al chat
        this.addUserMessage(message);
        this.chatInput.value = '';
        
        // Mostrar indicador de escritura
        this.showTypingIndicator();
        this.isWaitingResponse = true;
        
        // Enviar mensaje al backend
        this.sendToBackend(message)
            .then(response => {
                // Ocultar indicador de escritura
                this.hideTypingIndicator();
                
                // Añadir respuesta del asistente
                this.addAssistantMessage(response.message);
                
                // Aplicar cambios de código si es necesario
                if (response.codeChanges) {
                    this.applyCodeChanges(response.codeChanges);
                }
                
                this.isWaitingResponse = false;
            })
            .catch(error => {
                this.hideTypingIndicator();
                this.addSystemMessage(`Error: No se pudo obtener respuesta. ${error.message}`);
                this.isWaitingResponse = false;
            });
    }
    
    /**
     * Envía el mensaje al backend
     * @param {string} message - Mensaje a enviar
     * @return {Promise} - Promesa con la respuesta
     */
    sendToBackend(message) {
        return fetch('/api/dev-assistant/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                sessionId: this.sessionId,
                interventionMode: this.interventionMode.checked
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la comunicación con el servidor');
            }
            return response.json();
        });
    }
    
    /**
     * Añade un mensaje del usuario al chat
     * @param {string} message - Mensaje del usuario
     */
    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.textContent = message;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    /**
     * Añade un mensaje del asistente al chat
     * @param {string} message - Mensaje del asistente
     */
    addAssistantMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message assistant-message';
        messageElement.innerHTML = CodeFormatter.formatCode(message);
        this.chatMessages.appendChild(messageElement);
        
        // Aplicar resaltado de sintaxis si hay código
        CodeFormatter.highlightAll();
        this.scrollToBottom();
    }
    
    /**
     * Añade un mensaje del sistema al chat
     * @param {string} message - Mensaje del sistema
     */
    addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'system-message';
        messageElement.innerHTML = message;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    /**
     * Muestra el indicador de escritura
     */
    showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const bubble = document.createElement('div');
            bubble.className = 'typing-bubble';
            typingIndicator.appendChild(bubble);
        }
        
        this.chatMessages.appendChild(typingIndicator);
        this.scrollToBottom();
    }
    
    /**
     * Oculta el indicador de escritura
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    /**
     * Aplica cambios de código en el proyecto
     * @param {Object} changes - Cambios a aplicar
     */
    applyCodeChanges(changes) {
        if (changes.success) {
            this.addSystemMessage(`
                <p><i class="bi bi-check-circle-fill text-success"></i> <strong>Cambios aplicados:</strong></p>
                <ul>
                    ${changes.files.map(file => `<li>Modificado: ${file}</li>`).join('')}
                </ul>
            `);
        } else {
            this.addSystemMessage(`
                <p><i class="bi bi-exclamation-triangle-fill text-warning"></i> <strong>No se pudieron aplicar todos los cambios:</strong></p>
                <p>${changes.error}</p>
            `);
        }
    }
    
    /**
     * Desplaza el chat hacia abajo
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    /**
     * Genera un ID de sesión único
     * @return {string} - ID de sesión
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Inicializar el asistente cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.developmentAssistant = new DevelopmentAssistant();
});
