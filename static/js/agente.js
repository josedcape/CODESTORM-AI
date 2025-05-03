
/**
 * agente.js - Funcionalidades JavaScript específicas para la página de agente
 * Proporciona integración con las APIs del sistema y funcionalidades de interfaz
 */

// Namespace para las funcionalidades del agente
const agenteApp = (function() {
    // Configuración inicial
    const config = {
        apiBase: '/api',
        endpoints: {
            chat: '/api/chat',
            fileOperations: '/api/file',
            agentSelector: '/api/agents',
            codeGeneration: '/api/code/generate'
        },
        defaultModel: 'openai'
    };

    // Estado de la aplicación
    let state = {
        activeAgent: 'developer',
        activeModel: 'openai',
        interventionMode: true,
        isProcessing: false
    };

    // Cache para resultados y conversaciones
    const cache = {
        conversations: [],
        generatedFiles: []
    };

    // Referencias a elementos DOM
    let elements = {};

    /**
     * Inicializa la aplicación
     */
    function initialize() {
        // Capturar referencias a elementos DOM
        cacheElements();
        
        // Configurar controladores de eventos
        setupEventListeners();
        
        // Verificar estado de disponibilidad de APIs
        checkAPIAvailability();
        
        console.log('Agente: Inicialización completada');
    }

    /**
     * Guarda referencias a los elementos del DOM
     */
    function cacheElements() {
        elements = {
            chatInput: document.getElementById('assistant-chat-input'),
            sendButton: document.getElementById('send-assistant-message'),
            messagesContainer: document.getElementById('assistant-chat-messages'),
            agentSelector: document.getElementById('agent-selector'),
            modelSelector: document.getElementById('model-selector'),
            interventionToggle: document.getElementById('intervention-mode'),
            chatPanel: document.getElementById('assistant-chat-panel'),
            toggleButton: document.getElementById('toggle-assistant-chat')
        };
    }

    /**
     * Configura los controladores de eventos
     */
    function setupEventListeners() {
        // Solo configurar eventos si los elementos existen
        if (elements.sendButton) {
            elements.sendButton.addEventListener('click', handleSendMessage);
        }
        
        if (elements.chatInput) {
            elements.chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                }
            });
        }

        // Controladores para cambio de agente y modelo
        if (elements.agentSelector) {
            elements.agentSelector.addEventListener('change', function(e) {
                state.activeAgent = e.target.value;
                console.log(`Agente cambiado a: ${state.activeAgent}`);
            });
        }

        if (elements.modelSelector) {
            elements.modelSelector.addEventListener('change', function(e) {
                state.activeModel = e.target.value;
                console.log(`Modelo cambiado a: ${state.activeModel}`);
            });
        }

        if (elements.interventionToggle) {
            elements.interventionToggle.addEventListener('change', function(e) {
                state.interventionMode = e.target.checked;
                console.log(`Modo intervención: ${state.interventionMode ? 'activado' : 'desactivado'}`);
            });
        }

        // Controladores para abrir/cerrar panel
        if (elements.toggleButton) {
            elements.toggleButton.addEventListener('click', toggleChatPanel);
        }

        // Evento global para manejo de errores
        window.addEventListener('error', function(e) {
            console.error('Error global capturado:', e.message);
        });
    }

    /**
     * Verifica la disponibilidad de APIs
     */
    function checkAPIAvailability() {
        fetch(`${config.apiBase}/status`)
            .then(response => response.json())
            .then(data => {
                console.log('Estado API:', data);
                addSystemMessage(`<i class="bi bi-check-circle-fill text-success"></i> Servidor conectado: ${data.status || 'OK'}`);
                
                // Verificar modelos disponibles
                if (data.available_models) {
                    updateAvailableModels(data.available_models);
                }
            })
            .catch(error => {
                console.error('Error verificando API:', error);
                addSystemMessage(`<i class="bi bi-exclamation-triangle-fill text-warning"></i> Error conectando con el servidor: ${error.message}`);
            });
    }

    /**
     * Actualiza los modelos disponibles en el selector
     */
    function updateAvailableModels(models) {
        if (!elements.modelSelector || !models) return;
        
        // Limpiar opciones actuales
        elements.modelSelector.innerHTML = '';
        
        // Agregar nuevas opciones
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            option.disabled = !model.available;
            if (!model.available) {
                option.setAttribute('title', 'API key no configurada');
            }
            elements.modelSelector.appendChild(option);
        });
        
        // Seleccionar el primer modelo disponible
        const availableModel = models.find(m => m.available);
        if (availableModel) {
            elements.modelSelector.value = availableModel.id;
            state.activeModel = availableModel.id;
        }
    }

    /**
     * Maneja el envío de mensajes
     */
    function handleSendMessage() {
        if (!elements.chatInput) return;
        
        const message = elements.chatInput.value.trim();
        if (!message || state.isProcessing) return;

        // Agregar mensaje del usuario
        addUserMessage(message);
        
        // Limpiar input
        elements.chatInput.value = '';
        
        // Mostrar indicador de escritura
        showTypingIndicator();
        
        // Marcar como procesando
        state.isProcessing = true;
        
        // Enviar mensaje al servidor
        sendMessageToAPI(message);
    }

    /**
     * Envía mensaje a la API
     */
    function sendMessageToAPI(message) {
        fetch(config.endpoints.chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                agent_id: state.activeAgent,
                model: state.activeModel,
                intervention_mode: state.interventionMode
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Ocultar indicador de escritura
            hideTypingIndicator();
            
            // Agregar respuesta del asistente
            addAssistantMessage(data.response || data.message || 'No se pudo obtener una respuesta.');
            
            // Almacenar en caché
            cache.conversations.push({
                user: message,
                assistant: data.response || data.message,
                timestamp: new Date().toISOString()
            });
            
            // Verificar si hay acciones para realizar
            if (data.actions && data.actions.length > 0) {
                processActions(data.actions);
            }
            
            // Marcar como no procesando
            state.isProcessing = false;
        })
        .catch(error => {
            console.error('Error enviando mensaje:', error);
            hideTypingIndicator();
            
            // Mostrar error
            addSystemMessage(`<i class="bi bi-exclamation-triangle-fill text-warning"></i> <strong>Error:</strong> ${error.message}`);
            
            // Marcar como no procesando
            state.isProcessing = false;
        });
    }

    /**
     * Procesa acciones devueltas por la API
     */
    function processActions(actions) {
        actions.forEach(action => {
            switch (action.type) {
                case 'file_create':
                    addSystemMessage(`<i class="bi bi-file-earmark-plus"></i> Archivo creado: <code>${action.path}</code>`);
                    cache.generatedFiles.push(action.path);
                    break;
                    
                case 'file_modify':
                    addSystemMessage(`<i class="bi bi-file-earmark-text"></i> Archivo modificado: <code>${action.path}</code>`);
                    break;
                    
                case 'command_execute':
                    addSystemMessage(`<i class="bi bi-terminal"></i> Comando ejecutado: <code>${action.command}</code>`);
                    if (action.output) {
                        addSystemMessage(`<div class="command-output"><pre>${action.output}</pre></div>`);
                    }
                    break;
                    
                case 'api_call':
                    addSystemMessage(`<i class="bi bi-hdd-network"></i> API llamada: <code>${action.endpoint}</code>`);
                    break;
                    
                default:
                    console.log('Acción desconocida:', action);
            }
        });
    }

    /**
     * Agrega un mensaje del usuario al chat
     */
    function addUserMessage(message) {
        if (!elements.messagesContainer) return;
        
        const messageId = 'msg-' + Date.now();
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.id = messageId;
        userMsg.textContent = message;
        
        elements.messagesContainer.appendChild(userMsg);
        scrollToBottom();
    }

    /**
     * Agrega un mensaje del asistente al chat
     */
    function addAssistantMessage(messageHtml) {
        if (!elements.messagesContainer) return;
        
        const messageId = 'msg-' + Date.now();
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'message assistant-message';
        assistantMsg.id = messageId;
        assistantMsg.innerHTML = messageHtml;
        
        // Agregar botones de acción
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'message-actions-extended';
        actionsContainer.innerHTML = `
            <button class="apply-code-btn" onclick="agenteApp.applyCode('${messageId}')">
                <i class="bi bi-code-square"></i> Aplicar código
            </button>
            <button class="explore-files-btn" onclick="agenteApp.exploreRelatedFiles('${messageId}')">
                <i class="bi bi-folder2-open"></i> Explorar archivos
            </button>
            <button class="contextualize-btn" onclick="agenteApp.contextualizeCode('${messageId}')">
                <i class="bi bi-braces"></i> Contextualizar
            </button>
        `;
        
        assistantMsg.appendChild(actionsContainer);
        elements.messagesContainer.appendChild(assistantMsg);
        
        // Aplicar highlight.js a los bloques de código si está disponible
        if (window.hljs) {
            assistantMsg.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
        
        scrollToBottom();
    }

    /**
     * Agrega un mensaje del sistema al chat
     */
    function addSystemMessage(messageHtml) {
        if (!elements.messagesContainer) return;
        
        const systemMsg = document.createElement('div');
        systemMsg.className = 'system-message';
        systemMsg.innerHTML = messageHtml;
        
        elements.messagesContainer.appendChild(systemMsg);
        scrollToBottom();
    }

    /**
     * Muestra el indicador de escritura
     */
    function showTypingIndicator() {
        if (!elements.messagesContainer) return;
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const bubble = document.createElement('div');
            bubble.className = 'typing-bubble';
            typingIndicator.appendChild(bubble);
        }
        
        elements.messagesContainer.appendChild(typingIndicator);
        scrollToBottom();
    }

    /**
     * Oculta el indicador de escritura
     */
    function hideTypingIndicator() {
        if (!elements.messagesContainer) return;
        
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Hace scroll hasta el final del contenedor de mensajes
     */
    function scrollToBottom() {
        if (elements.messagesContainer) {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }
    }

    /**
     * Muestra/oculta el panel de chat
     */
    function toggleChatPanel() {
        if (elements.chatPanel) {
            const isVisible = elements.chatPanel.style.display !== 'none' && elements.chatPanel.style.display !== '';
            elements.chatPanel.style.display = isVisible ? 'none' : 'flex';
            
            // Enfocar el input cuando se abre
            if (!isVisible && elements.chatInput) {
                elements.chatInput.focus();
            }
        }
    }

    /**
     * Aplica código de un mensaje al proyecto
     */
    function applyCode(messageId) {
        const message = document.getElementById(messageId);
        if (!message) return;
        
        // Buscar bloques de código
        const codeBlocks = message.querySelectorAll('pre code');
        if (codeBlocks.length === 0) {
            addSystemMessage('<i class="bi bi-exclamation-circle"></i> No se encontró código para aplicar');
            return;
        }
        
        // Si hay más de un bloque, mostrar selector
        if (codeBlocks.length > 1) {
            showCodeSelectionDialog(messageId, codeBlocks);
            return;
        }
        
        // Si solo hay un bloque, aplicar directamente
        const codeContent = codeBlocks[0].textContent;
        const language = codeBlocks[0].className.replace('language-', '');
        
        showFileSelectionDialog(codeContent, language);
    }

    /**
     * Muestra un diálogo para seleccionar qué bloque de código aplicar
     */
    function showCodeSelectionDialog(messageId, codeBlocks) {
        // Crear el modal de selección
        const modal = document.createElement('div');
        modal.className = 'code-selection-modal';
        modal.id = 'code-selection-modal';
        modal.innerHTML = `
            <div class="code-selection-dialog">
                <h3>Seleccionar código para aplicar</h3>
                <div class="code-blocks-list">
                    ${Array.from(codeBlocks).map((block, index) => {
                        const language = block.className.replace('language-', '');
                        const preview = block.textContent.substring(0, 100) + (block.textContent.length > 100 ? '...' : '');
                        return `
                            <div class="code-block-option" data-index="${index}">
                                <div class="code-block-header">
                                    <span class="code-language-badge">${language}</span>
                                    <button class="select-code-btn" onclick="agenteApp.selectCodeBlock('${messageId}', ${index})">Seleccionar</button>
                                </div>
                                <pre><code>${preview}</code></pre>
                            </div>
                        `;
                    }).join('')}
                </div>
                <div class="dialog-actions">
                    <button onclick="agenteApp.closeCodeSelectionDialog()">Cancelar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * Selecciona un bloque de código específico
     */
    function selectCodeBlock(messageId, blockIndex) {
        const message = document.getElementById(messageId);
        if (!message) return;
        
        const codeBlocks = message.querySelectorAll('pre code');
        if (blockIndex >= 0 && blockIndex < codeBlocks.length) {
            const codeContent = codeBlocks[blockIndex].textContent;
            const language = codeBlocks[blockIndex].className.replace('language-', '');
            
            closeCodeSelectionDialog();
            showFileSelectionDialog(codeContent, language);
        }
    }

    /**
     * Cierra el diálogo de selección de código
     */
    function closeCodeSelectionDialog() {
        const modal = document.getElementById('code-selection-modal');
        if (modal) {
            document.body.removeChild(modal);
        }
    }

    /**
     * Muestra un diálogo para seleccionar o crear el archivo donde aplicar el código
     */
    function showFileSelectionDialog(codeContent, language) {
        // Sugerir extensión de archivo basada en el lenguaje
        let fileExtension = '.txt';
        
        switch (language) {
            case 'javascript':
            case 'js':
                fileExtension = '.js';
                break;
            case 'typescript':
            case 'ts':
                fileExtension = '.ts';
                break;
            case 'python':
            case 'py':
                fileExtension = '.py';
                break;
            case 'html':
                fileExtension = '.html';
                break;
            case 'css':
                fileExtension = '.css';
                break;
            case 'json':
                fileExtension = '.json';
                break;
        }
        
        // Crear el modal de selección de archivo
        const modal = document.createElement('div');
        modal.className = 'file-selection-modal';
        modal.id = 'file-selection-modal';
        modal.innerHTML = `
            <div class="file-selection-dialog">
                <h3>Aplicar código a archivo</h3>
                
                <div class="file-selection-tabs">
                    <button id="new-file-tab" class="file-tab active" onclick="agenteApp.switchFileTab('new')">Nuevo archivo</button>
                    <button id="existing-file-tab" class="file-tab" onclick="agenteApp.switchFileTab('existing')">Archivo existente</button>
                </div>
                
                <div id="new-file-panel" class="file-panel">
                    <div class="form-group">
                        <label for="new-file-name">Nombre de archivo:</label>
                        <input type="text" id="new-file-name" placeholder="nombre_archivo${fileExtension}" value="nuevo_archivo${fileExtension}">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="create-folder" onchange="agenteApp.toggleFolderInput()">
                            Crear en una nueva carpeta
                        </label>
                    </div>
                    <div class="form-group" id="folder-input" style="display: none;">
                        <label for="folder-name">Nombre de carpeta:</label>
                        <input type="text" id="folder-name" placeholder="nombre_carpeta">
                    </div>
                </div>
                
                <div id="existing-file-panel" class="file-panel" style="display: none;">
                    <div class="form-group">
                        <label for="existing-file-path">Ruta del archivo:</label>
                        <input type="text" id="existing-file-path" placeholder="ruta/al/archivo${fileExtension}">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="radio" name="replace-mode" value="replace" checked>
                            Reemplazar contenido completo
                        </label>
                        <label>
                            <input type="radio" name="replace-mode" value="append">
                            Añadir al final del archivo
                        </label>
                    </div>
                </div>
                
                <div class="code-preview">
                    <h4>Vista previa del código</h4>
                    <pre><code class="language-${language}">${codeContent}</code></pre>
                </div>
                
                <div class="dialog-actions">
                    <button onclick="agenteApp.applyCodeToFile('${encodeURIComponent(codeContent)}', '${language}')">Aplicar</button>
                    <button onclick="agenteApp.closeFileSelectionDialog()">Cancelar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Aplicar highlight.js a la vista previa si está disponible
        if (window.hljs) {
            document.querySelectorAll('.code-preview pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }

    /**
     * Cambia entre las pestañas de nuevo archivo y archivo existente
     */
    function switchFileTab(tab) {
        const newFileTab = document.getElementById('new-file-tab');
        const existingFileTab = document.getElementById('existing-file-tab');
        const newFilePanel = document.getElementById('new-file-panel');
        const existingFilePanel = document.getElementById('existing-file-panel');
        
        if (tab === 'new') {
            newFileTab.classList.add('active');
            existingFileTab.classList.remove('active');
            newFilePanel.style.display = 'block';
            existingFilePanel.style.display = 'none';
        } else {
            newFileTab.classList.remove('active');
            existingFileTab.classList.add('active');
            newFilePanel.style.display = 'none';
            existingFilePanel.style.display = 'block';
        }
    }

    /**
     * Muestra/oculta el campo de entrada de carpeta
     */
    function toggleFolderInput() {
        const folderInput = document.getElementById('folder-input');
        const createFolder = document.getElementById('create-folder');
        
        if (folderInput && createFolder) {
            folderInput.style.display = createFolder.checked ? 'block' : 'none';
        }
    }

    /**
     * Cierra el diálogo de selección de archivo
     */
    function closeFileSelectionDialog() {
        const modal = document.getElementById('file-selection-modal');
        if (modal) {
            document.body.removeChild(modal);
        }
    }

    /**
     * Aplica el código al archivo especificado
     */
    function applyCodeToFile(encodedCodeContent, language) {
        const codeContent = decodeURIComponent(encodedCodeContent);
        const newFileTab = document.getElementById('new-file-tab');
        
        // Determinar modo (nuevo archivo o existente)
        const isNewFile = newFileTab.classList.contains('active');
        
        let filePath = '';
        let mode = 'replace';
        
        if (isNewFile) {
            const fileName = document.getElementById('new-file-name').value.trim();
            if (!fileName) {
                showNotification('Debes especificar un nombre de archivo', 'error');
                return;
            }
            
            // Verificar si se creará en una carpeta
            if (document.getElementById('create-folder').checked) {
                const folderName = document.getElementById('folder-name').value.trim();
                if (!folderName) {
                    showNotification('Debes especificar un nombre de carpeta', 'error');
                    return;
                }
                filePath = `${folderName}/${fileName}`;
            } else {
                filePath = fileName;
            }
            
            mode = 'create';
        } else {
            filePath = document.getElementById('existing-file-path').value.trim();
            if (!filePath) {
                showNotification('Debes especificar la ruta del archivo', 'error');
                return;
            }
            
            // Obtener modo de reemplazo
            const replaceMode = document.querySelector('input[name="replace-mode"]:checked').value;
            mode = replaceMode;
        }
        
        // Enviar solicitud al servidor
        fetch(config.endpoints.fileOperations + '/write', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                content: codeContent,
                mode: mode,
                language: language
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification(`Código aplicado a ${filePath}`, 'success');
                closeFileSelectionDialog();
                
                // Añadir mensaje del sistema informando de la acción
                addSystemMessage(`Se ha ${mode === 'create' ? 'creado' : (mode === 'append' ? 'actualizado' : 'reemplazado')} el archivo <code>${filePath}</code> con el código aplicado.`);
                
                // Agregar a la lista de archivos generados
                if (mode === 'create') {
                    cache.generatedFiles.push(filePath);
                }
            } else {
                showNotification(`Error: ${data.error || 'No se pudo aplicar el código'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error aplicando código:', error);
            showNotification(`Error: ${error.message}`, 'error');
        });
    }

    /**
     * Explora archivos relacionados con el código en un mensaje
     */
    function exploreRelatedFiles(messageId) {
        const message = document.getElementById(messageId);
        if (!message) return;
        
        // Buscar bloques de código
        const codeBlocks = message.querySelectorAll('pre code');
        if (codeBlocks.length === 0) {
            addSystemMessage('<i class="bi bi-exclamation-circle"></i> No se encontró código para analizar');
            return;
        }
        
        // Extraer código y lenguaje del primer bloque
        const codeContent = codeBlocks[0].textContent;
        const language = codeBlocks[0].className.replace('language-', '');
        
        // Mostrar indicador de carga
        addSystemMessage('<i class="bi bi-search"></i> Buscando archivos relacionados con el código...');
        
        // Enviar solicitud al servidor
        fetch(config.endpoints.fileOperations + '/find_related', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: codeContent,
                language: language
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.files && data.files.length > 0) {
                // Mostrar archivos relacionados
                let filesMessage = `<div class="related-files">
                    <h4><i class="bi bi-folder2"></i> Archivos relacionados encontrados:</h4>
                    <ul class="files-list">`;
                
                data.files.forEach(file => {
                    filesMessage += `
                        <li class="file-item">
                            <span class="file-icon"><i class="bi bi-file-code"></i></span>
                            <span class="file-path">${file.path}</span>
                            <span class="file-actions">
                                <button onclick="agenteApp.viewFileContent('${file.path}')" title="Ver contenido">
                                    <i class="bi bi-eye"></i>
                                </button>
                                <button onclick="agenteApp.openFileInEditor('${file.path}')" title="Abrir en editor">
                                    <i class="bi bi-pencil-square"></i>
                                </button>
                            </span>
                        </li>`;
                });
                
                filesMessage += `</ul></div>`;
                addSystemMessage(filesMessage);
            } else {
                addSystemMessage('<i class="bi bi-info-circle"></i> No se encontraron archivos relacionados con el código.');
            }
        })
        .catch(error => {
            console.error('Error buscando archivos:', error);
            addSystemMessage(`<i class="bi bi-exclamation-triangle"></i> Error al buscar archivos relacionados: ${error.message}`);
        });
    }

    /**
     * Contextualiza el código con información del proyecto
     */
    function contextualizeCode(messageId) {
        const message = document.getElementById(messageId);
        if (!message) return;
        
        // Buscar bloques de código
        const codeBlocks = message.querySelectorAll('pre code');
        if (codeBlocks.length === 0) {
            addSystemMessage('<i class="bi bi-exclamation-circle"></i> No se encontró código para contextualizar');
            return;
        }
        
        // Extraer código y lenguaje del primer bloque
        const codeContent = codeBlocks[0].textContent;
        const language = codeBlocks[0].className.replace('language-', '');
        
        // Mostrar indicador de carga
        addSystemMessage('<i class="bi bi-braces"></i> Contextualizando el código...');
        
        // Enviar solicitud al servidor
        fetch(config.endpoints.codeGeneration + '/contextualize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: codeContent,
                language: language
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Mostrar contextualización
                let contextMessage = `<div class="code-context">
                    <h4><i class="bi bi-braces"></i> Contextualización del código:</h4>
                    <div class="context-details">
                        ${data.explanation || 'No se pudo generar explicación'}
                    </div>`;
                
                if (data.dependencies && data.dependencies.length > 0) {
                    contextMessage += `
                        <div class="context-section">
                            <h5>Dependencias detectadas:</h5>
                            <ul>
                                ${data.dependencies.map(dep => `<li>${dep}</li>`).join('')}
                            </ul>
                        </div>`;
                }
                
                if (data.references && data.references.length > 0) {
                    contextMessage += `
                        <div class="context-section">
                            <h5>Referencias a otros archivos:</h5>
                            <ul>
                                ${data.references.map(ref => `<li>${ref}</li>`).join('')}
                            </ul>
                        </div>`;
                }
                
                contextMessage += `</div>`;
                addSystemMessage(contextMessage);
            } else {
                addSystemMessage(`<i class="bi bi-exclamation-triangle"></i> Error al contextualizar el código: ${data.error || 'Error desconocido'}`);
            }
        })
        .catch(error => {
            console.error('Error contextualizando código:', error);
            addSystemMessage(`<i class="bi bi-exclamation-triangle"></i> Error al contextualizar el código: ${error.message}`);
        });
    }

    /**
     * Ver el contenido de un archivo
     */
    function viewFileContent(filePath) {
        // Mostrar indicador de carga
        addSystemMessage(`<i class="bi bi-hourglass-split"></i> Cargando contenido de ${filePath}...`);
        
        // Solicitar el contenido del archivo
        fetch(config.endpoints.fileOperations + '/read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Determinar el lenguaje basado en la extensión
                const extension = filePath.split('.').pop().toLowerCase();
                let language = 'plaintext';
                
                switch (extension) {
                    case 'js': language = 'javascript'; break;
                    case 'ts': language = 'typescript'; break;
                    case 'py': language = 'python'; break;
                    case 'html': language = 'html'; break;
                    case 'css': language = 'css'; break;
                    case 'json': language = 'json'; break;
                    // Añadir más mapeos según sea necesario
                }
                
                // Mostrar contenido del archivo
                const fileContent = `<div class="file-content">
                    <div class="file-header">
                        <span><i class="bi bi-file-earmark-code"></i> ${filePath}</span>
                        <button onclick="agenteApp.openFileInEditor('${filePath}')" title="Abrir en editor">
                            <i class="bi bi-pencil-square"></i> Editar
                        </button>
                    </div>
                    <pre><code class="language-${language}">${data.content}</code></pre>
                </div>`;
                
                addSystemMessage(fileContent);
                
                // Aplicar highlight.js
                if (window.hljs) {
                    document.querySelectorAll('.file-content pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }
            } else {
                addSystemMessage(`<i class="bi bi-exclamation-triangle"></i> Error al leer el archivo: ${data.error || 'Error desconocido'}`);
            }
        })
        .catch(error => {
            console.error('Error leyendo archivo:', error);
            addSystemMessage(`<i class="bi bi-exclamation-triangle"></i> Error al leer el archivo: ${error.message}`);
        });
    }

    /**
     * Abre un archivo en el editor
     */
    function openFileInEditor(filePath) {
        window.open(`/editor?file=${encodeURIComponent(filePath)}`, '_blank');
    }

    /**
     * Muestra una notificación
     */
    function showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Agregar a la página
        document.body.appendChild(notification);
        
        // Eliminar después de un tiempo
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // API pública del módulo
    return {
        initialize: initialize,
        addSystemMessage: addSystemMessage,
        addUserMessage: addUserMessage,
        addAssistantMessage: addAssistantMessage,
        applyCode: applyCode,
        selectCodeBlock: selectCodeBlock,
        closeCodeSelectionDialog: closeCodeSelectionDialog,
        switchFileTab: switchFileTab,
        toggleFolderInput: toggleFolderInput,
        closeFileSelectionDialog: closeFileSelectionDialog,
        applyCodeToFile: applyCodeToFile,
        exploreRelatedFiles: exploreRelatedFiles,
        contextualizeCode: contextualizeCode,
        viewFileContent: viewFileContent,
        openFileInEditor: openFileInEditor
    };
})();

// Inicializar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    agenteApp.initialize();
});
