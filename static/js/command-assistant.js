/**
 * Command Assistant - Integración con el asistente flotante
 * Asegura que la funcionalidad de comandos esté disponible a través del asistente flotante
 */

(function() {
    // Interfaz para el asistente de comandos
    const commandAssistant = {
        isConnected: false,
        connectionAttempts: 0,
        maxConnectionAttempts: 5,

        init: function() {
            console.log('Inicializando asistente de comandos...');

            // Asegurar que el asistente se inicialice en la página de xterm_terminal
            if (window.location.pathname.includes('xterm_terminal')) {
                this.initializeForXTerm();
                return;
            }

            // Verificar si el asistente flotante ya existe
            if (window.floatingAssistant) {
                console.log('Usando asistente flotante existente para comandos');
                this.checkServerConnection();
                return;
            }

            // Si no existe el asistente flotante, cargar el script
            this.loadFloatingAssistant();

            // Verificar conexión con el servidor
            this.checkServerConnection();
        },

        // Inicialización específica para la página xterm_terminal
        initializeForXTerm: function() {
            console.log('Configurando asistente para XTerm terminal');
            // Intento de conexión inmediato
            this.checkServerConnection();

            // Mostrar indicador visual de inicialización
            const assistantArea = document.querySelector('.assistant-container');
            if (assistantArea) {
                assistantArea.classList.add('initializing');
            }

            // Registrar manejadores de eventos para la terminal XTerm
            this.setupXTermEvents();
        },

        // Configurar eventos específicos para XTerm
        setupXTermEvents: function() {
            // Detectar el botón de consulta del asistente
            const assistantBtn = document.getElementById('assistant-btn');
            if (assistantBtn) {
                assistantBtn.addEventListener('click', () => {
                    if (!this.isConnected) {
                        console.log('Reconectando antes de procesar consulta...');
                        this.checkServerConnection();
                        this.showNotification('Reconectando con el servidor...', 'info');
                    }
                });
            }
        },

        // Verificar la conexión con el servidor
        checkServerConnection: function() {
            console.log('Verificando conexión con el servidor...');

            // Primero intentar con /api/status
            fetch('/api/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                timeout: 3000 // Timeout rápido para no bloquear UI
            })
            .then(response => {
                if (response.ok) {
                    this.connectionSuccessful(response);
                    return;
                }
                throw new Error('Respuesta no válida del servidor');
            })
            .catch(error => {
                console.warn('Error en primera ruta, intentando ruta alternativa:', error);
                // Intentar con ruta alternativa
                this.tryAlternativeConnection();
            });
        },

        // Intentar ruta alternativa para verificar la conexión
        tryAlternativeConnection: function() {
            fetch('/api/ping', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    this.connectionSuccessful(response);
                    return;
                }
                throw new Error('No se pudo establecer conexión con rutas alternativas');
            })
            .catch(error => {
                // Si ambas rutas fallan, intentar con la raíz
                fetch('/', { method: 'HEAD' })
                .then(response => {
                    if (response.ok) {
                        // El servidor está vivo pero las rutas API no funcionan
                        console.warn('Servidor disponible pero API no responde correctamente');
                        this.handleConnectionFailure('API no disponible en servidor');
                    } else {
                        this.handleConnectionFailure(error.message);
                    }
                })
                .catch(err => {
                    this.handleConnectionFailure(err.message);
                });
            });
        },

        // Manejar conexión exitosa
        connectionSuccessful: function(response) {
            this.isConnected = true;
            this.connectionAttempts = 0;
            console.log('Asistente de comandos conectado al servidor');

            // Actualizar estado en la UI
            this.updateConnectionStatus(true);

            // Mostrar notificación en XTerm si es aplicable
            if (window.showNotification) {
                window.showNotification('Asistente de comandos conectado', 'success');
            }

            return response.json().catch(() => ({}));
        },

        // Manejar fallo de conexión
        handleConnectionFailure: function(errorMsg) {
            console.warn('Error de conexión con el servidor:', errorMsg);
            this.isConnected = false;
            this.updateConnectionStatus(false);

            // Mostrar mensaje al usuario si existe la función de notificación
            if (window.showNotification) {
                window.showNotification('Error de conexión con el asistente', 'error');
            }

            // Intentar reconectar si no hemos excedido el número máximo de intentos
            if (this.connectionAttempts < this.maxConnectionAttempts) {
                this.connectionAttempts++;
                const delay = 1500 * this.connectionAttempts;
                console.log(`Intento de reconexión ${this.connectionAttempts} de ${this.maxConnectionAttempts} en ${delay}ms`);
                setTimeout(() => this.checkServerConnection(), delay);
            } else {
                console.error('Se alcanzó el número máximo de intentos de reconexión');
                if (window.showNotification) {
                    window.showNotification('No se pudo establecer conexión con el asistente después de varios intentos', 'error');
                }
            }
        },

        // Actualizar el estado de conexión en la UI si está disponible
        updateConnectionStatus: function(isConnected) {
            // Actualizar en el asistente flotante si existe
            if (window.floatingAssistant && window.floatingAssistant.updateConnectionStatus) {
                window.floatingAssistant.updateConnectionStatus(isConnected);
            }

            // Actualizar en la UI de XTerm si existe
            const assistantResult = document.getElementById('assistant-result');
            if (assistantResult) {
                if (isConnected) {
                    assistantResult.innerHTML = `
                        <div class="text-center py-3">
                            <p class="text-success mb-1"><i class="bi bi-check-circle"></i> Asistente conectado</p>
                            <small class="text-muted">Describe lo que necesitas hacer y te daré el comando exacto</small>
                        </div>
                    `;
                } else {
                    assistantResult.innerHTML = `
                        <div class="text-center py-3">
                            <p class="text-danger mb-1"><i class="bi bi-exclamation-triangle"></i> Asistente desconectado</p>
                            <small class="text-muted">Intentando reconectar...</small>
                            <button id="retry-connection" class="btn btn-sm btn-outline-primary mt-2">
                                <i class="bi bi-arrow-repeat"></i> Reintentar conexión
                            </button>
                        </div>
                    `;
                }

                // Agregar evento al botón de reintento
                const retryButton = document.getElementById('retry-connection');
                if (retryButton) {
                    retryButton.addEventListener('click', () => {
                        this.connectionAttempts = 0; // Reiniciar contador
                        this.checkServerConnection();
                    });
                }
            }

            // Disparar evento para que otros componentes puedan escucharlo
            document.dispatchEvent(new CustomEvent('assistant-connection-status', {
                detail: { connected: isConnected }
            }));
        },

        // Cargar el script del asistente flotante
        loadFloatingAssistant: function() {
            const script = document.createElement('script');
            script.src = '/static/js/floating-assistant.js';
            script.async = true;
            script.onload = function() {
                console.log('Asistente flotante cargado correctamente');
                // Asegurar que las dependencias de estilo están cargadas
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = '/static/css/floating-assistant.css';
                document.head.appendChild(link);
            };
            script.onerror = function() {
                console.error('Error al cargar el asistente flotante');
            };
            document.head.appendChild(script);
        },

        // Método para procesar comandos a través del asistente flotante
        processCommand: function(command) {
            if (!this.isConnected) {
                console.warn('No se puede procesar comando: asistente desconectado');
                if (window.showNotification) {
                    window.showNotification('Asistente desconectado. Intenta reconectar.', 'warning');
                }
                return Promise.reject(new Error('Asistente desconectado'));
            }

            if (window.floatingAssistant) {
                return window.floatingAssistant.processQuery(command);
            } else {
                // Implementar procesamiento directo al API
                return fetch('/api/process_instructions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        instruction: command,
                        model: document.getElementById('assistant-model')?.value || 'openai'
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error en la respuesta: ${response.status}`);
                    }
                    return response.json();
                });
            }
        },

        // Utilidad para mostrar notificaciones
        showNotification: function(message, type) {
            if (window.showNotification) {
                window.showNotification(message, type);
            } else {
                console.log(`[${type}] ${message}`);
            }
        }
    };

    // Exponer al ámbito global
    window.commandAssistant = commandAssistant;

    // Inicializar solo si estamos en una página que usa el asistente
    const initAssistant = () => {
        // Verificar si la página actual necesita el asistente
        try {
            if (document.querySelector('[data-needs-assistant]') || 
                document.getElementById('floating-assistant-container') ||
                window.location.pathname.includes('xterm_terminal') ||
                document.getElementById('assistant-btn')) {
                commandAssistant.init();
            } else {
                console.log('Esta página no requiere el asistente de comandos');
            }
        } catch (error) {
            console.error('Error durante la inicialización del asistente:', error);
        }
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAssistant);
    } else {
        initAssistant();
    }
})();

// Función para eliminar un archivo o directorio
function deleteFile(filePath) {
    if (!filePath) return;

    if (confirm(`¿Estás seguro de eliminar "${filePath}"?`)) {
        // Mostrar indicador de carga
        showNotification('Eliminando archivo...', 'info');

        // Enviar petición al servidor para eliminar
        fetch('/api/file/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_path: filePath })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification('Archivo eliminado correctamente', 'success');
                // Recargar el explorador de archivos
                refreshFileExplorer();

                // Notificar al sistema de terminales si está disponible
                if (window.terminalInterface && window.terminalInterface.loadFiles) {
                    window.terminalInterface.loadFiles('.');
                }

                // Emitir evento para que otros componentes lo detecten
                document.dispatchEvent(new CustomEvent('file_deleted', {
                    detail: { path: filePath }
                }));
            } else {
                showNotification(`Error: ${data.error || 'No se pudo eliminar el archivo'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error al eliminar archivo:', error);
            showNotification(`Error: ${error.message}`, 'error');
        });
    }
}

