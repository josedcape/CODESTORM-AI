document.addEventListener('DOMContentLoaded', function() {
    // Initialize app
    window.app = {
        currentDirectory: '/',
        commandHistory: [],
        historyIndex: -1,
        userId: null,
        workspace: null,

        // Function to add file action buttons - temporary fix for compatibility
        addFileActionButtons: function() {
            if (window.fileActions && typeof window.fileActions.addFileActionButtons === 'function') {
                window.fileActions.addFileActionButtons();
            }
        },

        // DOM elements
        elements: {
            instructionInput: document.getElementById('instruction-input'),
            executeBtn: document.getElementById('execute-btn'),
            commandDisplay: document.getElementById('command-display'),
            outputDisplay: document.getElementById('output-display'),
            fileExplorer: document.getElementById('file-explorer'),
            directoryPath: document.getElementById('directory-path'),
            statusIndicator: document.getElementById('status-indicator'),
            clearBtn: document.getElementById('clear-btn'),
            refreshBtn: document.getElementById('refresh-btn'),
            previousBtn: document.getElementById('previous-btn'),
            nextBtn: document.getElementById('next-btn'),
            workspaceInfo: document.getElementById('workspace-info')
        },

        init: function() {
            this.initSession();
            this.bindEvents();
            this.checkServerStatus();
        },

        initSession: function() {
            // Get session info or initialize a new one
            fetch('/api/session')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    this.userId = data.user_id;
                    this.workspace = data.workspace;

                    if (this.elements.workspaceInfo) {
                        this.elements.workspaceInfo.textContent = `Workspace: ${this.workspace}`;
                    }

                    // Update file explorer after session initialization
                    this.updateFileExplorer();
                })
                .catch(error => {
                    console.error('Error initializing session:', error);
                    // Continue with default values if the session API fails
                    this.userId = 'default';
                    this.workspace = 'default';

                    // Still update the file explorer after setting defaults
                    this.updateFileExplorer();
                });
        },

        bindEvents: function() {
            // Execute button
            if (this.elements.executeBtn) {
                this.elements.executeBtn.addEventListener('click', () => this.processInstruction());
            }

            // Clear button
            if (this.elements.clearBtn) {
                this.elements.clearBtn.addEventListener('click', () => this.clearTerminal());
            }

            // Refresh button
            if (this.elements.refreshBtn) {
                this.elements.refreshBtn.addEventListener('click', () => this.updateFileExplorer());
            }

            // Command history navigation
            if (this.elements.previousBtn) {
                this.elements.previousBtn.addEventListener('click', () => this.navigateHistory(-1));
            }
            if (this.elements.nextBtn) {
                this.elements.nextBtn.addEventListener('click', () => this.navigateHistory(1));
            }

            // Enter key in textarea
            if (this.elements.instructionInput) {
                this.elements.instructionInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        this.processInstruction();
                    }
                });
            }
        },

        checkServerStatus: function() {
            fetch('/api/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => {
                if (response.ok) {
                    this.elements.statusIndicator.classList.remove('status-disconnected');
                    this.elements.statusIndicator.classList.add('status-connected');
                    this.elements.statusIndicator.title = 'Connected to server';
                } else {
                    throw new Error('Server error');
                }
            })
            .catch(error => {
                this.elements.statusIndicator.classList.remove('status-connected');
                this.elements.statusIndicator.classList.add('status-disconnected');
                this.elements.statusIndicator.title = 'Disconnected from server';
                console.error('Server status check failed:', error);
            });
        },

        processInstruction: function() {
            const instruction = this.elements.instructionInput.value.trim();
            if (!instruction) return;

            // Add loading indicator
            this.elements.executeBtn.classList.add('loading');

            // Save to history
            this.commandHistory.push(instruction);
            this.historyIndex = this.commandHistory.length;

            // Cache for common responses (improves speed)
            const cachedCommands = {
                'hola': "echo '¡Hola! ¿En qué puedo ayudarte hoy?'",
                'mostrar archivos': 'ls -la',
                'listar': 'ls -la',
                'archivos': 'ls -la',
                'fecha': 'date',
                'hora': 'date +%H:%M:%S',
                'ayuda': "echo 'Puedo convertir tus instrucciones en comandos de terminal'"
            };

            // Try using local cache first before calling the server
            const lowerInstruction = instruction.toLowerCase();
            for (const [key, cmd] of Object.entries(cachedCommands)) {
                if (lowerInstruction.includes(key)) {
                    // Show the generated command
                    this.elements.commandDisplay.textContent = cmd;

                    // Execute directly without calling the server
                    this.executeCommandDirectly(cmd, instruction);
                    return; // End the function here if a match is found
                }
            }

            // Get the selected model (default to OpenAI)
            const modelSelect = document.getElementById('model-select');
            const selectedModel = modelSelect ? modelSelect.value : 'openai';

            // Show progress indicator
            this.elements.executeBtn.disabled = true;
            this.elements.executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';

            // Process the instruction through the Flask backend
            fetch('/api/process_natural', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: instruction,
                    instruction: instruction,
                    model: selectedModel,
                    user_id: this.userId || 'default'
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.displayError(data.error);
                    return null;
                }

                const command = data.command;
                this.elements.commandDisplay.textContent = command;

                // Show a success message
                if (window.fileActions && typeof window.fileActions.showNotification === 'function') {
                    window.fileActions.showNotification('Command generated successfully', 'success');
                }

                // Execute the command
                return fetch('/api/execute_command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        command: command,
                        instruction: instruction,
                        model: selectedModel
                    })
                });
            })
            .then(response => {
                if (!response || !response.ok) {
                    throw new Error(`Server error: ${response ? response.status + ' ' + response.statusText : 'No response'}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;

                if (data.error) {
                    this.displayError(data.error);
                    return;
                }

                // Display command output
                let output = '';
                if (data.stdout) output += data.stdout;
                if (data.stderr) output += '\n' + data.stderr;

                this.elements.outputDisplay.textContent = output;

                // Update file explorer after command execution
                this.updateFileExplorer();
            })
            .catch(error => {
                console.error('Error:', error);
                this.displayError('Failed to process instruction: ' + error.message);
            })
            .finally(() => {
                // Remove loading indicator
                this.elements.executeBtn.disabled = false;
                this.elements.executeBtn.innerHTML = 'Execute';
            });
        },

        displayError: function(errorMessage) {
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('alert', 'alert-danger', 'mt-2');
            errorDiv.textContent = errorMessage;

            this.elements.outputDisplay.textContent = '';
            this.elements.outputDisplay.appendChild(errorDiv);
        },

        clearTerminal: function() {
            this.elements.commandDisplay.textContent = '';
            this.elements.outputDisplay.textContent = '';
            this.elements.instructionInput.value = '';
        },

        updateFileExplorer: function() {
            // Sanitize current directory
            let directory = this.currentDirectory;

            // Make sure directory is not undefined and has a value
            if (!directory || directory === undefined) {
                directory = '/';
                this.currentDirectory = '/';
            }

            // Check if fileExplorer element exists
            if (!this.elements.fileExplorer) {
                console.error('File explorer element not found');
                return;
            }

            // Display loading indicator
            this.elements.fileExplorer.innerHTML = '<div class="loading-spinner"></div>';

            fetch(`/api/files?directory=${encodeURIComponent(directory)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.displayFileExplorerError(data.error);
                    return;
                }

                // Update current directory display
                if (data.directory) {
                    this.currentDirectory = data.directory;
                }

                this.elements.directoryPath.textContent = this.currentDirectory;
                this.renderFileExplorer(data.files || []);

                // Add Create File and Create Folder buttons if available
                if (window.fileActions && typeof window.fileActions.addFileActionButtons === 'function') {
                    window.fileActions.addFileActionButtons();
                }
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                this.displayFileExplorerError('Failed to fetch files: ' + error.message);
            });
        },

        renderFileExplorer: function(files) {
            const fileExplorer = this.elements.fileExplorer;
            fileExplorer.innerHTML = '';

            // Add parent directory navigation if not in root
            if (this.currentDirectory !== '/') {
                const parentItem = this.createFileItem('..', 'directory');
                parentItem.addEventListener('click', () => {
                    this.navigateToDirectory('..');
                });
                fileExplorer.appendChild(parentItem);
            }

            // Sort files - directories first, then alphabetically
            files.sort((a, b) => {
                if (a.type !== b.type) {
                    return a.type === 'directory' ? -1 : 1;
                }
                return a.name.localeCompare(b.name);
            });

            // Add file items
            files.forEach(file => {
                if (file.name === '.' || file.name === '..') return;

                const fileItem = this.createFileItem(file.name, file.type);

                // Add click handler
                fileItem.addEventListener('click', () => {
                    if (file.type === 'directory') {
                        this.navigateToDirectory(file.name);
                    } else {
                        // Open file in editor
                        const filePath = this.currentDirectory === '/'
                            ? file.name
                            : `${this.currentDirectory.replace(/^\//, '')}/${file.name}`;
                        window.location.href = `/edit/${filePath}`;
                    }
                });

                fileExplorer.appendChild(fileItem);
            });
        },

        createFileItem: function(name, type) {
            const item = document.createElement('div');
            item.classList.add('file-item', 'd-flex', 'align-items-center');

            const icon = document.createElement('i');
            icon.classList.add('file-icon');

            if (type === 'directory') {
                icon.classList.add('bi', 'bi-folder-fill');
                item.classList.add('directory');
            } else {
                icon.classList.add('bi', 'bi-file-text');
                item.classList.add('file');
            }

            const nameSpan = document.createElement('span');
            nameSpan.textContent = name;

            item.appendChild(icon);
            item.appendChild(nameSpan);

            return item;
        },

        navigateToDirectory: function(dirName) {
            let newPath;

            if (dirName === '..') {
                // Navigate to parent directory
                const parts = this.currentDirectory.split('/').filter(p => p);
                parts.pop();
                newPath = parts.length ? '/' + parts.join('/') : '/';
            } else if (dirName.startsWith('/')) {
                // Absolute path
                newPath = dirName;
            } else {
                // Relative path
                newPath = this.currentDirectory === '/'
                    ? '/' + dirName
                    : `${this.currentDirectory}/${dirName}`;
            }

            // Normalize path for consistency
            if (!newPath.startsWith('/')) {
                newPath = '/' + newPath;
            }

            // Remove any double slashes
            newPath = newPath.replace(/\/\//g, '/');

            this.currentDirectory = newPath;
            this.updateFileExplorer();
        },

        displayFileExplorerError: function(errorMessage) {
            this.elements.fileExplorer.innerHTML = '';

            const errorDiv = document.createElement('div');
            errorDiv.classList.add('alert', 'alert-danger');
            errorDiv.textContent = errorMessage;

            this.elements.fileExplorer.appendChild(errorDiv);
        },

        createNewFile: function() {
            const fileName = prompt('File name:');
            if (!fileName || fileName.trim() === '') return;

            const path = this.currentDirectory === '/'
                ? fileName
                : `${this.currentDirectory.replace(/^\//, '')}/${fileName}`;

            fetch('/api/files/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: path,
                    content: ''
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.displayFileExplorerError(data.error);
                    return;
                }

                // Redirect to edit the new file
                window.location.href = `/edit/${path}`;
            })
            .catch(error => {
                console.error('Error creating file:', error);
                this.displayFileExplorerError('Error creating file: ' + error.message);
            });
        },

        createNewFolder: function() {
            const folderName = prompt('Folder name:');
            if (!folderName || folderName.trim() === '') return;

            const path = this.currentDirectory === '/'
                ? folderName
                : `${this.currentDirectory.replace(/^\//, '')}/${folderName}`;

            fetch('/api/files/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: path,
                    is_directory: true
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.displayFileExplorerError(data.error);
                    return;
                }

                // Refresh file explorer
                this.updateFileExplorer();
            })
            .catch(error => {
                console.error('Error creating folder:', error);
                this.displayFileExplorerError('Error creating folder: ' + error.message);
            });
        },

        // Function to execute commands directly from cache
        executeCommandDirectly: function(command, instruction) {
            // Show loading indicator
            this.elements.executeBtn.disabled = true;
            this.elements.executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';

            // Execute the command directly (from cache)
            fetch('/api/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    instruction: instruction,
                    model: 'cache' // Indicate using local cache
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.displayError(data.error);
                    return;
                }

                // Display command output
                let output = '';
                if (data.stdout) output += data.stdout;
                if (data.stderr) output += '\n' + data.stderr;

                this.elements.outputDisplay.textContent = output;

                // Update file explorer
                this.updateFileExplorer();

                // Notify success
                if (window.fileActions && typeof window.fileActions.showNotification === 'function') {
                    window.fileActions.showNotification('Command executed successfully', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.displayError('Error executing command: ' + error.message);
            })
            .finally(() => {
                // Remove loading indicator
                this.elements.executeBtn.disabled = false;
                this.elements.executeBtn.innerHTML = 'Execute';
            });
        },

        navigateHistory: function(direction) {
            if (this.commandHistory.length === 0) return;

            this.historyIndex += direction;

            // Ensure index stays within bounds
            if (this.historyIndex < 0) this.historyIndex = 0;
            if (this.historyIndex >= this.commandHistory.length) {
                this.historyIndex = this.commandHistory.length - 1;
            }

            // Set the input value to the command at the current index
            this.elements.instructionInput.value = this.commandHistory[this.historyIndex];
        }
    };

    // Initialize the app
    app.init();
});


