/**
 * Formateador de código para el chat interactivo
 * Ayuda a mostrar y renderizar código en el chat del agente
 */

// Función para resaltar sintaxis en bloques de código
function highlightCode(code, language) {
  // Si hljs no está disponible, devolver el código con escape HTML básico
  if (typeof hljs === 'undefined') {
    return escapeHtml(code);
  }

  try {
    if (language && hljs.getLanguage(language)) {
      return hljs.highlight(code, {language: language}).value;
    } else {
      return hljs.highlightAuto(code).value;
    }
  } catch (e) {
    console.error("Error al resaltar código:", e);
    return escapeHtml(code);
  }
}

// Función para escapar HTML
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// Función para formatear el código de la respuesta del asistente
function formatCodeResponse(response) {
  if (!response) return '';

  // Reemplazar bloques de código con formato
  let formattedResponse = response.replace(/```(\w*)\n([\s\S]+?)```/g, function(match, language, code) {
    language = language.trim() || 'plaintext';

    const highlightedCode = highlightCode(code, language);

    return `<div class="code-block-container">
      <div class="code-toolbar">
        <span class="code-language">${language}</span>
        <button class="btn btn-sm btn-dark code-copy-btn" onclick="copyCode(this)" title="Copiar código">
          <i class="bi bi-clipboard"></i> Copiar
        </button>
      </div>
      <pre><code class="language-${language}">${highlightedCode}</code></pre>
    </div>`;
  });

  // Reemplazar código en línea
  formattedResponse = formattedResponse.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Convertir saltos de línea a etiquetas <br>
  formattedResponse = formattedResponse.replace(/\n/g, '<br>');

  return formattedResponse;
}

// Función para copiar código al portapapeles
function copyCode(button) {
  // Encontrar el contenedor y el elemento de código
  const codeContainer = button.closest('.code-block-container');
  if (!codeContainer) {
    console.error('No se pudo encontrar el contenedor de código');
    return;
  }
  
  const preElement = codeContainer.querySelector('pre');
  const codeElement = preElement.querySelector('code');
  
  if (!codeElement) {
    console.error('No se pudo encontrar el elemento de código');
    return;
  }
  
  // Obtener el texto real sin formato HTML
  const textToCopy = codeElement.textContent || codeElement.innerText;

  // Crear un elemento de texto temporal para copiar
  const textArea = document.createElement('textarea');
  textArea.value = textToCopy;
  textArea.style.position = 'fixed';  // Evita desplazamiento
  textArea.style.opacity = '0';
  document.body.appendChild(textArea);
  textArea.select();

  try {
    // Intentar usar el nuevo API de clipboard si está disponible
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        // Éxito - cambia el botón para dar feedback
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.style.backgroundColor = '#28a745';
        
        // Mostrar una notificación de éxito temporal
        if (window.showNotification) {
          window.showNotification('Código copiado al portapapeles', 'success');
        }

        setTimeout(() => {
          button.innerHTML = originalText;
          button.style.backgroundColor = '';
        }, 2000);
      }).catch(err => {
        console.error('Error al copiar texto: ', err);
        fallbackCopy();
      });
    } else {
      // Fallback para navegadores que no soportan clipboard API
      fallbackCopy();
    }
  } catch (err) {
    console.error('Error al copiar el código: ', err);
    fallbackCopy();
  }

  // Método alternativo de copia
  function fallbackCopy() {
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.style.backgroundColor = '#28a745';
        if (window.showNotification) {
          window.showNotification('Código copiado al portapapeles', 'success');
        }
      } else {
        button.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
        button.style.backgroundColor = '#dc3545';
        if (window.showNotification) {
          window.showNotification('No se pudo copiar el código', 'error');
        }
      }
    } catch (err) {
      console.error('Error en el fallback de copia: ', err);
      button.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
      button.style.backgroundColor = '#dc3545';
    }
    
    setTimeout(() => {
      button.innerHTML = '<i class="bi bi-clipboard"></i>';
      button.style.backgroundColor = '';
    }, 2000);
  }
  
  // Limpiar
  document.body.removeChild(textArea);
}

