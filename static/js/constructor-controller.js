
// Constructor Controller - Maneja el estado y progreso del constructor de aplicaciones

(function() {
    // Clase controladora del constructor
    class ConstructorController {
        constructor() {
            this.state = {
                isPaused: false,
                progress: 0,
                currentStep: null,
                steps: [],
                errors: [],
                startTime: null,
                endTime: null,
                projectId: null,
                apiConnected: false
            };
            
            this.options = {
                autoResume: true,
                maxRetries: 3,
                timeout: 60000, // 60 segundos
                apiEndpoints: {
                    generate: '/api/constructor/generate',
                    status: '/api/constructor/status/',
                    download: '/api/constructor/download/',
                    preview: '/api/constructor/preview/',
                    pause: '/api/constructor/pause/',
                    resume: '/api/constructor/resume/',
                    analyze: '/api/constructor/analyze-features'
                }
            };
            
            this.callbacks = {
                onProgress: null,
                onPause: null,
                onResume: null,
                onComplete: null,
                onError: null,
                onApiStatus: null
            };
            
            // Inicializar
            this.init();
        }
        
        init() {
            console.log('Constructor controller inicializado');
            
            // Registrar eventos globales
            window.addEventListener('constructor-progress', this.handleProgress.bind(this));
            
            // Verificar estado de la API
            this.checkApiStatus();
            
            // Publicar métodos en el objeto global
            window.constructorController = this;
        }
        
        // Verificar si las APIs están disponibles
        checkApiStatus() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    this.state.apiConnected = true;
                    console.log('APIs conectadas:', data);
                    
                    // Ejecutar callback si existe
                    if (typeof this.callbacks.onApiStatus === 'function') {
                        this.callbacks.onApiStatus(true, data);
                    }
                })
                .catch(error => {
                    this.state.apiConnected = false;
                    console.error('Error conectando a las APIs:', error);
                    
                    // Ejecutar callback si existe
                    if (typeof this.callbacks.onApiStatus === 'function') {
                        this.callbacks.onApiStatus(false, error);
                    }
                });
        }
        
        // Generar una nueva aplicación
        generateApplication(description, agent, model, options, features) {
            if (!this.state.apiConnected) {
                console.error('APIs no conectadas');
                return Promise.reject(new Error('APIs no conectadas'));
            }
            
            return fetch(this.options.apiEndpoints.generate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    description: description,
                    agent: agent,
                    model: model,
                    options: options,
                    features: features
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.projectId = data.project_id;
                    this.state.startTime = new Date();
                    return data;
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            });
        }
        
        // Pausar la construcción
        pause(reason) {
            if (this.state.isPaused) return false;
            
            this.state.isPaused = true;
            this.state.pauseReason = reason || 'Manual pause';
            
            console.log(`Constructor pausado: ${this.state.pauseReason}`);
            
            // Ejecutar callback si existe
            if (typeof this.callbacks.onPause === 'function') {
                this.callbacks.onPause(this.state);
            }
            
            return true;
        }
        
        // Reanudar la construcción
        resume() {
            if (!this.state.isPaused) return false;
            
            this.state.isPaused = false;
            this.state.pauseReason = null;
            
            console.log('Constructor reanudado');
            
            // Ejecutar callback si existe
            if (typeof this.callbacks.onResume === 'function') {
                this.callbacks.onResume(this.state);
            }
            
            return true;
        }
        
        // Actualizar el progreso
        updateProgress(progress, step) {
            if (progress < 0) progress = 0;
            if (progress > 100) progress = 100;
            
            this.state.progress = progress;
            
            if (step) {
                this.state.currentStep = step;
                this.state.steps.push({
                    name: step,
                    progress: progress,
                    timestamp: new Date()
                });
            }
            
            // Ejecutar callback si existe
            if (typeof this.callbacks.onProgress === 'function') {
                this.callbacks.onProgress(this.state);
            }
            
            // Actualizar interfaz de usuario
            this.updateUI();
            
            return this.state.progress;
        }
        
        // Manejar eventos de progreso
        handleProgress(event) {
            const data = event.detail || {};
            this.updateProgress(data.progress, data.step);
        }
        
        // Actualizar elementos de la interfaz
        updateUI() {
            // Actualizar barra de progreso si existe
            const progressBar = document.getElementById('constructor-progress');
            if (progressBar) {
                progressBar.style.width = `${this.state.progress}%`;
                progressBar.setAttribute('aria-valuenow', this.state.progress);
                
                // Actualizar texto de progreso
                const progressText = document.getElementById('constructor-progress-text');
                if (progressText) {
                    progressText.textContent = `${Math.round(this.state.progress)}%`;
                }
            }
            
            // Actualizar estado actual
            const currentStepElement = document.getElementById('current-step');
            if (currentStepElement && this.state.currentStep) {
                currentStepElement.textContent = this.state.currentStep;
            }
            
            // Actualizar botones de control según el estado
            const pauseButton = document.getElementById('pause-constructor');
            const resumeButton = document.getElementById('resume-constructor');
            
            if (pauseButton) {
                pauseButton.disabled = this.state.isPaused;
            }
            
            if (resumeButton) {
                resumeButton.disabled = !this.state.isPaused;
            }
        }
        
        // Registrar un error
        logError(error, fatal = false) {
            const errorObj = {
                message: error.message || error,
                timestamp: new Date(),
                step: this.state.currentStep,
                progress: this.state.progress,
                fatal: fatal
            };
            
            this.state.errors.push(errorObj);
            console.error('Constructor error:', errorObj);
            
            // Ejecutar callback si existe
            if (typeof this.callbacks.onError === 'function') {
                this.callbacks.onError(errorObj);
            }
            
            // Pausar si es un error fatal
            if (fatal) {
                this.pause(`Error fatal: ${errorObj.message}`);
            }
            
            return errorObj;
        }
        
        // Verificar estado del proyecto
        checkProjectStatus(projectId) {
            if (!projectId && this.state.projectId) {
                projectId = this.state.projectId;
            }
            
            if (!projectId) {
                return Promise.reject(new Error('ID de proyecto no especificado'));
            }
            
            return fetch(`${this.options.apiEndpoints.status}${projectId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Actualizar estado con los datos del servidor
                        this.state.progress = data.progress || 0;
                        this.state.currentStep = data.current_stage || '';
                        
                        // Si hay un mensaje de consola nuevo, añadirlo
                        if (data.console_message) {
                            this.state.steps.push({
                                name: data.current_stage,
                                progress: data.progress,
                                message: data.console_message.message,
                                timestamp: new Date(data.console_message.time * 1000)
                            });
                        }
                        
                        // Actualizar UI
                        this.updateUI();
                        
                        // Ejecutar callback si existe
                        if (typeof this.callbacks.onProgress === 'function') {
                            this.callbacks.onProgress(this.state);
                        }
                        
                        return data;
                    } else {
                        throw new Error(data.error || 'Error desconocido');
                    }
                });
        }
        
        // Pausar el desarrollo del proyecto
        pauseProject(projectId) {
            if (!projectId && this.state.projectId) {
                projectId = this.state.projectId;
            }
            
            if (!projectId) {
                return Promise.reject(new Error('ID de proyecto no especificado'));
            }
            
            return fetch(`${this.options.apiEndpoints.pause}${projectId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.isPaused = true;
                    
                    // Ejecutar callback si existe
                    if (typeof this.callbacks.onPause === 'function') {
                        this.callbacks.onPause(this.state);
                    }
                    
                    return data;
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            });
        }
        
        // Reanudar el desarrollo del proyecto
        resumeProject(projectId) {
            if (!projectId && this.state.projectId) {
                projectId = this.state.projectId;
            }
            
            if (!projectId) {
                return Promise.reject(new Error('ID de proyecto no especificado'));
            }
            
            return fetch(`${this.options.apiEndpoints.resume}${projectId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.isPaused = false;
                    
                    // Ejecutar callback si existe
                    if (typeof this.callbacks.onResume === 'function') {
                        this.callbacks.onResume(this.state);
                    }
                    
                    return data;
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            });
        }
        
        // Analizar características de una descripción
        analyzeFeatures(description) {
            return fetch(this.options.apiEndpoints.analyze, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    description: description
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    return data;
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            });
        }
        
        // Registrar una función callback
        on(event, callback) {
            if (typeof callback !== 'function') {
                console.error('El callback debe ser una función');
                return false;
            }
            
            switch(event) {
                case 'progress':
                    this.callbacks.onProgress = callback;
                    break;
                case 'pause':
                    this.callbacks.onPause = callback;
                    break;
                case 'resume':
                    this.callbacks.onResume = callback;
                    break;
                case 'complete':
                    this.callbacks.onComplete = callback;
                    break;
                case 'error':
                    this.callbacks.onError = callback;
                    break;
                case 'apiStatus':
                    this.callbacks.onApiStatus = callback;
                    break;
                default:
                    console.warn(`Evento no reconocido: ${event}`);
                    return false;
            }
            
            return true;
        }
    }
    
    // Crear instancia y asignarla globalmente
    const controller = new ConstructorController();
    window.constructorController = controller;
    
    // Inicializar controlador cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            // Buscar elementos de control en la página
            const pauseButton = document.getElementById('pause-constructor');
            const resumeButton = document.getElementById('resume-constructor');
            
            if (pauseButton) {
                pauseButton.addEventListener('click', () => controller.pause());
            }
            
            if (resumeButton) {
                resumeButton.addEventListener('click', () => controller.resume());
            }
        });
    }
})();
