/**
 * DevAssistant - Módulo unificado para el asistente de desarrollo interactivo
 * Versión: 2.0.0
 * 
 * Funcionalidades:
 * - Interfaz de chat interactiva con el asistente
 * - Modo intervención para modificar archivos del proyecto
 * - Visualización de código con resaltado de sintaxis
 * - Ejecución de acciones sobre el proyecto (crear/modificar/eliminar archivos)
 * - Seguimiento del contexto de la conversación
 */

// Verificar si la clase ya existe para evitar redefiniciones
if (typeof window.DevAssistant === 'undefined') {
    window.DevAssistant = class {
    constructor(config = {}) {
        // Configuración por defecto
        this.config = Object.assign({
            apiEndpoints: window.app && window.app.apiEndpoints && window.app.apiEndpoints.assistant ? 
                window.app.apiEndpoints.assistant : {
                    chat: '/api/chat',  // Cambiado para usar el endpoint principal
                    execute: '/api/execute_command',
                    files: '/api/files',
                    interventionMode: '/api/intervention_mode',
                    applyChanges: '/api/apply_changes'
                },
            selectors: {
                panel: '#assistant-chat-panel',
                button: '#toggle-assistant-chat',
                close: '#close-assistant-chat',
                input: '#assistant-chat-input',
                send: '#send-assistant-message',
                messages: '#assistant-chat-messages',
                intervention: '#intervention-mode'
            }
        }, config);

        // Estado interno
        this.state = {
            active: false,
            isSending: false,
            chatContext: [],
            sessionId: this.generateSessionId(),
            projectId: window.projectId || null
        };

        // Inicializar elementos DOM
        this.initDOM();

        // Verificar si los elementos necesarios están presentes
        const missingElements = [];
        if (!this.elements.panel) missingElements.push('panel');
        if (!this.elements.button) missingElements.push('botón de chat');
        if (!this.elements.input) missingElements.push('campo de entrada');
        if (!this.elements.send) missingElements.push('botón de enviar');
        if (!this.elements.messages) missingElements.push('contenedor de mensajes');
        
        if (missingElements.length === 0) {
            // Todos los elementos necesarios están presentes
            this.initEventListeners();
            this.loadDependencies();
            console.log('DevAssistant: Inicializado correctamente');
        } else {
            // Crear elementos faltantes dinámicamente
            console.warn(`DevAssistant: No se encontraron los siguientes elementos: ${missingElements.join(', ')}`);
            this.createMissingElements(missingElements);
            
            // Reintentar inicialización
            setTimeout(() => {
                this.initDOM();
                if (this.elements.panel && this.elements.button && 
                    this.elements.input && this.elements.send && this.elements.messages) {
                    this.initEventListeners();
                    this.loadDependencies();
                    console.log('DevAssistant: Inicializado correctamente tras crear elementos');
                } else {
                    console.error('DevAssistant: No se pudo inicializar incluso después de crear elementos');
                }
            }, 100);
        }
    }

    /**
     * Inicializa las referencias a elementos DOM
     */
    initDOM() {
        this.elements = {};
        Object.keys(this.config.selectors).forEach(key => {
            this.elements[key] = document.querySelector(this.config.selectors[key]);
        });
    }

    /**
     * Inicializa los listeners de eventos
     */
    initEventListeners() {
        // Abrir/cerrar panel
        this.elements.button.addEventListener('click', () => this.toggleChat());
        this.elements.close.addEventListener('click', () => this.hideChat());

        // Enviar mensaje
        this.elements.send.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Modo intervención
        if (this.elements.intervention) {
            this.elements.intervention.addEventListener('change', () => {
                const isInterventionMode = this.elements.intervention.checked;

                if (isInterventionMode) {
                    this.elements.button.classList.add('intervention-active');
                } else {
                    this.elements.button.classList.remove('intervention-active');
                }

                this.notifyInterventionMode(isInterventionMode);
            });
        }

        // Eventos para copiar código (delegación)
        this.elements.messages.addEventListener('click', (e) => {
            if (e.target.closest('.copy-message')) {
                const messageEl = e.target.closest('.message');
                if (messageEl) {
                    const content = messageEl.querySelector('.message-content').innerText;
                    this.copyToClipboard(content, e.target.closest('.copy-message'));
                }
            }

            // Botón para aplicar cambios
            if (e.target.closest('.apply-changes-btn')) {
                const changesEl = e.target.closest('.file-changes');
                if (changesEl && changesEl.dataset.changes) {
                    try {
                        const changes = JSON.parse(changesEl.dataset.changes);
                        this.applyFileChanges(changes);
                    } catch (err) {
                        console.error('Error al parsear los cambios:', err);
                    }
                }
            }
        });
    }

    /**
     * Carga dependencias externas y estilos necesarios
     */
    loadDependencies() {
        // Cargar highlight.js si no está disponible
        if (!window.hljs) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js';
            script.onload = () => {
                const css = document.createElement('link');
                css.rel = 'stylesheet';
                css.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css';
                document.head.appendChild(css);
            };
            document.head.appendChild(script);
        }
        
        // Cargar estilos del asistente si no están disponibles
        if (!document.querySelector('link[href*="assistant.css"]')) {
            const assistantStyles = document.createElement('link');
            assistantStyles.rel = 'stylesheet';
            assistantStyles.href = '/static/css/assistant.css';
            document.head.appendChild(assistantStyles);
            
            // Estilo alternativo en caso de que el archivo no esté disponible
            assistantStyles.onerror = () => {
                console.warn('No se pudo cargar assistant.css, usando estilos embebidos');
                const inlineStyles = document.createElement('style');
                inlineStyles.textContent = `
                    .assistant-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; }
                    .assistant-button { width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #0A2E6B, #0D47A1); color: white; border: none; cursor: pointer; }
                    .assistant-panel { position: fixed; bottom: 80px; right: 20px; width: 350px; height: 500px; background-color: #1E1E1E; border-radius: 10px; display: flex; flex-direction: column; overflow: hidden; }
                    .assistant-header { background: linear-gradient(90deg, #0A2E6B, #0D47A1); color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
                    .assistant-close { background: none; border: none; color: white; cursor: pointer; }
                    .assistant-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background-color: #2D2D2D; }
                    .message { max-width: 80%; padding: 10px 15px; border-radius: 10px; }
                    .user-message { align-self: flex-end; background-color: #0D47A1; color: white; }
                    .assistant-message { align-self: flex-start; background-color: #3D3D3D; color: #E0E0E0; }
                    .system-message { align-self: center; background-color: #424242; color: #BDBDBD; font-style: italic; max-width: 90%; }
                    .assistant-footer { background-color: #1E1E1E; padding: 10px; border-top: 1px solid #333; }
                    .assistant-input-group { display: flex; gap: 8px; }
                    .assistant-input { flex: 1; border: 1px solid #444; background-color: #2D2D2D; color: white; border-radius: 5px; padding: 8px; }
                    .assistant-send { width: 40px; background-color: #0D47A1; border: none; border-radius: 5px; color: white; cursor: pointer; }
                `;
                document.head.appendChild(inlineStyles);
            };
        }
        
        // Cargar Bootstrap Icons si no están disponibles
        if (!document.querySelector('link[href*="bootstrap-icons"]')) {
            const iconLink = document.createElement('link');
            iconLink.rel = 'stylesheet';
            iconLink.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css';
            document.head.appendChild(iconLink);
        }
    }

    /**
     * Muestra/oculta el panel de chat
     */
    toggleChat() {
        if (this.state.active) {
            this.hideChat();
        } else {
            this.showChat();
        }
    }

    /**
     * Muestra el panel de chat
     */
    showChat() {
        this.elements.panel.style.display = 'flex';
        this.state.active = true;
        this.elements.input.focus();

        // Mostrar mensaje de bienvenida si el chat está vacío
        if (this.elements.messages.querySelectorAll('.message').length === 0) {
            this.addSystemMessage("¡Bienvenido al asistente de desarrollo! Puedo ayudarte a modificar tu proyecto. Ejemplos de lo que puedo hacer:");
            this.addSystemMessage(`
                <ul>
                    <li>Crear nuevos archivos o componentes</li>
                    <li>Modificar archivos existentes</li>
                    <li>Revisar código y sugerir mejoras</li>
                    <li>Implementar nuevas funcionalidades</li>
                    <li>Corregir errores en el código</li>
                </ul>
                <p>Para permitirme hacer cambios directos en los archivos, activa el "Modo intervención".</p>
            `);
        }
    }

    /**
     * Oculta el panel de chat
     */
    hideChat() {
        this.elements.panel.style.display = 'none';
        this.state.active = false;
    }

    /**
     * Envía un mensaje al asistente
     */
    sendMessage() {
        if (this.state.isSending) return;

        const message = this.elements.input.value.trim();
        if (!message) return;

        // Agregar mensaje del usuario
        this.addUserMessage(message);

        // Limpiar input
        this.elements.input.value = '';

        // Verificar si el modo intervención está activado
        const interventionEnabled = this.elements.intervention ? this.elements.intervention.checked : false;

        // Indicar que estamos enviando un mensaje
        this.state.isSending = true;
        if (this.elements.send) this.elements.send.disabled = true;

        // Mostrar indicador de escritura
        this.addTypingIndicator();

        // Preparar datos para enviar
        const requestData = {
            message: message,
            sessionId: this.state.sessionId,
            projectId: this.state.projectId,
            interventionMode: interventionEnabled,
            context: {
                chatHistory: this.state.chatContext.slice(-10), // Últimos 10 mensajes para contexto
                currentStage: document.getElementById('current-stage')?.textContent || null,
                progress: document.getElementById('progress-bar')?.getAttribute('aria-valuenow') || 0
            }
        };

        // Usar endpoint corregido
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                console.error(`Error en la solicitud: ${response.status} - Endpoint: ${this.config.apiEndpoints.chat}`);
                throw new Error(`Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Eliminar indicador de escritura
            this.removeTypingIndicator();

            // Agregar respuesta del asistente
            if (data.response || data.message) {
                const responseText = data.response || data.message;
                this.addAssistantMessage(responseText);

                // Guardar en el contexto
                this.state.chatContext.push({ role: 'user', content: message });
                this.state.chatContext.push({ role: 'assistant', content: responseText });

                // Si hay acciones para ejecutar
                if (data.actions && data.actions.length > 0) {
                    this.processActions(data.actions);
                }

                // Si hay cambios de archivos propuestos
                if (data.fileChanges || data.file_changes) {
                    const changes = data.fileChanges || data.file_changes;
                    if (changes && changes.length > 0) {
                        this.addFileChangesMessage(changes);
                    }
                }
            } else if (data.error) {
                this.addSystemMessage(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.removeTypingIndicator();
            this.addSystemMessage(`Error al enviar mensaje: ${error.message}`);
        })
        .finally(() => {
            this.state.isSending = false;
            if (this.elements.send) this.elements.send.disabled = false;
        });
    }

    /**
     * Procesa acciones devueltas por el asistente
     * @param {Array} actions - Lista de acciones a ejecutar
     */
    processActions(actions) {
        actions.forEach(action => {
            this.addActionMessage(`Ejecutando: ${this.getActionDescription(action)}`);

            fetch(this.config.apiEndpoints.execute, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    project_id: this.state.projectId,
                    action: action
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.addActionMessage(`✅ Acción completada: ${data.message || ''}`);

                    // Actualizar UI si es necesario
                    if (data.new_progress) {
                        this.updateProgressUI(data.new_progress);
                    }
                } else {
                    this.addActionMessage(`❌ Error en acción: ${data.error || 'Error desconocido'}`);
                }
            })
            .catch(error => {
                console.error('Error al ejecutar acción:', error);
                this.addActionMessage(`❌ Error de comunicación`);
            });
        });
    }

    /**
     * Obtiene descripción legible de una acción
     * @param {Object} action - Acción a describir
     * @return {string} - Descripción de la acción
     */
    getActionDescription(action) {
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
            default:
                return `Ejecutando acción: ${action.type}`;
        }
    }

    /**
     * Aplica cambios de archivos propuestos
     * @param {Array} fileChanges - Lista de cambios a aplicar
     */
    applyFileChanges(fileChanges) {
        if (!fileChanges || fileChanges.length === 0) {
            this.addSystemMessage('❌ No hay cambios para aplicar');
            return;
        }

        this.addSystemMessage('Aplicando cambios en archivos...');

        // Formatear cambios para API
        const changes = fileChanges.map(change => {
            return {
                file_path: change.file_path || change.filename,
                content: change.content || change.code || '',
                change_type: change.change_type || 'write'
            };
        });

        fetch('/api/apply_changes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                changes: changes,
                projectId: this.state.projectId,
                user_id: 'default'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.addSystemMessage(`✅ Cambios aplicados correctamente a ${changes.length} ${changes.length === 1 ? 'archivo' : 'archivos'}.`);

                // Si hay archivos modificados, mostrarlos
                if (data.modifiedFiles && data.modifiedFiles.length > 0) {
                    let filesList = '<ul>';
                    data.modifiedFiles.forEach(file => {
                        filesList += `<li>${file}</li>`;
                    });
                    filesList += '</ul>';
                    this.addSystemMessage(`Archivos modificados: ${filesList}`);
                }

                // Notificar al explorador de archivos para recargar
                if (window.fileActions && typeof window.fileActions.refreshFileExplorer === 'function') {
                    window.fileActions.refreshFileExplorer();
                }
            } else {
                this.addSystemMessage(`❌ Error al aplicar cambios: ${data.error || 'Error desconocido'}`);
            }
        })
        .catch(error => {
            console.error('Error al aplicar cambios:', error);
            this.addSystemMessage(`❌ Error al aplicar cambios: ${error.message}`);
        });
    }

    /**
     * Notifica al servidor sobre el cambio de modo intervención
     * @param {boolean} isIntervening - Estado del modo intervención
     */
    notifyInterventionMode(isIntervening) {
        if (!this.state.projectId) {
            if (isIntervening) {
                this.addSystemMessage('Modo intervención activado. Puedo realizar cambios directos en el proyecto.');
            } else {
                this.addSystemMessage('Modo intervención desactivado. Solo puedo proporcionar información.');
            }
            return;
        }

        fetch(this.config.apiEndpoints.interventionMode, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: this.state.projectId,
                is_intervening: isIntervening
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isIntervening) {
                    this.addSystemMessage('Modo intervención activado. Puedo realizar cambios directos en el proyecto.');
                } else {
                    this.addSystemMessage('Modo intervención desactivado. Solo puedo proporcionar información.');
                }
            } else {
                console.error('Error al cambiar modo intervención:', data.error);
            }
        })
        .catch(error => {
            console.error('Error de comunicación:', error);
        });
    }

    /**
     * Actualiza la UI de progreso del proyecto
     * @param {number} progress - Nuevo valor de progreso
     */
    updateProgressUI(progress) {
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

    /**
     * Agrega un mensaje del usuario al chat
     * @param {string} message - Contenido del mensaje
     */
    addUserMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message user-message';
        messageEl.innerHTML = `
            <div class="message-content">${this.escapeHtml(message).replace(/\n/g, '<br>')}</div>
            <div class="message-time">${this.getCurrentTime()}</div>
        `;
        this.elements.messages.appendChild(messageEl);
        this.scrollToBottom();
    }

    /**
     * Agrega un mensaje del asistente al chat
     * @param {string} message - Contenido del mensaje
     */
    addAssistantMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant-message';

        // Formatear el mensaje (código, etc.)
        const formattedMessage = this.formatMessage(message);

        messageEl.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-time">${this.getCurrentTime()}</div>
            <div class="message-actions">
                <button class="btn btn-sm btn-icon copy-message" title="Copiar mensaje">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        `;

        this.elements.messages.appendChild(messageEl);

        // Aplicar resaltado de sintaxis si existe hljs
        if (window.hljs) {
            messageEl.querySelectorAll('pre code').forEach(block => {
                window.hljs.highlightElement(block);
            });
        }

        this.scrollToBottom();
    }

    /**
     * Agrega un mensaje del sistema al chat
     * @param {string} message - Contenido del mensaje
     */
    addSystemMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message system-message';
        messageEl.innerHTML = `<div class="message-content">${message}</div>`;
        this.elements.messages.appendChild(messageEl);
        this.scrollToBottom();
    }

    /**
     * Agrega un mensaje de acción al chat
     * @param {string} message - Contenido del mensaje
     */
    addActionMessage(message) {
        const actionEl = document.createElement('div');
        actionEl.className = 'action-message';
        actionEl.innerHTML = `<i class="bi bi-gear-fill me-1"></i> ${message}`;
        this.elements.messages.appendChild(actionEl);
        this.scrollToBottom();
    }

    /**
     * Agrega un mensaje con cambios de archivos propuestos
     * @param {Array} fileChanges - Lista de cambios propuestos
     */
    addFileChangesMessage(fileChanges) {
        if (!fileChanges || fileChanges.length === 0) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message action-message';

        // Sanitizar y formatear los cambios para mostrarlos
        let filesList = '<ul class="file-changes-list">';
        fileChanges.forEach(change => {
            const filePath = change.file_path || change.filename || 'archivo sin nombre';
            const changeType = change.change_type || change.type || 'modificación';
            
            filesList += `<li><strong>${this.escapeHtml(filePath)}</strong> - ${this.escapeHtml(changeType)}</li>`;
        });
        filesList += '</ul>';

        // Guardar una copia segura de los cambios
        const changesData = JSON.stringify(fileChanges.map(change => {
            return {
                file_path: change.file_path || change.filename,
                content: change.content || change.code || '',
                change_type: change.change_type || change.type || 'write'
            };
        }));

        messageDiv.innerHTML = `
            <div class="file-changes">
                <p>Cambios propuestos (${fileChanges.length} ${fileChanges.length === 1 ? 'archivo' : 'archivos'}):</p>
                ${filesList}
                <button class="btn btn-sm btn-primary mt-2 apply-changes-btn">Aplicar cambios</button>
            </div>
        `;

        // Adjuntar los datos de cambios como atributo 
        messageDiv.querySelector('.file-changes').dataset.changes = changesData;

        this.elements.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Agrega un indicador de escritura al chat
     */
    addTypingIndicator() {
        // Eliminar indicador existente si lo hay
        this.removeTypingIndicator();

        const indicatorDiv = document.createElement('div');
        indicatorDiv.id = 'typing-indicator';
        indicatorDiv.className = 'typing-indicator';
        indicatorDiv.innerHTML = `
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
        `;

        this.elements.messages.appendChild(indicatorDiv);
        this.scrollToBottom();
    }

    /**
     * Elimina el indicador de escritura
     */
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Formatea un mensaje para mostrar código y otros elementos
     * @param {string} content - Contenido a formatear
     * @return {string} - Contenido formateado
     */
    formatMessage(content) {
        if (!content) return '';

        // Escapar HTML
        let formatted = this.escapeHtml(content);

        // Formatear bloques de código
        formatted = formatted.replace(/```([\s\S]+?)```/g, function(match, code) {
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
     * Escapa caracteres HTML
     * @param {string} text - Texto a escapar
     * @return {string} - Texto escapado
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Copia texto al portapapeles
     * @param {string} text - Texto a copiar
     * @param {HTMLElement} button - Botón que inició la acción
     */
    copyToClipboard(text, button) {
        navigator.clipboard.writeText(text)
            .then(() => {
                // Cambiar icono temporalmente
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i>';
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                }, 2000);
            })
            .catch(err => console.error('Error al copiar:', err));
    }

    /**
     * Desplaza el chat hacia abajo
     */
    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    /**
     * Obtiene la hora actual formateada
     * @return {string} - Hora formateada (HH:MM)
     */
    getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();

        // Añadir ceros iniciales si es necesario
        hours = hours < 10 ? '0' + hours : hours;
        minutes = minutes < 10 ? '0' + minutes : minutes;

        return `${hours}:${minutes}`;
    }

    /**
     * Genera un ID de sesión único
     * @return {string} - ID de sesión
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Establece el ID del proyecto actual
     * @param {string} projectId - ID del proyecto
     */
    setProjectId(projectId) {
        this.state.projectId = projectId;
        console.log(`DevAssistant: Proyecto establecido a ${projectId}`);
    }

    /**
     * Crea elementos HTML faltantes dinámicamente
     * @param {Array} missingElements - Lista de elementos faltantes
     */
    createMissingElements(missingElements) {
        // Verificar si ya existe el contenedor principal
        let container = document.getElementById('assistant-chat-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'assistant-chat-container';
            container.className = 'assistant-container';
            document.body.appendChild(container);
        }

        // Crear panel si falta
        if (missingElements.includes('panel') && !document.querySelector(this.config.selectors.panel)) {
            const panel = document.createElement('div');
            panel.id = 'assistant-chat-panel';
            panel.className = 'assistant-panel';
            panel.style.display = 'none';
            container.appendChild(panel);
        }

        // Crear botón si falta
        if (missingElements.includes('botón de chat') && !document.querySelector(this.config.selectors.button)) {
            const button = document.createElement('button');
            button.id = 'toggle-assistant-chat';
            button.className = 'assistant-button';
            button.innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
            button.title = 'Asistente de desarrollo';
            container.appendChild(button);
        }

        // Si falta el panel, crear su estructura interna
        const panel = document.querySelector(this.config.selectors.panel) || document.getElementById('assistant-chat-panel');
        if (panel) {
            // Crear encabezado si no existe
            if (!panel.querySelector('.assistant-header')) {
                const header = document.createElement('div');
                header.className = 'assistant-header';
                header.innerHTML = `
                    <h5>Asistente de Desarrollo</h5>
                    <button id="close-assistant-chat" class="assistant-close"><i class="bi bi-x"></i></button>
                `;
                panel.appendChild(header);
            }

            // Crear contenedor de mensajes si falta
            if (missingElements.includes('contenedor de mensajes') && !document.querySelector(this.config.selectors.messages)) {
                const messages = document.createElement('div');
                messages.id = 'assistant-chat-messages';
                messages.className = 'assistant-messages';
                panel.appendChild(messages);
            }

            // Crear pie con input y botón si faltan
            if ((missingElements.includes('campo de entrada') || missingElements.includes('botón de enviar')) && 
                (!document.querySelector(this.config.selectors.input) || !document.querySelector(this.config.selectors.send))) {
                const footer = document.createElement('div');
                footer.className = 'assistant-footer';
                
                const inputGroup = document.createElement('div');
                inputGroup.className = 'assistant-input-group';
                
                const input = document.createElement('textarea');
                input.id = 'assistant-chat-input';
                input.className = 'assistant-input';
                input.placeholder = 'Escribe tu mensaje...';
                
                const sendButton = document.createElement('button');
                sendButton.id = 'send-assistant-message';
                sendButton.className = 'assistant-send';
                sendButton.innerHTML = '<i class="bi bi-send"></i>';
                
                inputGroup.appendChild(input);
                inputGroup.appendChild(sendButton);
                
                // Agregar switch para modo intervención
                const interventionDiv = document.createElement('div');
                interventionDiv.className = 'intervention-switch';
                interventionDiv.innerHTML = `
                    <label class="switch">
                        <input type="checkbox" id="intervention-mode">
                        <span class="slider round"></span>
                    </label>
                    <span>Modo intervención</span>
                `;
                
                footer.appendChild(inputGroup);
                footer.appendChild(interventionDiv);
                panel.appendChild(footer);
            }
        }

        // Asegurar que Bootstrap Icons esté cargado
        if (!document.querySelector('link[href*="bootstrap-icons"]')) {
            const iconLink = document.createElement('link');
            iconLink.rel = 'stylesheet';
            iconLink.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css';
            document.head.appendChild(iconLink);
        }

        console.log('DevAssistant: Elementos creados dinámicamente');
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.devAssistant = new DevAssistant();

    // Si hay un ID de proyecto disponible, establecerlo
    if (window.projectId) {
        window.devAssistant.setProjectId(window.projectId);
    }
});