// Función para mostrar notificaciones si no existe globalmente
if (!window.showNotification) {
  window.showNotification = function(message, type) {
    console.log(`Notificación (${type}): ${message}`);
  };
}go al portapapeles
function copyCode(button) {
  // Encontrar el contenedor y el elemento de código
  const codeContainer = button.closest('.code-block-container');
  if (!codeContainer) {
    console.error('No se pudo encontrar el contenedor de código');
    return;
  }
  
  const preElement = codeContainer.querySelector('pre');
  const codeElement = preElement.querySelector('code');
  
  if (!codeElement) {
    console.error('No se pudo encontrar el elemento de código');
    return;
  }
  
  // Obtener el texto real sin formato HTML
  const textToCopy = codeElement.textContent || codeElement.innerText;

  // Crear un elemento de texto temporal para copiar
  const textArea = document.createElement('textarea');
  textArea.value = textToCopy;
  textArea.style.position = 'fixed';  // Evita desplazamiento
  textArea.style.opacity = '0';
  document.body.appendChild(textArea);
  textArea.select();

  try {
    // Intentar usar el nuevo API de clipboard si está disponible
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        // Éxito - cambia el botón para dar feedback
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.style.backgroundColor = '#28a745';
        
        // Mostrar una notificación de éxito temporal
        showNotification('Código copiado al portapapeles');

        setTimeout(() => {
          button.innerHTML = originalText;
          button.style.backgroundColor = '';
        }, 2000);
      }).catch(err => {
        console.error('Error al copiar texto: ', err);
        fallbackCopy();
      });
    } else {
      // Fallback para navegadores que no soportan clipboard API
      fallbackCopy();
    }
  } catch (err) {
    console.error('Error al copiar el código: ', err);
    fallbackCopy();
  }

  // Método alternativo de copia
  function fallbackCopy() {
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.style.backgroundColor = '#28a745';
        showNotification('Código copiado al portapapeles');
      } else {
        button.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
        button.style.backgroundColor = '#dc3545';
        showNotification('No se pudo copiar el código', 'error');
      }
    } catch (err) {
      console.error('Error en el fallback de copia: ', err);
      button.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
      button.style.backgroundColor = '#dc3545';
    }
    
    setTimeout(() => {
      button.innerHTML = '<i class="bi bi-clipboard"></i>';
      button.style.backgroundColor = '';
    }, 2000);
  }
  
  // Limpiar
  document.body.removeChild(textArea);
}

// Función para mostrar notificaciones de copia
function showNotification(message, type = 'success') {
  // Verificar si ya existe un contenedor de notificaciones
  let notificationContainer = document.getElementById('notification-container');
  
  if (!notificationContainer) {
    notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.position = 'fixed';
    notificationContainer.style.top = '20px';
    notificationContainer.style.right = '20px';
    notificationContainer.style.zIndex = '9999';
    document.body.appendChild(notificationContainer);
  }
  
  // Crear la notificación
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.style.padding = '10px 15px';
  notification.style.margin = '5px 0';
  notification.style.borderRadius = '4px';
  notification.style.color = 'white';
  notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
  notification.style.transition = 'all 0.3s ease';
  notification.style.opacity = '0';
  notification.style.transform = 'translateY(-20px)';
  
  // Estilos según el tipo
  if (type === 'success') {
    notification.style.backgroundColor = '#28a745';
  } else if (type === 'error') {
    notification.style.backgroundColor = '#dc3545';
  } else {
    notification.style.backgroundColor = '#17a2b8';
  }
  
  notification.textContent = message;
  
  // Añadir al contenedor
  notificationContainer.appendChild(notification);
  
  // Animar entrada
  setTimeout(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateY(0)';
  }, 10);
  
  // Eliminar después de un tiempo
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

// Exponer funciones globalmente
window.highlightCode = highlightCode;
window.formatCodeResponse = formatCodeResponse;
window.copyCode = copyCode;


