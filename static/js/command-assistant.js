/**
 * Command Assistant - Integración con el asistente flotante
 * Asegura que la funcionalidad de comandos esté disponible a través del asistente flotante
 */

(function() {
    // Interfaz para el asistente de comandos
    const commandAssistant = {
        isConnected: false,
        connectionAttempts: 0,
        maxConnectionAttempts: 3,
        
        init: function() {
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
        
        // Verificar la conexión con el servidor
        checkServerConnection: function() {
            fetch('/api/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            })
            .then(response => {
                if (response.ok) {
                    this.isConnected = true;
                    console.log('Asistente de comandos conectado al servidor');
                    // Intentar notificar en la UI si existe
                    this.updateConnectionStatus(true);
                    return response.json();
                } else {
                    throw new Error('No se pudo conectar al servidor');
                }
            })
            .catch(error => {
                console.warn('Error de conexión con el servidor:', error);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Intentar reconectar si no hemos excedido el número máximo de intentos
                if (this.connectionAttempts < this.maxConnectionAttempts) {
                    this.connectionAttempts++;
                    console.log(`Intento de reconexión ${this.connectionAttempts} de ${this.maxConnectionAttempts}`);
                    setTimeout(() => this.checkServerConnection(), 1500 * this.connectionAttempts);
                }
            });
        },
        
        // Actualizar el estado de conexión en la UI si está disponible
        updateConnectionStatus: function(isConnected) {
            if (window.floatingAssistant && window.floatingAssistant.updateConnectionStatus) {
                window.floatingAssistant.updateConnectionStatus(isConnected);
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
            if (window.floatingAssistant) {
                return window.floatingAssistant.processQuery(command);
            } else {
                console.error('Asistente flotante no disponible');
                return false;
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
                document.getElementById('floating-assistant-container')) {
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