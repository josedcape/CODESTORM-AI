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
        <button class="btn btn-sm btn-dark code-copy-btn" onclick="copyCode(this)">
          <i class="bi bi-clipboard"></i>
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
  const preElement = button.closest('.code-block-container').querySelector('pre');
  const codeElement = preElement.querySelector('code');
  const textToCopy = codeElement.textContent;

  navigator.clipboard.writeText(textToCopy).then(() => {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check"></i>';
    button.style.backgroundColor = '#28a745';

    setTimeout(() => {
      button.innerHTML = originalText;
      button.style.backgroundColor = '';
    }, 2000);
  }).catch(err => {
    console.error('Error al copiar texto: ', err);
    button.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
    button.style.backgroundColor = '#dc3545';

    setTimeout(() => {
      button.innerHTML = '<i class="bi bi-clipboard"></i>';
      button.style.backgroundColor = '';
    }, 2000);
  });
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