/**
 * Formateador de código para la interfaz de chat
 * Este script se encarga de formatear correctamente los bloques de código en los mensajes del chat
 */

document.addEventListener('DOMContentLoaded', function() {
    // Función para formatear bloques de código en el contenido HTML
    function formatCodeBlocks(htmlContent) {
        if (!htmlContent) return htmlContent;

        // Buscar todos los bloques de código (```lenguaje ... ```)
        const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;

        // Reemplazar con un formato HTML adecuado
        return htmlContent.replace(codeBlockRegex, function(match, language, code) {
            // Escapar HTML para evitar inyección
            const escapedCode = code
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");

            return `<div class="code-block"><div class="code-header">${language || 'código'}</div><pre><code class="language-${language || 'plaintext'}">${escapedCode}</code></pre></div>`;
        });
    }

    // Función para agregar estilos de código
    function addCodeStyles() {
        if (document.getElementById('code-formatter-styles')) return;

        const styleElement = document.createElement('style');
        styleElement.id = 'code-formatter-styles';
        styleElement.textContent = `
            .code-block {
                background-color: #1e1e1e;
                border-radius: 6px;
                margin: 10px 0;
                overflow: hidden;
            }

            .code-header {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 6px 12px;
                font-family: monospace;
                font-size: 12px;
                text-transform: uppercase;
                border-bottom: 1px solid #3d3d3d;
            }

            .code-block pre {
                margin: 0;
                padding: 12px;
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #e0e0e0;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
                background-color: transparent;
                overflow-x: auto;
            }

            .code-block code {
                background-color: transparent;
                padding: 0;
            }

            /* Colores de sintaxis básicos */
            .language-javascript .keyword { color: #569CD6; }
            .language-javascript .string { color: #CE9178; }
            .language-javascript .number { color: #B5CEA8; }
            .language-javascript .comment { color: #6A9955; }

            .language-html .tag { color: #569CD6; }
            .language-html .attr { color: #9CDCFE; }
            .language-html .string { color: #CE9178; }

            .language-css .property { color: #9CDCFE; }
            .language-css .value { color: #CE9178; }
        `;

        document.head.appendChild(styleElement);
    }

    // Observar cambios en el DOM para formatear código en nuevos mensajes
    function observeMessages() {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        // Crear un observador
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('message') && 
                        node.classList.contains('assistant-message')) {
                        // Es un mensaje del asistente, formatear su contenido
                        const formattedContent = formatCodeBlocks(node.innerHTML);
                        node.innerHTML = formattedContent;
                    }
                });
            });
        });

        // Configurar y comenzar la observación
        observer.observe(messagesContainer, { childList: true });
    }

    // Inicializar formateador
    function initCodeFormatter() {
        addCodeStyles();
        observeMessages();
        console.log('Formateador de código inicializado');
    }

    // Iniciar el formateador
    initCodeFormatter();
});
/**
 * Utilidades para formatear código en los mensajes del chat
 */
