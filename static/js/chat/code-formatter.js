
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