// Función para verificar disponibilidad de APIs
function checkAPIAvailability() {
    fetch('/api/health')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la verificación de salud del API');
            }
            return response.json();
        })
        .then(data => {
            // Actualizar el estado global de APIs
            if (window.app && window.app.apiStatus) {
                const apis = data.apis || {};
                window.app.apiStatus.openai = apis.openai === 'ok';
                window.app.apiStatus.anthropic = apis.anthropic === 'ok';
                window.app.apiStatus.gemini = apis.gemini === 'ok';
                window.app.apiStatus.lastChecked = new Date().toISOString();
                window.app.apiStatus.availableModels = data.available_models || [];
            }
            
            // Actualizar la interfaz de usuario
            const apiStatus = document.getElementById('api-status');
            if (apiStatus) {
                const apis = data.apis || {};
                const availableApis = Object.entries(apis)
                    .filter(([_, status]) => status === 'ok')
                    .map(([name, _]) => name);
                
                if (availableApis.length > 0) {
                    apiStatus.innerHTML = '<span class="status-success"><i class="bi bi-check-circle"></i> APIs disponibles:</span> ' + availableApis.join(', ');
                    apiStatus.className = 'mt-2 small text-success';
                } else {
                    apiStatus.innerHTML = '<span class="status-warning"><i class="bi bi-exclamation-triangle"></i> No hay APIs configuradas.</span> Configura al menos una en el panel de Secrets.';
                    apiStatus.className = 'mt-2 small text-warning';
                }
                
                // Actualizar selectores de modelos en todas las páginas
                document.querySelectorAll('.model-selector, #model-selector, [data-role="model-selector"]').forEach(modelSelector => {
                    if (modelSelector) {
                        // Resetear opciones primero
                        Array.from(modelSelector.options).forEach(option => {
                            // Eliminar texto de "no configurado" si existe
                            option.textContent = option.textContent.replace(' (no configurado)', '');
                            option.disabled = false;
                        });
                        
                        // Deshabilitar opciones no disponibles
                        Array.from(modelSelector.options).forEach(option => {
                            const isAvailable = apis[option.value] === 'ok';
                            option.disabled = !isAvailable;
                            if (!isAvailable) {
                                option.textContent += ' (no configurado)';
                            }
                        });
                    });
                    
                    // Seleccionar el primer modelo disponible
                    const firstAvailable = Array.from(modelSelector.options)
                        .find(option => !option.disabled);
                    if (firstAvailable) {
                        firstAvailable.selected = true;
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error checking API availability:', error);
            const apiStatus = document.getElementById('api-status');
            if (apiStatus) {
                apiStatus.textContent = 'Error al verificar disponibilidad de APIs';
                apiStatus.className = 'mt-2 small text-danger';
            }
        });
}

// Llamar a la función cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar la aplicación
    if (window.app && typeof window.app.init === 'function') {
        window.app.init();
    }
    
    // Verificar disponibilidad de APIs
    checkAPIAvailability();
});
/**
 * Constructor de Aplicaciones - Archivo base generado
 * Este archivo contiene la funcionalidad principal para la aplicación
 */

