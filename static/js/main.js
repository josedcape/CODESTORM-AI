/**
 * Funciones principales de Codestorm Assistant
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Codestorm Assistant inicializado');

    // Variables para controlar el estado de pausa del constructor
    window.constructorState = {
        isPaused: false,
        progress: 0,
        pauseCallback: null,
        resumeCallback: null
    };

    // Función para pausar el constructor
    window.pauseConstructor = function(callback) {
        window.constructorState.isPaused = true;
        if (callback && typeof callback === 'function') {
            window.constructorState.pauseCallback = callback;
            callback();
        }
        console.log('Constructor pausado');
        return window.constructorState.isPaused;
    };

    // Función para reanudar el constructor
    window.resumeConstructor = function(callback) {
        window.constructorState.isPaused = false;
        if (callback && typeof callback === 'function') {
            window.constructorState.resumeCallback = callback;
            callback();
        }
        console.log('Constructor reanudado');
        return !window.constructorState.isPaused;
    };

    // Inicializar tooltips de Bootstrap si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Inicializar popovers de Bootstrap si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Función para mostrar mensajes de notificación
    window.showNotification = function(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            // Crear contenedor si no existe
            const container = document.createElement('div');
            container.id = 'alert-container';
            container.style.position = 'fixed';
            container.style.top = '10px';
            container.style.right = '10px';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.getElementById('alert-container').appendChild(alert);

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            if (alert) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    };

    // Hacer que los campos de formulario con la clase 'autosize' se ajusten automáticamente
    document.querySelectorAll('textarea.autosize').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // Trigger inicial
        textarea.dispatchEvent(new Event('input'));
    });

    // Integración markdown automática para elementos con la clase 'markdown-content'
    if (typeof marked !== 'undefined') {
        // Verificamos si marked es un objeto (versión más reciente) o una función (versión antigua)
        const markdownParser = typeof marked.parse === 'function' ? marked.parse : (typeof marked === 'function' ? marked : null);

        if (markdownParser) {
            document.querySelectorAll('.markdown-content').forEach(element => {
                const markdown = element.textContent || element.innerText;
                try {
                    element.innerHTML = markdownParser(markdown);

                    // Resaltar código si prism está disponible
                    if (typeof Prism !== 'undefined') {
                        element.querySelectorAll('pre code').forEach(block => {
                            Prism.highlightElement(block);
                        });
                    }
                } catch (e) {
                    console.error('Error al procesar markdown:', e);
                }
            });
        } else {
            // Cargar marked dinámicamente si no está disponible
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            script.onload = function() {
                console.log('Biblioteca marked cargada correctamente');
                // Volver a intentar procesar el markdown cuando se cargue
                const markdownParser = typeof marked.parse === 'function' ? marked.parse : marked;

                document.querySelectorAll('.markdown-content').forEach(element => {
                    const markdown = element.textContent || element.innerText;
                    try {
                        element.innerHTML = markdownParser(markdown);
                    } catch (e) {
                        console.error('Error al procesar markdown:', e);
                    }
                });
            };
            document.head.appendChild(script);
        }
    }

    // Función para copiar texto al portapapeles
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showNotification('Copiado al portapapeles', 'success');
            })
            .catch(err => {
                console.error('Error al copiar: ', err);
                showNotification('Error al copiar al portapapeles', 'danger');
            });
    };

    window.webSocketClient = {
        sendMessage: function(type, data) {
            if (socket && socket.connected) {
                socket.emit(type, data);
            } else if (window.nativeWebSocket && window.nativeWebSocket.readyState === WebSocket.OPEN) {
                window.nativeWebSocket.send(JSON.stringify({
                    type: type,
                    data: data
                }));
            }
        }
    };

    // Configurar endpoints API globalmente
    window.app = window.app || {};
    window.app.apiEndpoints = {
        chat: '/api/chat',
        fallback: '/api/generate',
        health: '/api/health',
        processCode: '/api/process_code',
        execute: '/api/execute_command',
        files: '/api/files',
        assistant: {
            chat: '/api/assistant/chat',
            execute: '/api/assistant/execute-action',
            files: '/api/assistant/files',
            interventionMode: '/api/assistant/intervention-mode',
            applyChanges: '/api/assistant/apply-changes'
        }
    };

    // Verificar disponibilidad de APIs
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('Estado de la API:', data.status || 'OK');
        })
        .catch(error => {
            console.warn('Error al verificar estado de API:', error);
            showNotification('Algunas funciones del asistente podrían no estar disponibles', 'warning');
        });

    // Inicializar la funcionalidad del asistente flotante
    if (typeof initFloatingAssistant === 'function') {
        initFloatingAssistant();
    }

    // Inicializar el chat si estamos en la página de chat
    if (document.getElementById('chat-container')) {
        console.log('DOM cargado, inicializando chat...');

        // Configurar un observer para mensajes de chat
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            console.log('Observer para mensajes de chat configurado');

            // Asegurar que los objetos necesarios estén inicializados
            window.app = window.app || {};
            window.app.chat = window.app.chat || {};

            // Inicializar endpoints API
            window.app.apiEndpoints = window.app.apiEndpoints || {
                chat: '/api/chat',
                fallback: '/api/generate',
                health: '/api/health',
                processCode: '/api/process_code',
                execute: '/api/execute_command',
                files: '/api/files'
            };

            // Inicializar el objeto chat si no existe
            if (!window.app.chat) {
                window.app.chat = {};
            }

            // Asignar endpoints al chat
            window.app.chat.apiEndpoints = window.app.apiEndpoints;

            // Verificar explícitamente que los endpoints existan
            console.log('API Endpoints configurados:', window.app.chat.apiEndpoints);

            // Inicializar chat
            if (typeof window.initializeChat === 'function') {
                window.initializeChat();
            } else if (typeof initializeChat === 'function') {
                initializeChat();
            } else {
                console.error('La función initializeChat no está disponible. Verifica que chat.js se cargó correctamente.');

                // Intento de recuperación: cargar dinámicamente chat.js
                const chatScript = document.createElement('script');
                chatScript.src = '/static/js/chat/chat.js';
                chatScript.onload = function() {
                    console.log('Chat.js cargado dinámicamente');
                    if (typeof window.initializeChat === 'function') {
                        window.initializeChat();
                    } else {
                        console.error('No se pudo cargar la función initializeChat. Recargando la página...');
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000);
                    }
                };
                chatScript.onerror = function() {
                    console.error('Error al cargar chat.js');
                    alert('Error al cargar el módulo de chat. Por favor, recarga la página.');
                };
                document.head.appendChild(chatScript);
            }
        }
    }
});

// Función para formatear fechas
function formatDate(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }

    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };

    return date.toLocaleDateString('es-ES', options);
}

// Función para formatear bytes a unidades legibles
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Inicializar el corrector de código cuando esté en la página correspondiente
document.addEventListener('DOMContentLoaded', function() {
    // Comprobar si estamos en la página de corrector de código
    if (document.getElementById('process-btn') && document.getElementById('code-input')) {
        console.log('Inicializando corrector de código...');

        // Configurar el manipulador de eventos para el botón de proceso
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.addEventListener('click', function() {
                const codeInput = document.getElementById('code-input');
                const language = document.getElementById('code-language').value;
                const instructions = document.getElementById('instructions')?.value || '';
                const modelSelect = document.getElementById('model-select');

                if (!codeInput || !codeInput.value.trim()) {
                    window.showNotification?.('Por favor, ingresa código para corregir', 'warning') || 
                    alert('Por favor, ingresa código para corregir');
                    return;
                }

                // Mostrar indicador de carga
                processBtn.disabled = true;
                processBtn.innerHTML = '<span class="btn-content"><div class="btn-spinner"></div> Procesando...</span>';

                // Mostrar la barra de progreso
                const progressContainer = document.getElementById('progress-container');
                const progressBar = document.getElementById('correction-progress-bar');
                const progressStatus = document.getElementById('progress-status');

                if (progressContainer) progressContainer.style.display = 'block';
                if (progressBar) progressBar.style.width = '0%';
                if (progressStatus) progressStatus.textContent = 'Iniciando corrección...';

                // Simular progreso (ya que el proceso real ocurre en el servidor)
                let progress = 0;
                const progressInterval = setInterval(() => {
                    if (progress < 95) {
                        progress += Math.random() * 10;
                        if (progress > 95) progress = 95; // Máximo antes de completar

                        if (progressBar) progressBar.style.width = `${progress}%`;

                        // Mostrar mensaje cuando esté cerca de terminar
                        if (progress > 75 && progressStatus) {
                            progressStatus.textContent = 'Ya casi finalizamos, paciencia...';
                        } else if (progress > 50 && progressStatus) {
                            progressStatus.textContent = 'Optimizando el código...';
                        } else if (progress > 20 && progressStatus) {
                            progressStatus.textContent = 'Analizando errores...';
                        }
                    }
                }, 800);

                // Llamar a la API para procesar el código
                fetch('/api/process_code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: codeInput.value.trim(),
                        language: language,
                        instructions: instructions || 'Corrige errores y mejora la calidad del código',
                        model: modelSelect?.value || 'openai',
                        auto_fix: true,
                        optimize: true,
                        improve_readability: true
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error en el servidor: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Mostrar resultados
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.style.display = 'block';
                    }

                    // Actualizar código corregido
                    const correctedCode = document.getElementById('corrected-code');
                    if (correctedCode && data.corrected_code) {
                        correctedCode.textContent = data.corrected_code;

                        // Resaltar sintaxis si está disponible
                        if (window.hljs) {
                            hljs.highlightElement(correctedCode);
                        }
                    }

                    // Actualizar explicación
                    const explanationText = document.getElementById('explanation-text');
                    if (explanationText && data.explanation) {
                        if (window.marked && typeof window.marked === 'function') {
                            explanationText.innerHTML = window.marked(data.explanation);
                        } else {
                            explanationText.textContent = data.explanation;
                        }
                    }

                    // Mostrar cambios
                    if (data.changes && document.getElementById('changes-list')) {
                        renderChanges(data.changes);
                    }

                    // Actualizar vista de diferencias si hay función definida
                    if (typeof generateDiff === 'function' && document.getElementById('diff-view')) {
                        document.getElementById('diff-view').innerHTML = generateDiff(codeInput.value.trim(), data.corrected_code);
                    }

                    window.showNotification?.('Código corregido exitosamente', 'success') || 
                    console.log('Código corregido exitosamente');
                    clearInterval(progressInterval); //Detener el intervalo después de completar
                    if (progressStatus) progressStatus.textContent = 'Corrección completada!';
                })
                .catch(error => {
                    console.error('Error:', error);
                    window.showNotification?.(`Error: ${error.message}`, 'error') || 
                    alert(`Error: ${error.message}`);
                    clearInterval(progressInterval); //Detener el intervalo en caso de error
                    if (progressStatus) progressStatus.textContent = 'Error durante la corrección.';

                })
                .finally(() => {
                    // Restaurar botón
                    processBtn.disabled = false;
                    processBtn.innerHTML = '<span class="btn-content"><i class="bi bi-wrench"></i> Corregir código</span>';
                    if (progressContainer) progressContainer.style.display = 'none'; //Ocultar el contenedor de progreso
                });
            });
        }

        // Función auxiliar para renderizar cambios
        window.renderChanges = function(changes) {
            const changesList = document.getElementById('changes-list');
            if (!changesList) return;

            changesList.innerHTML = '';

            if (changes && changes.length > 0) {
                changes.forEach((change, index) => {
                    const item = document.createElement('div');
                    item.className = 'cyber-list-item';

                    // Determinar badge de importancia
                    let importance = change.importance || 'info';
                    const badgeClass = importance === 'alta' ? 'cyber-badge-danger' :
                                      importance === 'media' ? 'cyber-badge-warning' : 'cyber-badge-info';

                    // Información de línea (verificando que lineNumbers sea un array)
                    let lineInfo = '';
                    if (change.lineNumbers && Array.isArray(change.lineNumbers)) {
                        lineInfo = `<span class="cyber-badge cyber-badge-secondary">Línea(s): ${change.lineNumbers.join(', ')}</span>`;
                    } else if (change.lineNumbers && typeof change.lineNumbers === 'string') {
                        lineInfo = `<span class="cyber-badge cyber-badge-secondary">Línea(s): ${change.lineNumbers}</span>`;
                    } else if (change.lineNumbers && typeof change.lineNumbers === 'number') {
                        lineInfo = `<span class="cyber-badge cyber-badge-secondary">Línea: ${change.lineNumbers}</span>`;
                    }

                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div><span class="cyber-badge ${badgeClass}">${importance}</span> ${change.description}</div>
                            ${lineInfo}
                        </div>
                    `;

                    changesList.appendChild(item);
                });
            } else {
                const item = document.createElement('div');
                item.className = 'cyber-list-item';
                item.innerHTML = 'No se detectaron cambios significativos';
                changesList.appendChild(item);
            }
        };
    }
});