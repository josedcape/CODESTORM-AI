
/**
 * Cargador del procesador de comandos naturales
 * Este script asegura que natural-command-processor.js esté cargado correctamente
 */

(function() {
  // Verificar si ya está cargado
  if (typeof NaturalCommandProcessor !== 'undefined') {
    console.log('NaturalCommandProcessor ya está cargado');
    return;
  }

  // Cargar el script
  const script = document.createElement('script');
  script.src = '/static/js/natural-command-processor.js';
  script.async = true;
  script.onload = () => {
    console.log('NaturalCommandProcessor cargado correctamente');
    // Notificar a otros scripts que podrían estar esperando
    document.dispatchEvent(new CustomEvent('natural-command-processor-loaded'));
  };
  script.onerror = (err) => {
    console.error('Error al cargar NaturalCommandProcessor:', err);
  };

  document.head.appendChild(script);
})();