// Objeto principal de la aplicación
const app = {
  // Configuración
  config: {
    apiUrl: '/api',
    debug: true,
    autoInit: true
  },
  
  // Estado de la aplicación
  state: {
    initialized: false,
    loading: false,
    error: null,
    data: null
  },
  
  // Inicialización
  init: function() {
    if (this.config.debug) {
      console.log('Inicializando aplicación...');
    }
    
    this.setupEventListeners();
    this.checkDependencies();
    
    this.state.initialized = true;
    
    if (this.config.debug) {
      console.log('Aplicación inicializada correctamente');
    }
    
    return this;
  },
  
  // Configurar escuchadores de eventos
  setupEventListeners: function() {
    document.addEventListener('DOMContentLoaded', this.onDocumentReady.bind(this));
    window.addEventListener('error', this.handleError.bind(this));
  },
  
  // Verificar dependencias necesarias
  checkDependencies: function() {
    // Aquí se pueden verificar bibliotecas externas o APIs
    return true;
  },
  
  // Evento cuando el documento está listo
  onDocumentReady: function() {
    if (this.config.debug) {
      console.log('Documento listo');
    }
    
    // Iniciar carga de datos si es necesario
    if (this.config.autoInit) {
      this.loadInitialData();
    }
  },
  
  // Cargar datos iniciales
  loadInitialData: function() {
    this.state.loading = true;
    
    // Simular carga de datos (reemplazar con llamada real a API)
    setTimeout(() => {
      this.state.data = {
        name: 'Aplicación generada',
        version: '1.0.0',
        timestamp: new Date().toISOString()
      };
      
      this.state.loading = false;
      this.onDataLoaded();
    }, 1000);
  },
  
  // Callback cuando los datos están cargados
  onDataLoaded: function() {
    if (this.config.debug) {
      console.log('Datos cargados:', this.state.data);
    }
    
    // Actualizar UI o ejecutar lógica adicional
    this.updateUI();
  },
  
  // Actualizar interfaz de usuario
  updateUI: function() {
    // Buscar elementos para actualizar
    const appContainer = document.getElementById('app');
    if (appContainer && this.state.data) {
      appContainer.innerHTML = `
        <div class="app-info">
          <h2>${this.state.data.name}</h2>
          <p>Versión: ${this.state.data.version}</p>
          <p>Generado: ${new Date(this.state.data.timestamp).toLocaleString()}</p>
        </div>
      `;
    }
  },
  
  // Manejar errores
  handleError: function(error) {
    this.state.error = error;
    
    if (this.config.debug) {
      console.error('Error en la aplicación:', error);
    }
    
    // Mostrar mensaje de error en UI
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
      errorContainer.innerHTML = `
        <div class="error-message">
          <h3>Error</h3>
          <p>${error.message || 'Error desconocido'}</p>
        </div>
      `;
      errorContainer.style.display = 'block';
    }
  }
};

// Iniciar la aplicación cuando se carga el script
if (app.config.autoInit) {
  app.init();
}

// Exportar el objeto app para uso externo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = app;
} else {
  window.app = app;
}
