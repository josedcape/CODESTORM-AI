
/**
 * Command Assistant - Integración con el asistente flotante
 * Asegura que la funcionalidad de comandos esté disponible a través del asistente flotante
 */

(function() {
    // Interfaz para el asistente de comandos
    const commandAssistant = {
        init: function() {
            // Verificar si el asistente flotante ya existe
            if (window.floatingAssistant) {
                console.log('Usando asistente flotante existente para comandos');
                return;
            }
            
            // Si no existe el asistente flotante, cargar el script
            this.loadFloatingAssistant();
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

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => commandAssistant.init());
    } else {
        commandAssistant.init();
    }
})();
