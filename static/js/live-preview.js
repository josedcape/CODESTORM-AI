
/**
 * Módulo para implementar preview en tiempo real con MutationObserver
 */

class LivePreview {
  constructor(options = {}) {
    this.targetSelector = options.targetSelector || 'body';
    this.previewSelector = options.previewSelector || '#preview-iframe';
    this.interval = options.interval || 1000;
    this.lastContent = '';
    this.observer = null;
    this.debounceTimer = null;
  }

  /**
   * Inicia el monitoreo de cambios
   */
  init() {
    this.preview = document.querySelector(this.previewSelector);
    
    if (!this.preview) {
      console.error("Elemento de preview no encontrado");
      return;
    }
    
    // Configurar el MutationObserver
    this.setupObserver();
    
    // Realizar actualización inicial
    this.updatePreview();
    
    console.log("Live Preview inicializado");
  }
  
  /**
   * Configura el MutationObserver para detectar cambios en el DOM
   */
  setupObserver() {
    const config = {
      attributes: true,
      childList: true, 
      subtree: true,
      characterData: true
    };
    
    // Crear el observer
    this.observer = new MutationObserver((mutationsList) => {
      this.handleMutations(mutationsList);
    });
    
    // Observar el elemento seleccionado
    const targetElements = document.querySelectorAll(this.targetSelector);
    targetElements.forEach(element => {
      this.observer.observe(element, config);
    });
  }
  
  /**
   * Maneja las mutaciones detectadas
   */
  handleMutations(mutationsList) {
    // Debounce para evitar actualizaciones excesivas
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    
    this.debounceTimer = setTimeout(() => {
      this.updatePreview();
    }, this.interval);
  }
  
  /**
   * Actualiza la vista previa
   */
  updatePreview() {
    try {
      // Solo actualizar si hay cambios
      const currentContent = document.documentElement.innerHTML;
      
      if (currentContent !== this.lastContent) {
        // Guardar el contenido actual
        this.lastContent = currentContent;
        
        // Actualizar el iframe si está visible
        if (this.preview.parentElement.style.display !== 'none') {
          // Si el iframe tiene un src, recargarlo
          if (this.preview.src && !this.preview.src.includes('about:blank')) {
            this.preview.contentWindow.location.reload();
          } else {
            // Si no tiene src, actualizar directamente su contenido
            const previewDoc = this.preview.contentDocument || this.preview.contentWindow.document;
            previewDoc.open();
            previewDoc.write(currentContent);
            previewDoc.close();
          }
        }
      }
    } catch (error) {
      console.error("Error al actualizar la vista previa:", error);
    }
  }
  
  /**
   * Detiene el monitoreo de cambios
   */
  stop() {
    if (this.observer) {
      this.observer.disconnect();
    }
    
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
  }
}

// Exportar para uso en otros módulos
window.LivePreview = LivePreview;