const CodeFormatter = {
    /**
     * Detecta y formatea bloques de código en un mensaje
     * @param {string} message - El mensaje a formatear
     * @return {string} - Mensaje con código formateado en HTML
     */
    formatCode: function(message) {
        // Detectar bloques de código con triple backtick
        const codeBlockRegex = /```([a-zA-Z]*)\n([\s\S]*?)```/g;
        
        // Reemplazar bloques de código con elementos <pre><code>
        let formattedMessage = message.replace(codeBlockRegex, (match, language, code) => {
            const langClass = language ? `language-${language}` : '';
            return `<pre><code class="${langClass}">${this.escapeHtml(code)}</code></pre>`;
        });
        
        // Detectar código en línea con backtick simple
        const inlineCodeRegex = /`([^`]+)`/g;
        formattedMessage = formattedMessage.replace(inlineCodeRegex, '<code>$1</code>');
        
        return formattedMessage;
    },
    
    /**
     * Escapa caracteres HTML para mostrar código correctamente
     * @param {string} html - Texto a escapar
     * @return {string} - Texto con caracteres HTML escapados
     */
    escapeHtml: function(html) {
        const escapeMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return html.replace(/[&<>"']/g, function(m) {
            return escapeMap[m];
        });
    },
    
    /**
     * Aplica resaltado de sintaxis a los bloques de código
     */
    highlightAll: function() {
        // Si se usa una biblioteca como Prism.js o highlight.js
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        } else if (typeof hljs !== 'undefined') {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
        }
    }
};
/**
 * Utilidades para formatear y manejar código en bloques de código
 */
class CodeFormatter {
  /**
   * Inicializa el formateador de código
   */
  constructor() {
    this.initCodeBlocks();
  }

  /**
   * Inicializa todos los bloques de código en la página
   */
  initCodeBlocks() {
    document.querySelectorAll('pre code').forEach((block) => {
      this.setupCodeBlock(block);
    });
  }

  /**
   * Configura un bloque de código con opciones de copia
   * @param {HTMLElement} block - El elemento de código
   */
  setupCodeBlock(block) {
    const container = block.parentNode;
    if (!container.classList.contains('code-block-processed')) {
      // Crear contenedor para el bloque de código con encabezado
      const codeBlock = document.createElement('div');
      codeBlock.className = 'code-block';
      
      // Crear encabezado para el bloque de código
      const header = document.createElement('div');
      header.className = 'code-block-header';
      
      // Detectar lenguaje de programación
      let language = 'código';
      const classList = block.classList;
      if (classList.length > 0) {
        for (let i = 0; i < classList.length; i++) {
          if (classList[i].startsWith('language-')) {
            language = classList[i].replace('language-', '');
            break;
          }
        }
      }
      
      // Añadir lenguaje al encabezado
      const langLabel = document.createElement('span');
      langLabel.className = 'code-language';
      langLabel.textContent = language;
      
      // Añadir botones de acción
      const actions = document.createElement('div');
      actions.className = 'code-actions';
      
      // Botón de copiar
      const copyButton = document.createElement('button');
      copyButton.className = 'btn-copy';
      copyButton.innerHTML = '<i class="bi bi-clipboard"></i>';
      copyButton.title = 'Copiar al portapapeles';
      copyButton.onclick = () => this.copyToClipboard(block.textContent);
      
      // Estructurar componentes
      actions.appendChild(copyButton);
      header.appendChild(langLabel);
      header.appendChild(actions);
      
      // Crear contenedor para el código
      const codeContent = document.createElement('div');
      codeContent.className = 'code-content';
      codeContent.appendChild(block.cloneNode(true));
      
      // Armar el bloque completo
      codeBlock.appendChild(header);
      codeBlock.appendChild(codeContent);
      
      // Reemplazar el bloque original
      container.innerHTML = '';
      container.appendChild(codeBlock);
      container.classList.add('code-block-processed');
    }
  }

  /**
   * Copia el texto al portapapeles
   * @param {string} text - El texto a copiar
   */
  copyToClipboard(text) {
    navigator.clipboard.writeText(text)
      .then(() => {
        this.showCopyNotification('Código copiado al portapapeles');
      })
      .catch(err => {
        console.error('Error al copiar: ', err);
        this.showCopyNotification('Error al copiar', true);
      });
  }

  /**
   * Muestra una notificación de copia
   * @param {string} message - El mensaje a mostrar
   * @param {boolean} isError - Indica si es un error
   */
  showCopyNotification(message, isError = false) {
    const notification = document.createElement('div');
    notification.className = `copy-notification ${isError ? 'error' : 'success'}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Animar salida y eliminar
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 2000);
  }
}

// Inicializar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
  window.codeFormatter = new CodeFormatter();
});

// Exponer la función de copia globalmente para que pueda ser usada por botones
window.copyCodeToClipboard = function(element) {
  const codeBlock = element.closest('.code-block').querySelector('code');
  if (codeBlock) {
    window.codeFormatter.copyToClipboard(codeBlock.textContent);
  }
};