// Función para cerrar el modal de visualización de archivos
function closeFileViewer() {
    const fileViewer = document.getElementById('file-viewer-modal');
    if (fileViewer) {
        // Aplicar animación de cierre
        fileViewer.classList.add('fade-out');

        // Esperar a que termine la animación
        setTimeout(() => {
            fileViewer.style.display = 'none';
            fileViewer.classList.remove('fade-out');

            // Limpiar contenido para liberar memoria
            const contentContainer = fileViewer.querySelector('.modal-content');
            if (contentContainer) {
                contentContainer.innerHTML = '';
            }

            // Desbloquear scroll del body si estaba bloqueado
            document.body.style.overflow = '';

            // Emitir evento de cierre
            document.dispatchEvent(new CustomEvent('file_viewer_closed'));
        }, 300);
    }

    // Si hay un listener de tecla Escape, eliminarlo
    document.removeEventListener('keydown', handleEscapeKeyForModal);
}

// Manejador para la tecla Escape
function handleEscapeKeyForModal(e) {
    if (e.key === 'Escape') {
        closeFileViewer();
    }
}

// Modificamos la función de apertura del modal para añadir el listener de Escape
function openFileViewer(filePath, content, fileName) {
    const fileViewer = document.getElementById('file-viewer-modal');
    if (!fileViewer) return;

    // Configurar contenido
    const titleElement = fileViewer.querySelector('.modal-title');
    const contentElement = fileViewer.querySelector('.modal-body');

    if (titleElement) titleElement.textContent = fileName || filePath;
    if (contentElement) contentElement.innerHTML = `<pre class="file-content">${content}</pre>`;

    // Mostrar modal con animación
    fileViewer.style.display = 'flex';
    fileViewer.classList.add('fade-in');
    setTimeout(() => fileViewer.classList.remove('fade-in'), 300);

    // Bloquear scroll del body
    document.body.style.overflow = 'hidden';

    // Añadir listener para la tecla Escape
    document.addEventListener('keydown', handleEscapeKeyForModal);
}