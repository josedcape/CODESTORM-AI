/**
 * Command Assistant - Ahora redirige al asistente flotante
 * Este archivo se mantiene para compatibilidad pero toda la funcionalidad
 * se ha movido al asistente flotante
 */

(function() {
    // Redirigir al asistente flotante
    const commandAssistant = {
        init: function() {
            // Comprobar si existe el asistente flotante
            if (window.floatingAssistant) {
                console.log('Usando asistente flotante para comandos');
            } else {
                console.warn('Asistente flotante no encontrado');
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