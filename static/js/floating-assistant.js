
/**
 * Command Assistant - Asistente flotante para comandos de terminal
 * Responde únicamente con comandos para terminal sin comentarios adicionales
 */

(function() {
    // Estado y configuración del asistente
    const assistant = {
        isOpen: false,
        activeModel: 'openai',
        isProcessing: false,
        
        models: {
            'openai': 'OpenAI (GPT-4o)',
            'anthropic': 'Anthropic (Claude)',
            'gemini': 'Google (Gemini)'
        },
        
        // Inicializar el asistente
        init: function() {
            this.createElements();
            this.bindEvents();
            this.loadScript('https://cdn.jsdelivr.net/npm/marked/marked.min.js');
            
            // Retraso para inicializar después de que termine el documento
            setTimeout(() => {
                if (document.readyState === 'complete') {
                    this.checkConnectionStatus();
                }
            }, 1000);
        },
        
        // Crear elementos del asistente
        createElements: function() {
            const floatingBtn = document.createElement('div');
            floatingBtn.id = 'floating-assistant-btn';
            floatingBtn.className = 'floating-assistant-btn';
            floatingBtn.innerHTML = '<i class="bi bi-terminal"></i>';
            
            const assistantPanel = document.createElement('div');
            assistantPanel.id = 'assistant-panel';
            assistantPanel.className = 'assistant-panel hidden';
            
            assistantPanel.innerHTML = `
                <div class="assistant-header">
                    <h5><i class="bi bi-terminal"></i> Asistente de Comandos</h5>
                    <button id="assistant-close" class="assistant-close">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
                <div class="assistant-body">
                    <div class="model-selector mb-2">
                        <select id="assistant-model" class="form-select form-select-sm">
                            ${Object.entries(this.models).map(([key, name]) => 
                                `<option value="${key}"${key === this.activeModel ? ' selected' : ''}>${name}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div id="assistant-result" class="assistant-result">
                        <div class="text-center py-3">
                            <p class="text-muted mb-1">Asistente de Comandos</p>
                            <small class="text-muted">Describe lo que necesitas hacer y te daré el comando exacto</small>
                        </div>
                    </div>
                    <div class="assistant-input-container">
                        <textarea 
                            id="assistant-input" 
                            class="assistant-input" 
                            placeholder="Describe lo que quieres hacer en lenguaje natural..."></textarea>
                        <button id="assistant-send" class="assistant-send">
                            <i class="bi bi-send"></i>
                        </button>
                    </div>
                </div>
            `;
            
            // Agregar elementos al DOM
            document.body.appendChild(floatingBtn);
            document.body.appendChild(assistantPanel);
            
            // Cargar estilos si no están ya cargados
            if (!document.getElementById('floating-assistant-styles')) {
                const link = document.createElement('link');
                link.id = 'floating-assistant-styles';
                link.rel = 'stylesheet';
                link.href = '/static/css/floating-assistant.css';
                document.head.appendChild(link);
            }
        },
        
        // Asociar eventos
        bindEvents: function() {
            const floatingBtn = document.getElementById('floating-assistant-btn');
            const closeBtn = document.getElementById('assistant-close');
            const sendBtn = document.getElementById('assistant-send');
            const input = document.getElementById('assistant-input');
            const modelSelect = document.getElementById('assistant-model');
            
            if (floatingBtn) {
                floatingBtn.addEventListener('click', () => this.togglePanel());
            }
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.togglePanel(false));
            }
            
            if (sendBtn && input) {
                sendBtn.addEventListener('click', () => this.processQuery());
                
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.processQuery();
                    }
                });
            }
            
            if (modelSelect) {
                modelSelect.addEventListener('change', (e) => {
                    this.activeModel = e.target.value;
                    console.log('Modelo cambiado a:', this.activeModel);
                });
            }
            
            // Cerrar panel al hacer clic fuera
            document.addEventListener('click', (e) => {
                const panel = document.getElementById('assistant-panel');
                const btn = document.getElementById('floating-assistant-btn');
                
                if (this.isOpen && panel && btn && 
                    !panel.contains(e.target) && 
                    !btn.contains(e.target)) {
                    this.togglePanel(false);
                }
            });
        },
        
        // Alternar visibilidad del panel
        togglePanel: function(forceState) {
            const panel = document.getElementById('assistant-panel');
            if (!panel) return;
            
            this.isOpen = forceState !== undefined ? forceState : !this.isOpen;
            
            if (this.isOpen) {
                panel.classList.remove('hidden');
                // Enfocar el input automáticamente
                setTimeout(() => {
                    const input = document.getElementById('assistant-input');
                    if (input) input.focus();
                }, 300);
            } else {
                panel.classList.add('hidden');
            }
        },
        
        // Procesar consulta del usuario
        processQuery: function() {
            const input = document.getElementById('assistant-input');
            const result = document.getElementById('assistant-result');
            const sendBtn = document.getElementById('assistant-send');
            
            if (!input || !result || !sendBtn) return;
            
            const query = input.value.trim();
            if (!query || this.isProcessing) return;
            
            // Actualizar estado
            this.isProcessing = true;
            sendBtn.disabled = true;
            
            // Mostrar mensaje del usuario
            this.addMessage('user', query);
            
            // Limpiar input
            input.value = '';
            
            // Mostrar indicador de carga
            this.addLoadingIndicator();
            
            // Preparar datos para la petición
            const requestData = {
                message: query,
                model: this.activeModel,
                agent_id: 'command',
                format: 'markdown',
                command_only: true
            };
            
            // Enviar petición al servidor con gestión mejorada de errores y timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 segundos de timeout
            
            fetch('/api/process_instructions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData),
                signal: controller.signal
            })
            .then(response => {
                clearTimeout(timeoutId);
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Eliminar indicador de carga
                this.removeLoadingIndicator();
                
                // Procesar respuesta - solo mostrar el comando
                if (data.command) {
                    this.addCommandResult(data.command);
                    
                    // Mostrar notificación si el comando afecta archivos
                    if (data.command.includes('mkdir') || data.command.includes('touch')) {
                        this.showToast('Comando ejecutado: se creará un nuevo elemento', 'success');
                    }
                } else if (data.error) {
                    if (data.needs_more_info) {
                        // Si falta información, mostrar mensaje claro
                        this.addErrorMessage(`${data.error}. Por favor, proporciona más detalles.`);
                    } else {
                        this.addErrorMessage(data.error);
                    }
                } else if (data.response) {
                    // Intentar extraer comando de la respuesta
                    const commandMatch = data.response.match(/```(bash|sh)?\s*([^`]+)```/);
                    if (commandMatch && commandMatch[2]) {
                        this.addCommandResult(commandMatch[2].trim());
                    } else {
                        this.addCommandResult(data.response);
                    }
                } else {
                    this.addErrorMessage('No se pudo generar un comando.');
                }
            })
            .catch(error => {
                // Eliminar indicador de carga
                this.removeLoadingIndicator();
                
                // Manejar errores específicos
                if (error.name === 'AbortError') {
                    this.addErrorMessage('La solicitud excedió el tiempo de espera. Por favor, intenta de nuevo.');
                } else if (error.message.includes('Failed to fetch')) {
                    this.addErrorMessage('Error de conexión. Verifica tu conexión a internet.');
                } else {
                    this.addErrorMessage(`Error: ${error.message}`);
                }
                
                console.error('Error al procesar consulta:', error);
            })
            .finally(() => {
                // Restaurar estado
                this.isProcessing = false;
                if (sendBtn) sendBtn.disabled = false;
            });
        },
        
        // Añadir mensaje al chat
        addMessage: function(role, content) {
            const result = document.getElementById('assistant-result');
            if (!result) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            
            // Para mensajes del usuario, convertir saltos de línea en <br>
            if (role === 'user') {
                messageDiv.innerHTML = content.replace(/\n/g, '<br>');
            } else {
                // Para el asistente no mostraremos mensajes de texto, solo comandos
                return;
            }
            
            result.appendChild(messageDiv);
            
            // Scroll al final
            result.scrollTop = result.scrollHeight;
        },
        
        // Añadir mensaje de error
        addErrorMessage: function(error) {
            const result = document.getElementById('assistant-result');
            if (!result) return;
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message error-message';
            errorDiv.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${error}`;
            
            result.appendChild(errorDiv);
            result.scrollTop = result.scrollHeight;
        },
        
        // Añadir resultado de comando
        addCommandResult: function(command) {
            const result = document.getElementById('assistant-result');
            if (!result) return;
            
            // Limpiar resultados anteriores para mostrar solo el comando actual
            const existingCommands = result.querySelectorAll('.command-item');
            existingCommands.forEach(item => item.remove());
            
            const commandDiv = document.createElement('div');
            commandDiv.className = 'command-item';
            commandDiv.innerHTML = `
                <div class="command-text">
                    <pre><code>${command.trim()}</code></pre>
                </div>
                <div class="command-actions">
                    <button title="Copiar comando" class="copy-btn">
                        <i class="bi bi-clipboard"></i>
                    </button>
                    <button title="Ejecutar comando" class="execute-btn">
                        <i class="bi bi-play"></i>
                    </button>
                </div>
            `;
            
            // Añadir eventos a los botones
            const copyBtn = commandDiv.querySelector('.copy-btn');
            const executeBtn = commandDiv.querySelector('.execute-btn');
            
            if (copyBtn) {
                copyBtn.addEventListener('click', () => {
                    navigator.clipboard.writeText(command.trim())
                        .then(() => this.showToast('Comando copiado al portapapeles'))
                        .catch(err => console.error('Error al copiar:', err));
                });
            }
            
            if (executeBtn) {
                executeBtn.addEventListener('click', () => {
                    this.executeCommand(command.trim());
                });
            }
            
            result.appendChild(commandDiv);
            result.scrollTop = result.scrollHeight;
        },
        
        // Ejecutar comando
        executeCommand: function(command) {
            // Buscar interfaz de terminal disponible
            if (window.terminalInterface && typeof window.terminalInterface.executeCommand === 'function') {
                window.terminalInterface.executeCommand(command);
                this.showToast('Comando ejecutado en terminal');
            } else if (window.executeCommand && typeof window.executeCommand === 'function') {
                window.executeCommand(command);
                this.showToast('Comando ejecutado');
            } else {
                // Fallback: enviar al servidor
                fetch('/api/execute_command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ command })
                })
                .then(response => response.json())
                .then(data => {
                    this.showToast('Comando ejecutado');
                    
                    // Añadir resultado si está disponible
                    if (data.stdout || data.stderr) {
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'command-result';
                        
                        if (data.stdout) {
                            resultDiv.innerHTML += `<pre class="stdout">${data.stdout}</pre>`;
                        }
                        
                        if (data.stderr) {
                            resultDiv.innerHTML += `<pre class="stderr">${data.stderr}</pre>`;
                        }
                        
                        const result = document.getElementById('assistant-result');
                        if (result) {
                            result.appendChild(resultDiv);
                            result.scrollTop = result.scrollHeight;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error al ejecutar comando:', error);
                    this.showToast('Error al ejecutar comando', 'error');
                });
            }
        },
        
        // Añadir indicador de carga
        addLoadingIndicator: function() {
            const result = document.getElementById('assistant-result');
            if (!result) return;
            
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'assistant-loading';
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = `
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <div class="loading-text">Procesando...</div>
            `;
            
            result.appendChild(loadingDiv);
            result.scrollTop = result.scrollHeight;
        },
        
        // Eliminar indicador de carga
        removeLoadingIndicator: function() {
            const loadingIndicator = document.getElementById('assistant-loading');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        },
        
        // Formatear bloques de código
        formatCodeBlocks: function() {
            const result = document.getElementById('assistant-result');
            if (!result) return;
            
            const codeBlocks = result.querySelectorAll('pre code');
            codeBlocks.forEach((block, index) => {
                // Añadir clases para resaltado si no las tiene
                if (!block.classList.contains('hljs') && !block.classList.contains('language-')) {
                    // Detectar el lenguaje si no está especificado
                    if (block.className === '') {
                        block.className = 'language-plaintext';
                    }
                }
                
                // Aplicar highlight.js si está disponible
                if (window.hljs) {
                    try {
                        window.hljs.highlightElement(block);
                    } catch (e) {
                        console.warn('Error al aplicar highlight.js:', e);
                    }
                }
            });
        },
        
        // Comprobar estado de conexión
        checkConnectionStatus: function() {
            fetch('/api/health')
                .then(response => {
                    if (response.ok) {
                        console.log('Asistente conectado correctamente al servidor');
                    } else {
                        console.warn('El servidor está respondiendo pero con estado:', response.status);
                    }
                })
                .catch(error => {
                    console.error('Error al verificar estado del servidor:', error);
                });
        },
        
        // Mostrar notificación toast
        showToast: function(message, type = 'info') {
            // Buscar o crear contenedor de notificaciones
            let container = document.getElementById('toast-container');
            
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container position-fixed bottom-0 start-50 translate-middle-x p-3';
                container.style.zIndex = '10000';
                document.body.appendChild(container);
            }
            
            // Crear toast
            const toastId = 'toast-' + Date.now();
            const toast = document.createElement('div');
            toast.id = toastId;
            toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'info'} border-0`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            
            container.appendChild(toast);
            
            // Mostrar y ocultar automáticamente
            const bsToast = new bootstrap.Toast(toast, {
                animation: true,
                autohide: true,
                delay: 3000
            });
            
            bsToast.show();
            
            // Eliminar después de ocultarse
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        },
        
        // Cargar script dinámicamente
        loadScript: function(url) {
            return new Promise((resolve, reject) => {
                // Verificar si ya está cargado
                const scripts = document.getElementsByTagName('script');
                for (let i = 0; i < scripts.length; i++) {
                    if (scripts[i].src === url) {
                        resolve();
                        return;
                    }
                }
                
                // Cargar el script
                const script = document.createElement('script');
                script.src = url;
                script.async = true;
                
                script.onload = () => resolve();
                script.onerror = () => reject(new Error(`Error al cargar script: ${url}`));
                
                document.head.appendChild(script);
            });
        }
    };
    
    // Exponer al ámbito global
    window.floatingAssistant = assistant;
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => assistant.init());
    } else {
        assistant.init();
    }
})();
