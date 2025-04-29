
/**
 * Command Assistant - Módulo para convertir lenguaje natural a comandos de terminal
 * Este módulo permite interactuar con diferentes modelos de IA para generar comandos
 */

(function() {
    // Configuración del asistente
    const commandAssistant = {
        models: {
            'openai': 'OpenAI (GPT-4o)',
            'anthropic': 'Anthropic (Claude)',
            'gemini': 'Google (Gemini)'
        },
        activeModel: 'openai',
        
        // Inicializar el asistente
        init: function() {
            // Crear interfaz de usuario
            this.createUI();
            // Añadir event listeners
            this.bindEvents();
        },
        
        // Crear elementos de UI
        createUI: function() {
            // Verificar si ya existe el panel
            if (document.getElementById('command-assistant-panel')) return;
            
            // Crear panel del asistente
            const panel = document.createElement('div');
            panel.id = 'command-assistant-panel';
            panel.className = 'command-assistant-panel';
            panel.innerHTML = `
                <div class="assistant-header">
                    <h4><i class="bi bi-robot"></i> Asistente de Comandos</h4>
                    <div class="assistant-controls">
                        <select id="assistant-model-select" class="form-select form-select-sm">
                            ${Object.entries(this.models).map(([key, name]) => 
                                `<option value="${key}"${key === this.activeModel ? ' selected' : ''}>${name}</option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
                <div class="assistant-body">
                    <textarea id="assistant-input" class="form-control" 
                        placeholder="Describe lo que quieres hacer en lenguaje natural..."></textarea>
                    <div class="assistant-buttons mt-2">
                        <button id="assistant-clear-btn" class="btn btn-sm btn-secondary">
                            <i class="bi bi-x-circle"></i> Limpiar
                        </button>
                        <button id="assistant-send-btn" class="btn btn-sm btn-primary">
                            <i class="bi bi-send"></i> Consultar
                            <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                        </button>
                    </div>
                </div>
                <div class="assistant-result mt-2" id="assistant-result">
                    <div class="text-muted text-center py-3">
                        <small>El asistente generará comandos a partir de tus instrucciones en lenguaje natural</small>
                    </div>
                </div>
            `;
            
            // Añadir estilos
            const style = document.createElement('style');
            style.textContent = `
                .command-assistant-panel {
                    background-color: #121824;
                    border: 1px solid #2a3041;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    overflow: hidden;
                }
                
                .assistant-header {
                    background: linear-gradient(90deg, #0a1428 0%, #0d2855 100%);
                    padding: 10px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #2a3041;
                }
                
                .assistant-header h4 {
                    margin: 0;
                    font-size: 1rem;
                    color: #ffffff;
                }
                
                .assistant-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .assistant-body {
                    padding: 15px;
                    background-color: #121824;
                }
                
                .assistant-buttons {
                    display: flex;
                    justify-content: flex-end;
                    gap: 8px;
                }
                
                .assistant-result {
                    padding: 10px 15px;
                    background-color: #0a1020;
                    border-top: 1px solid #2a3041;
                    max-height: 150px;
                    overflow-y: auto;
                }
                
                .command-item {
                    background-color: #1a2133;
                    border: 1px solid #2a3041;
                    border-radius: 4px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .command-text {
                    font-family: monospace;
                    color: #50fa7b;
                }
                
                .command-actions {
                    display: flex;
                    gap: 5px;
                }
                
                .command-actions button {
                    background: none;
                    border: none;
                    color: #6272a4;
                    cursor: pointer;
                    padding: 2px;
                    font-size: 14px;
                    transition: color 0.2s;
                }
                
                .command-actions button:hover {
                    color: #bd93f9;
                }
            `;
            
            // Añadir al DOM
            document.head.appendChild(style);
            
            // Buscar el contenedor donde insertar el panel
            const terminalPanel = document.querySelector('.terminal-panel');
            if (terminalPanel) {
                terminalPanel.insertBefore(panel, terminalPanel.firstChild);
            } else {
                // Como alternativa, insertar antes del terminal-container
                const terminalContainer = document.getElementById('terminal-container');
                if (terminalContainer) {
                    terminalContainer.parentNode.insertBefore(panel, terminalContainer);
                } else {
                    // Si no encontramos ningún lugar específico, lo añadimos al body
                    document.body.appendChild(panel);
                }
            }
        },
        
        // Enlazar eventos
        bindEvents: function() {
            const sendBtn = document.getElementById('assistant-send-btn');
            const clearBtn = document.getElementById('assistant-clear-btn');
            const input = document.getElementById('assistant-input');
            const modelSelect = document.getElementById('assistant-model-select');
            
            if (sendBtn) {
                sendBtn.addEventListener('click', () => this.processRequest());
            }
            
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    input.value = '';
                    input.focus();
                });
            }
            
            if (input) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        this.processRequest();
                    }
                });
            }
            
            if (modelSelect) {
                modelSelect.addEventListener('change', (e) => {
                    this.activeModel = e.target.value;
                });
            }
        },
        
        // Procesar petición al asistente
        processRequest: function() {
            const input = document.getElementById('assistant-input');
            const resultContainer = document.getElementById('assistant-result');
            const spinner = document.querySelector('#assistant-send-btn .spinner-border');
            const sendBtn = document.getElementById('assistant-send-btn');
            
            if (!input || !resultContainer) return;
            
            const query = input.value.trim();
            if (!query) return;
            
            // Mostrar estado cargando
            if (spinner) spinner.classList.remove('d-none');
            if (sendBtn) sendBtn.disabled = true;
            
            resultContainer.innerHTML = `
                <div class="text-center py-3">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                    <p class="mt-2 text-muted">Generando comando...</p>
                </div>
            `;
            
            // Configurar timeout para abortar petición si tarda demasiado
            const controller = new AbortController();
            const signal = controller.signal;
            const timeout = setTimeout(() => {
                controller.abort();
            }, 30000); // 30 segundos de timeout
            
            // Enviar petición al servidor con control de timeout
            fetch('/api/process_instructions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    instruction: query,
                    model: this.activeModel
                }),
                signal: signal
            })
            .then(response => {
                clearTimeout(timeout);
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Ocultar spinner
                if (spinner) spinner.classList.add('d-none');
                if (sendBtn) sendBtn.disabled = false;
                
                if (data.command) {
                    // Mostrar comando generado
                    resultContainer.innerHTML = `
                        <div class="command-item">
                            <div class="command-text">${data.command}</div>
                            <div class="command-actions">
                                <button title="Copiar al portapapeles" class="copy-btn">
                                    <i class="bi bi-clipboard"></i>
                                </button>
                                <button title="Ejecutar comando" class="execute-btn">
                                    <i class="bi bi-play"></i>
                                </button>
                            </div>
                        </div>
                        <div class="text-muted text-center">
                            <small>Instrucción procesada correctamente</small>
                        </div>
                    `;
                    
                    // Añadir funcionalidad a los botones con manejo mejorado de eventos
                    const copyBtn = resultContainer.querySelector('.copy-btn');
                    const executeBtn = resultContainer.querySelector('.execute-btn');
                    
                    if (copyBtn) {
                        const copyHandler = () => {
                            navigator.clipboard.writeText(data.command)
                                .then(() => {
                                    this.showNotification('Comando copiado al portapapeles', 'success');
                                })
                                .catch(err => {
                                    console.error('Error al copiar:', err);
                                    this.showNotification('Error al copiar comando', 'danger');
                                });
                        };
                        
                        // Usar evento una vez
                        copyBtn.addEventListener('click', copyHandler, {once: false});
                    }
                    
                    if (executeBtn) {
                        const executeHandler = () => {
                            // Crear una promesa para resolver la ejecución del comando
                            const executePromise = new Promise((resolve, reject) => {
                                // Verificar si existe la función global para ejecutar comandos
                                if (window.terminalInterface && typeof window.terminalInterface.executeCommand === 'function') {
                                    try {
                                        window.terminalInterface.executeCommand(data.command);
                                        resolve({success: true});
                                    } catch (err) {
                                        reject(err);
                                    }
                                } else if (window.executeCommand && typeof window.executeCommand === 'function') {
                                    try {
                                        window.executeCommand(data.command);
                                        resolve({success: true});
                                    } catch (err) {
                                        reject(err);
                                    }
                                } else {
                                    // Como alternativa, enviar el comando al servidor directamente
                                    // Configurar timeout para esta petición también
                                    const cmdController = new AbortController();
                                    const cmdSignal = cmdController.signal;
                                    const cmdTimeout = setTimeout(() => cmdController.abort(), 15000);
                                    
                                    fetch('/api/execute_command', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({
                                            command: data.command
                                        }),
                                        signal: cmdSignal
                                    })
                                    .then(response => {
                                        clearTimeout(cmdTimeout);
                                        if (!response.ok) {
                                            throw new Error(`Error: ${response.status} ${response.statusText}`);
                                        }
                                        return response.json();
                                    })
                                    .then(cmdResult => {
                                        resolve(cmdResult);
                                    })
                                    .catch(err => {
                                        reject(err);
                                    });
                                }
                            });
                            
                            // Manejar resultado de la ejecución
                            executePromise
                                .then(cmdResult => {
                                    this.showNotification('Comando ejecutado', 'success');
                                    
                                    // Si hay un terminal-output, mostrar salida
                                    const outputDisplay = document.getElementById('output-display');
                                    if (outputDisplay && cmdResult.stdout !== undefined) {
                                        outputDisplay.innerHTML = `<div><strong>Ejecutado:</strong> ${data.command}</div>`;
                                        if (cmdResult.stdout) {
                                            outputDisplay.innerHTML += `<pre>${cmdResult.stdout}</pre>`;
                                        }
                                        if (cmdResult.stderr) {
                                            outputDisplay.innerHTML += `<pre class="text-danger">${cmdResult.stderr}</pre>`;
                                        }
                                    }
                                })
                                .catch(err => {
                                    console.error('Error al ejecutar:', err);
                                    this.showNotification('Error al ejecutar comando: ' + (err.message || 'Error desconocido'), 'danger');
                                });
                        };
                        
                        // Usar evento con gestión de errores
                        executeBtn.addEventListener('click', () => {
                            try {
                                executeHandler();
                            } catch (err) {
                                console.error('Error en manejador de ejecución:', err);
                                this.showNotification('Error interno al ejecutar comando', 'danger');
                            }
                        });
                    }
                } else {
                    // Mostrar error
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">
                            ${data.error || 'Error al procesar la instrucción'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                clearTimeout(timeout);
                console.error('Error:', error);
                
                // Ocultar spinner
                if (spinner) spinner.classList.add('d-none');
                if (sendBtn) sendBtn.disabled = false;
                
                // Personalizar mensaje según el tipo de error
                let errorMessage = 'Error al comunicarse con el servidor';
                
                if (error.name === 'AbortError') {
                    errorMessage = 'La solicitud ha excedido el tiempo de espera. Por favor, intenta de nuevo.';
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                // Mostrar error
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">
                        ${errorMessage}
                    </div>
                `;
                
                this.showNotification('Error al procesar instrucción', 'danger');
            });
        },
        
        // Mostrar notificación
        showNotification: function(message, type = 'info') {
            // Usar función global si existe
            if (window.showNotification && typeof window.showNotification === 'function') {
                window.showNotification(message, type);
                return;
            }
            
            // Implementación propia como fallback
            const container = document.getElementById('notifications');
            if (!container) return;
            
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show`;
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            container.appendChild(notification);
            
            // Auto-eliminar después de 5 segundos
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
    };
    
    // Exponer al ámbito global
    window.commandAssistant = commandAssistant;
    
    // Inicializar automáticamente si el DOM ya está cargado
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(() => commandAssistant.init(), 100);
    } else {
        document.addEventListener('DOMContentLoaded', () => commandAssistant.init());
    }
})();
