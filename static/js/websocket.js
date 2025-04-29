// WebSocket client for real-time file updates
document.addEventListener('DOMContentLoaded', function() {
    // Wait a short moment to ensure Socket.IO is fully loaded
    setTimeout(function() {
        // Check if SocketIO is available
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded, attempting to load it now');
            // Load Socket.IO client library if not already loaded
            const script = document.createElement('script');
            script.src = 'https://cdn.socket.io/4.6.1/socket.io.min.js';
            script.onload = function() {
                console.log('Socket.IO loaded successfully');
                initializeSocket();
            };
            script.onerror = function() {
                console.error('Failed to load Socket.IO');
            };
            document.head.appendChild(script);
        } else {
            console.log('Socket.IO already loaded');
            initializeSocket();
        }
    }, 100); // Small delay to ensure dependencies are loaded

    function initializeSocket() {
        // Get the current hostname and use the same URL as the page
        const socketUrl = window.location.origin;

        console.log('Connecting to Socket.IO server at:', socketUrl);

        // Connect to Socket.IO server with more resilient configuration
        const socket = io(socketUrl, {
            path: '/socket.io',
            transports: ['websocket', 'polling'], // Fallback to polling if websocket fails
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000
        });

        // Store socket globally for other scripts to use
        window.socketClient = socket;

        // Función para ejecutar comandos desde la terminal
        window.executeTerminalCommand = function(command) {
            if (!command) return;

            console.log("Ejecutando comando:", command);

            // Verificar si tenemos socket disponible
            if (!window.socketClient) {
                console.error("Socket no disponible para ejecutar comando");
                return;
            }

            // Enviar comando al servidor vía WebSocket
            window.socketClient.emit('terminal_command', {
                command: command,
                user_id: localStorage.getItem('user_id') || 'default'
            });

            // También hacer una solicitud HTTP para mayor fiabilidad
            fetch('/api/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    user_id: localStorage.getItem('user_id') || 'default'
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Respuesta del servidor:", data);

                // Si el comando modifica archivos, forzar actualización del explorador
                if (data.refresh_explorer) {
                    setTimeout(refreshFileExplorer, 300);
                }
            })
            .catch(error => {
                console.error("Error al ejecutar comando:", error);
            });
        };

        // Socket connection handlers
        socket.on('connect', function() {
            console.log('Connected to WebSocket server');

            // Join the current workspace room
            const userId = localStorage.getItem('user_id') || 'default';
            socket.emit('join_workspace', {
                workspace_id: userId
            });

            // Update UI to show connected status
            updateConnectionStatus(true);

            // Immediately request file list update
            refreshFileExplorer();
        });

        socket.on('disconnect', function() {
            console.log('Disconnected from WebSocket server');
            updateConnectionStatus(false);
        });

        socket.on('connect_error', function(error) {
            console.error('WebSocket connection error:', error);
            updateConnectionStatus(false);

            // Implementar reintentos manuales con backoff exponencial
            setTimeout(() => {
                console.log('Intentando reconectar al WebSocket...');
                socket.connect();
            }, 2000); // Reintento después de 2 segundos
        });

        // Manejador de error adicional
        socket.on('error', function(error) {
            console.error('Socket error:', error);
            // No desconectar inmediatamente, dejar que la reconexión automática funcione
        });

        // File change notifications
        socket.on('file_change', function(data) {
            console.log('File change notification:', data);

            // Verificar si el cambio pertenece al usuario actual
            const currentUserId = localStorage.getItem('user_id') || 'default';
            const changeUserId = data.user_id || 'default';

            // Si el cambio es para otro usuario y no es broadcast, ignorar
            if (data.user_id && data.user_id !== currentUserId && !data.broadcast) {
                console.log(`Ignorando cambio para otro usuario: ${data.user_id}`);
                return;
            }

            // Force immediate refresh of file explorer
            setTimeout(() => {
                refreshFileExplorer();

                // Notify parent window if we're in an iframe
                notifyParentWindow(data);

                // Display notification to user
                notifyFileChange(data.type, data.file);

                // Programar una segunda actualización para asegurarse de que todos los cambios se reflejen
                setTimeout(refreshFileExplorer, 800);
            }, 300); // Small delay to ensure the file is available
        });

        // File sync event handler
        socket.on('file_sync', function(data) {
            console.log('File sync event received:', data);
            refreshFileExplorer();
        });

        // Terminal command execution notifications
        socket.on('command_executed', function(data) {
            console.log('Command executed notification:', data);

            // Update terminal output if needed
            if (typeof app !== 'undefined' && app.updateCommandOutput) {
                app.updateCommandOutput(data);
            }

            // Notificar la ejecución del comando
            notifyCommandExecution(data);

            // Refresh file explorer after command execution (commands often create/modify files)
            setTimeout(refreshFileExplorer, 300);

            // Programar una segunda actualización para asegurarse de que todos los cambios se reflejen
            setTimeout(refreshFileExplorer, 1500);
        });

        // File commands notification handler
        socket.on('file_command', function(data) {
            console.log('File command notification:', data);

            // Notificar creación/modificación de archivos
            notifyFileChange(data.type || 'update', data.file || {path: data.command});

            // Refresh file explorer immediately
            refreshFileExplorer();
        });

        // Expose refresh function globally with enhanced functionality
        window.refreshFileExplorer = function() {
            console.log("Actualizando explorador de archivos...");
            refreshFileExplorer();
            
            // Emitir evento para componentes que escuchan eventos de actualización
            document.dispatchEvent(new CustomEvent('files_updated', {
                detail: { refreshed: true, timestamp: Date.now() }
            }));
            
            // Si estamos en un iframe, notificar al padre
            if (window.parent && window.parent !== window) {
                try {
                    window.parent.postMessage({
                        type: 'explorer_refresh',
                        timestamp: Date.now()
                    }, '*');
                } catch (e) {
                    console.warn("No se pudo notificar al padre:", e);
                }
            }
        };
    }

    // Function to refresh file explorer
    function refreshFileExplorer() {
        console.log("Refreshing file explorer...");

        // Prevent multiple refreshes in quick succession
        if (window._refreshInProgress) {
            console.log("Refresh already in progress, queuing...");
            if (!window._refreshQueue) {
                window._refreshQueue = true;
                setTimeout(() => { 
                    window._refreshQueue = false;
                    refreshFileExplorer();
                }, 1200);
            }
            return;
        }

        window._refreshInProgress = true;

        // Crear un evento visual de actualización
        const explorerEl = document.getElementById('explorer-contents') || 
                          document.getElementById('explorer-container') ||
                          document.querySelector('.explorer-content');

        if (explorerEl) {
            const refreshIndicator = document.createElement('div');
            refreshIndicator.className = 'refresh-indicator';
            refreshIndicator.textContent = 'Sincronizando...';
            refreshIndicator.style.position = 'absolute';
            refreshIndicator.style.top = '5px';
            refreshIndicator.style.right = '10px';
            refreshIndicator.style.background = 'rgba(0,100,255,0.7)';
            refreshIndicator.style.color = 'white';
            refreshIndicator.style.padding = '3px 8px';
            refreshIndicator.style.borderRadius = '3px';
            refreshIndicator.style.fontSize = '12px';
            refreshIndicator.style.zIndex = '1000';

            if (explorerEl.style.position !== 'absolute' && 
                explorerEl.style.position !== 'relative') {
                explorerEl.style.position = 'relative';
            }

            explorerEl.appendChild(refreshIndicator);

            setTimeout(() => {
                try {
                    explorerEl.removeChild(refreshIndicator);
                } catch (e) {
                    console.log("Error removing refresh indicator", e);
                }
            }, 2000);
        }

        setTimeout(() => { window._refreshInProgress = false; }, 2000);

        // Try multiple approaches to refresh the file list

        // 1. If app object is available
        if (typeof app !== 'undefined' && app.updateFileExplorer) {
            console.log("Refreshing via app.updateFileExplorer()");
            app.updateFileExplorer();
        }

        // 2. If fileActions is available
        if (window.fileActions && typeof window.fileActions.refreshFileExplorer === 'function') {
            console.log("Refreshing via fileActions.refreshFileExplorer()");
            window.fileActions.refreshFileExplorer();
        }

        // 3. Try to refresh via DOM manipulation if certain elements exist
        const explorerContainer = document.getElementById('explorer-contents') || 
                                 document.getElementById('explorer-container') ||
                                 document.querySelector('.explorer-content');

        if (explorerContainer) {
            console.log("Refreshing via direct API call for explorer container");
            // Get current directory or default to root
            const currentDirectory = window.currentDirectory || '.';
            const userId = localStorage.getItem('user_id') || 'default';

            // Show loading indicator
            explorerContainer.innerHTML = '<div style="padding: 10px; text-align: center;">Cargando archivos...</div>';

            // Make direct API call to get files with cache-busting
            fetch(`/api/files?directory=${currentDirectory}&user_id=${userId}&_t=${Date.now()}`, {
                headers: { 'Cache-Control': 'no-cache' }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.files) {
                        console.log("Files loaded successfully:", data.files.length);
                        // If there's a rendering function available, use it
                        if (window.renderFileList) {
                            window.renderFileList(data.files, explorerContainer);
                        } else {
                            // Simple rendering if no custom renderer
                            renderBasicFileList(data.files, explorerContainer);
                        }
                    } else {
                        console.error("API response indicates failure:", data);
                        explorerContainer.innerHTML = '<div style="padding: 10px; color: red;">Error al cargar archivos</div>';
                    }
                })
                .catch(err => {
                    console.error("Error fetching files:", err);
                    explorerContainer.innerHTML = `<div style="padding: 10px; color: red;">Error: ${err.message}</div>`;
                })
                .finally(() => {
                    // Schedule another refresh after a delay to ensure we have the latest files
                    setTimeout(() => { 
                        window._refreshInProgress = false;
                        // Retry one more time to ensure we have the latest
                        fetch(`/api/files?directory=${currentDirectory}&user_id=${userId}&_t=${Date.now()}`, {
                            headers: { 'Cache-Control': 'no-cache' }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.files) {
                                console.log("Files refreshed again:", data.files.length);
                                if (window.renderFileList) {
                                    window.renderFileList(data.files, explorerContainer);
                                } else {
                                    renderBasicFileList(data.files, explorerContainer);
                                }
                            }
                        })
                        .catch(err => console.warn("Error on secondary refresh:", err));
                    }, 1500);
                });
        }

        // 4. Dispatch a custom event that other components can listen for
        document.dispatchEvent(new CustomEvent('file_explorer_update', { 
            detail: { timestamp: Date.now() } 
        }));
    }

    // Simple file list renderer
    function renderBasicFileList(files, container) {
        if (!container) return;

        // Clear existing content
        container.innerHTML = '';

        if (!files || files.length === 0) {
            container.innerHTML = '<div class="empty-folder">No files found</div>';
            return;
        }

        // Sort files: directories first, then files
        files.sort((a, b) => {
            if (a.type === 'directory' && b.type !== 'directory') return -1;
            if (a.type !== 'directory' && b.type === 'directory') return 1;
            return a.name.localeCompare(b.name);
        });

        // Create file list
        files.forEach(file => {
            const item = document.createElement('div');
            item.className = `file-item ${file.type}`;

            const icon = document.createElement('span');
            icon.className = 'icon';
            icon.innerHTML = file.type === 'directory' ? 
                             '<i class="bi bi-folder"></i>' : 
                             '<i class="bi bi-file-text"></i>';

            const name = document.createElement('span');
            name.className = 'file-name';
            name.textContent = file.name;

            item.appendChild(icon);
            item.appendChild(name);
            container.appendChild(item);

            // Add click handler
            item.addEventListener('click', () => {
                if (file.type === 'directory') {
                    // Navigate to directory
                    if (window.navigateToDirectory) {
                        window.navigateToDirectory(file.path);
                    }
                } else {
                    // Open file
                    if (window.openFile) {
                        window.openFile(file.path);
                    }
                }
            });
        });
    }

    // Function to notify parent window about file changes
    function notifyParentWindow(data) {
        try {
            if (window.parent && window.parent !== window) {
                console.log("Notifying parent window about file changes");

                // If parent has fileActions
                if (window.parent.fileActions && typeof window.parent.fileActions.refreshFileExplorer === 'function') {
                    window.parent.fileActions.refreshFileExplorer();
                }

                // If parent has updateFileExplorer
                if (window.parent.updateFileExplorer) {
                    window.parent.updateFileExplorer();
                }

                // If parent has refreshFileExplorer
                if (window.parent.refreshFileExplorer) {
                    window.parent.refreshFileExplorer();
                }

                // Try to update terminal file list if in terminal view
                if (window.parent.document.getElementById('explorer-contents')) {
                    const event = new CustomEvent('terminal_file_update', { 
                        detail: { 
                            type: data.type,
                            file: data.file,
                            timestamp: Date.now() 
                        } 
                    });
                    window.parent.document.dispatchEvent(event);
                }
            }
        } catch (e) {
            console.warn("Error notifying parent window:", e);
        }
    }

    // Update UI to show WebSocket connection status
    function updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) {
            if (connected) {
                statusIndicator.classList.remove('status-disconnected');
                statusIndicator.classList.add('status-connected');
                statusIndicator.title = 'Connected to server';
            } else {
                statusIndicator.classList.remove('status-connected');
                statusIndicator.classList.add('status-disconnected');
                statusIndicator.title = 'Disconnected from server';
            }
        }
    }

    // Display notification for file changes
    function notifyFileChange(type, file) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.classList.add('notification', 'fade-in');

        // Set notification content based on change type
        let message = '';
        switch(type) {
            case 'create':
                message = `Archivo creado: ${file.path}`;
                notification.classList.add('notification-success');
                break;
            case 'update':
                message = `Archivo actualizado: ${file.path}`;
                notification.classList.add('notification-info');
                break;
            case 'delete':
                message = `Archivo eliminado: ${file.path}`;
                notification.classList.add('notification-warning');
                break;
            default:
                message = `Cambio en archivo: ${file.path}`;
                notification.classList.add('notification-info');
        }

        notification.textContent = message;

        // Add notification to the document
        const notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            // Create notification container if it doesn't exist
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '1000';
            document.body.appendChild(container);
            container.appendChild(notification);
        } else {
            notificationContainer.appendChild(notification);
        }

        // Remove notification after delay
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }

    function notifyCommandExecution(data) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.classList.add('notification', 'fade-in', 'notification-info'); // Use info notification type
        notification.textContent = `Comando ejecutado: ${data.command}`;

        // Add notification to the document
        const notificationContainer = document.getElementById('notification-container');
        if (notificationContainer) {
            notificationContainer.appendChild(notification);
        }

        // Remove notification after delay
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }
});