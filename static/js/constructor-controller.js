
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
                endTime: null
            };
            
            this.options = {
                autoResume: true,
                maxRetries: 3,
                timeout: 60000 // 60 segundos
            };
            
            this.callbacks = {
                onProgress: null,
                onPause: null,
                onResume: null,
                onComplete: null,
                onError: null
            };
            
            // Inicializar
            this.init();
        }
        
        init() {
            console.log('Constructor controller inicializado');
            
            // Registrar eventos globales
            window.addEventListener('constructor-progress', this.handleProgress.bind(this));
            
            // Publicar métodos en el objeto global
            window.constructorController = this;
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
