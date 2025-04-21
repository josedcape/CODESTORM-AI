// CODESTORM - Sistema de chat con agentes especializados y funcionalidades avanzadas

// Función principal para inicializar el chat
function initializeChat() {
  const chatContainer = document.getElementById('chat-container');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const agentSelector = document.getElementById('agent-selector');
  
  // Cargar los agentes en el selector
  loadAgentSelector();
  
  // Evento para enviar mensaje y autoajustar altura
  chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (message) {
      sendMessage(message);
      chatInput.value = '';
      // Restablecer altura después de enviar
      chatInput.style.height = 'auto';
    }
  });
  
  // Autoajustar altura del textarea al escribir
  chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
  });
  
  // Evento para cambiar de agente
  agentSelector.addEventListener('change', function() {
    const selectedAgentId = agentSelector.value;
    setActiveAgent(selectedAgentId);
  });
  
  // Inicializar detección de comandos de creación de páginas
  initCreationCommandDetection();
}

// Cargar los agentes en el selector
function loadAgentSelector() {
  const agentSelector = document.getElementById('agent-selector');
  if (!agentSelector) return; // Prevenir errores si el elemento no existe
  
  // Limpiar el selector actual
  agentSelector.innerHTML = '';
  
  // Verificar que SPECIALIZED_AGENTS está disponible
  if (typeof window.SPECIALIZED_AGENTS === 'undefined') {
    console.error("Error: SPECIALIZED_AGENTS no está definido");
    // Usar agentes predefinidos básicos si no están disponibles
    window.SPECIALIZED_AGENTS = {
      developer: {
        id: 'developer',
        name: 'Agente de Desarrollo',
        icon: 'bi-code-slash',
        description: 'Experto en optimización y edición de código en tiempo real',
        capabilities: ['Corrección de código', 'Optimización', 'Desarrollo']
      },
      architect: {
        id: 'architect',
        name: 'Agente de Arquitectura',
        icon: 'bi-diagram-3',
        description: 'Diseñador de arquitecturas escalables',
        capabilities: ['Diseño de sistemas', 'Planificación', 'Estructura']
      }
    };
  }
  
  // Crear opciones HTML directamente para mejor rendimiento
  let optionsHTML = '';
  
  // Opción por defecto (Developer)
  optionsHTML += `<option value="developer" selected>Agente de Desarrollo</option>`;
  
  // Añadir el resto de agentes
  for (const agentId in window.SPECIALIZED_AGENTS) {
    if (agentId !== 'developer') {
      const agent = window.SPECIALIZED_AGENTS[agentId];
      optionsHTML += `<option value="${agentId}">${agent.name}</option>`;
    }
  }
  
  // Insertar todas las opciones de una vez (mejor rendimiento)
  agentSelector.innerHTML = optionsHTML;
}

// Establecer el agente activo
function setActiveAgent(agentId) {
  // Asegurarse de que SPECIALIZED_AGENTS está definido
  if (typeof window.SPECIALIZED_AGENTS === 'undefined') {
    console.error("Error: SPECIALIZED_AGENTS no está definido");
    return;
  }
  
  // Obtener el agente seleccionado o usar el agente desarrollador por defecto
  window.app = window.app || {};
  window.app.activeAgent = window.SPECIALIZED_AGENTS[agentId] || window.SPECIALIZED_AGENTS.developer;
  
  // Actualizar el valor del selector
  const agentSelector = document.getElementById('agent-selector');
  if (agentSelector) {
    agentSelector.value = agentId;
  }
  
  // Actualizar la descripción del agente
  updateAgentDescription(window.app.activeAgent);
  
  // Actualizar el icono del avatar
  updateAgentAvatar(window.app.activeAgent);
  
  // Añadir mensaje informativo al chat
  addSystemMessage(`Has cambiado al <strong>${window.app.activeAgent.name}</strong>. Este agente se especializa en: ${window.app.activeAgent.description}.`);
}

// Actualizar el avatar del agente
function updateAgentAvatar(agent) {
  const agentAvatar = document.querySelector('.agent-avatar i');
  if (agentAvatar) {
    agentAvatar.className = `bi ${agent.icon}`;
  }
}

// Actualizar la descripción del agente
function updateAgentDescription(agent) {
  const agentDescription = document.getElementById('agent-description');
  const agentCapabilities = document.getElementById('agent-capabilities');
  const agentTitle = document.querySelector('.agent-details h5');
  
  if (agentDescription && agentCapabilities) {
    agentDescription.textContent = agent.description;
    if (agentTitle) {
      agentTitle.textContent = agent.name;
    }
    
    // Mostrar capacidades
    agentCapabilities.innerHTML = '';
    agent.capabilities.forEach(capability => {
      const li = document.createElement('li');
      li.textContent = capability;
      agentCapabilities.appendChild(li);
    });
  }
}

// Inicializar detección de comandos de creación
function initCreationCommandDetection() {
  // Patrones para detectar comandos de creación
  window.app.creationPatterns = {
    page: /crea(r)?\s+(una)?\s+p[áa]gina|genera(r)?\s+(una)?\s+p[áa]gina/i,
    component: /crea(r)?\s+(un)?\s+componente|genera(r)?\s+(un)?\s+componente/i,
    form: /crea(r)?\s+(un)?\s+formulario|genera(r)?\s+(un)?\s+formulario/i
  };
}

// Enviar mensaje al backend - Versión mejorada con sistema multi-agente
function sendMessage(message) {
  // Verificar si es un comando de creación
  if (handleCreationCommand(message)) {
    return; // Si se manejó como comando de creación, no enviamos al backend
  }
  
  // Añadir mensaje del usuario al chat
  addUserMessage(message);
  
  // Verificar si es un comando para modificar archivos o ejecutar comandos en lenguaje natural
  if (window.naturalCommandProcessor) {
    const parsedRequest = window.naturalCommandProcessor.processRequest(message);
    if (parsedRequest.success) {
      // Es un comando para manipular archivos o ejecutar comandos
      // Mostrar indicador de carga
      addLoadingMessage();
      
      // Procesar la solicitud mediante el API de lenguaje natural en el backend
      fetch('/api/natural_language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: message
        }),
      })
      .then(response => response.json())
      .then(data => {
        // Remover indicador de carga
        removeLoadingMessage();
        
        // Obtener el agente activo
        const activeAgent = window.app.activeAgent || window.SPECIALIZED_AGENTS.developer;
        
        if (data.success) {
          // La acción fue exitosa, mostrar el resultado
          let resultMessage = data.message || 'Acción completada correctamente';
          
          // Si hay contenido de archivo o salida de comando, agregarla
          if (data.content) {
            resultMessage += '\n\n```' + (data.file_type || '') + '\n' + data.content + '\n```';
          }
          
          if (data.stdout) {
            resultMessage += '\n\n```bash\n# Salida del comando:\n' + data.stdout + '\n```';
          }
          
          if (data.stderr && data.stderr.trim()) {
            resultMessage += '\n\n```bash\n# Errores:\n' + data.stderr + '\n```';
          }
          
          // Agregar respuesta del agente
          addAgentMessage(resultMessage, activeAgent);
        } else {
          // Hubo un error en la acción
          addAgentMessage('No pude completar esa acción: ' + data.message, activeAgent);
        }
      })
      .catch(error => {
        console.error('Error al procesar lenguaje natural:', error);
        removeLoadingMessage();
        addSystemMessage('Error de conexión. Por favor, inténtalo de nuevo.');
      });
      
      return; // Terminamos aquí porque ya procesamos el comando
    }
  }
  
  // Obtener el agente activo
  const activeAgent = window.app.activeAgent || window.SPECIALIZED_AGENTS.developer;
  const agentId = activeAgent.id || 'developer';
  
  // Mostrar indicador de carga con estilo futurista
  addLoadingMessage();
  
  // Determinar si estamos en modo colaborativo
  const collaborativeMode = true; // Activar por defecto
  
  // Enviar al backend con el modelo seleccionado
  const modelSelect = document.getElementById('model-select');
  const selectedModel = modelSelect ? modelSelect.value : 'openai';
  
  // Obtener el contexto de la conversación reciente (últimos 5 mensajes)
  let conversationContext = [];
  const chatMessages = document.querySelectorAll('.chat-message');
  let contextCount = 0;
  
  // Reunir los últimos mensajes como contexto, hasta un máximo de 5
  for (let i = chatMessages.length - 2; i >= 0 && contextCount < 5; i--) { // -2 para ignorar el mensaje actual
    const msg = chatMessages[i];
    const role = msg.classList.contains('user-message') ? 'user' : 
                 msg.classList.contains('system-message') ? 'system' : 'assistant';
    const content = msg.querySelector('.message-content').textContent;
    
    // Añadir al inicio para mantener el orden cronológico
    conversationContext.unshift({
      role: role,
      content: content
    });
    
    contextCount++;
  }
  
  console.log("Enviando mensaje al backend:", {
    message: message,
    agent_id: agentId,
    context: conversationContext,
    model: selectedModel,
    collaborative_mode: collaborativeMode
  });
  
  // Enviar al backend con información completa
  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      agent_id: agentId,
      context: conversationContext,
      model: selectedModel,
      collaborative_mode: collaborativeMode
    }),
  })
  .then(response => response.json())
  .then(data => {
    // Remover indicador de carga
    removeLoadingMessage();
    
    if (data.error) {
      addSystemMessage(`Error: ${data.error}`);
      return;
    }
    
    // Mostrar la respuesta del agente
    addAgentMessage(data.response, activeAgent);
    
    // Procesar recomendaciones de agentes si las hay
    if (data.response.includes('**Nota:** Para esta consulta, también podrías consultar a:')) {
      const recommendationSection = data.response.split('**Nota:** Para esta consulta, también podrías consultar a:')[1];
      // Extraer recomendaciones de agentes
      const agentRecommendations = recommendationSection.match(/- El (.*?), para obtener/g);
      
      if (agentRecommendations && agentRecommendations.length > 0) {
        // Añadir opciones para cambiar de agente
        const agentOptions = agentRecommendations.map(rec => {
          const agentName = rec.match(/- El (.*?),/)[1];
          let agentId = '';
          
          // Mapear nombres a IDs
          if (agentName.includes('Desarrollo')) agentId = 'developer';
          else if (agentName.includes('Arquitectura')) agentId = 'architect';
          else if (agentName.includes('Avanzado')) agentId = 'advanced';
          
          return { id: agentId, name: agentName };
        });
        
        // Mostrar opciones de cambio como botones
        let agentButtonsHTML = '<div class="agent-recommendations mt-2">';
        agentButtonsHTML += '<p class="text-muted small">¿Quieres cambiar de agente para esta consulta?</p>';
        
        agentOptions.forEach(agent => {
          agentButtonsHTML += `<button class="btn btn-sm btn-outline-primary me-2 mt-1 switch-agent-btn" data-agent-id="${agent.id}">
            Cambiar a ${agent.name}
          </button>`;
        });
        
        agentButtonsHTML += '</div>';
        
        // Añadir botones al último mensaje del agente
        const lastAgentMessage = document.querySelector('.chat-message.agent-message:last-child .message-content');
        if (lastAgentMessage) {
          lastAgentMessage.insertAdjacentHTML('beforeend', agentButtonsHTML);
          
          // Añadir event listeners a los botones
          document.querySelectorAll('.switch-agent-btn').forEach(btn => {
            btn.addEventListener('click', function() {
              const newAgentId = this.getAttribute('data-agent-id');
              if (newAgentId) {
                setActiveAgent(newAgentId);
                addSystemMessage(`Has cambiado al ${window.SPECIALIZED_AGENTS[newAgentId].name}. Puedes repetir tu consulta para obtener su perspectiva.`);
              }
            });
          });
        }
      }
    }
    
    // Detectar y procesar código HTML dentro de la respuesta
    processHtmlCodeForPreview(data.response);
  })
  .catch(error => {
    console.error('Error:', error);
    removeLoadingMessage();
    addSystemMessage('Error de conexión. Por favor, verifica tu conexión e intenta de nuevo.');
  });
}

// Manejar comandos de creación
function handleCreationCommand(message) {
  const lowerMsg = message.toLowerCase();
  
  // Verificar si es un comando para crear una página
  if (window.app.creationPatterns.page.test(lowerMsg)) {
    
    // Si el mensaje es muy genérico, solicitar más información
    if (message.length < 30 || !lowerMsg.includes('para')) {
      addUserMessage(message);
      
      // Agregar sugerencias específicas basadas en el tipo de comando
      const questions = [
        "¿Para qué tipo de producto o servicio necesitas la página?",
        "¿Puedes proporcionar detalles específicos sobre el diseño y contenido que deseas incluir?",
        "¿Qué secciones específicas necesitas en esta página (por ejemplo: header, galería, testimonios, formulario de contacto)?",
        "¿Tienes preferencias de estilo o paleta de colores para esta página?"
      ];
      
      // Seleccionar una pregunta aleatoria
      const randomIndex = Math.floor(Math.random() * questions.length);
      const randomQuestion = questions[randomIndex];
      
      removeLoadingMessage();
      addAgentMessage(`Para crear la página que necesitas, necesito más detalles. ${randomQuestion}`, window.app.activeAgent);
      
      return true; // Comando manejado
    }
  } 
  // Verificar si es un comando para crear un componente
  else if (window.app.creationPatterns.component.test(lowerMsg)) {
    if (message.length < 25) {
      addUserMessage(message);
      
      const questions = [
        "¿Qué tipo de componente necesitas exactamente (navbar, card, slider, galería)?",
        "¿Puedes describir la funcionalidad específica que debería tener este componente?",
        "¿Cómo debería integrarse este componente con el resto de tu página?"
      ];
      
      const randomIndex = Math.floor(Math.random() * questions.length);
      const randomQuestion = questions[randomIndex];
      
      removeLoadingMessage();
      addAgentMessage(`Para crear el componente adecuado, necesito más información. ${randomQuestion}`, window.app.activeAgent);
      
      return true; // Comando manejado
    }
  }
  // Verificar si es un comando para crear un formulario
  else if (window.app.creationPatterns.form.test(lowerMsg)) {
    if (message.length < 20) {
      addUserMessage(message);
      
      const questions = [
        "¿Qué tipo de datos necesitas recopilar con este formulario?",
        "¿Necesitas funcionalidades específicas como validación de datos o integración con algún servicio?",
        "¿Es un formulario de contacto, registro, pedido u otro tipo?"
      ];
      
      const randomIndex = Math.floor(Math.random() * questions.length);
      const randomQuestion = questions[randomIndex];
      
      removeLoadingMessage();
      addAgentMessage(`Para diseñar el formulario adecuado, necesito más detalles. ${randomQuestion}`, window.app.activeAgent);
      
      return true; // Comando manejado
    }
  }
  
  return false; // No se manejó como comando especial
}

// Procesar código HTML para previsualización
function processHtmlCodeForPreview(text) {
  // Buscar bloques de código HTML
  const htmlRegex = /```html([\s\S]*?)```/g;
  const htmlMatches = text.match(htmlRegex);
  
  if (htmlMatches && htmlMatches.length > 0) {
    // Extraer el contenido HTML del primer bloque
    const htmlContent = htmlMatches[0].replace(/```html/, '').replace(/```$/, '').trim();
    
    // Si existe contenido HTML válido, mostrar previsualización
    if (htmlContent && htmlContent.includes('<html') || htmlContent.includes('<body') || htmlContent.includes('<div')) {
      // Mejorar el HTML añadiendo referencias necesarias y estilos
      const enhancedHtml = enhanceHtmlForPreview(htmlContent);
      
      // Mostrar en el iframe de previsualización
      if (typeof window.showPreview === 'function') {
        window.showPreview(enhancedHtml);
        
        // Añadir botón para ver en diferentes dispositivos en el mensaje
        const lastMessage = document.querySelector('.chat-message.agent-message:last-child .message-content');
        if (lastMessage) {
          const previewButtonsHtml = `
            <div class="preview-actions mt-3">
              <button class="btn btn-sm btn-futuristic" onclick="document.getElementById('preview-section').scrollIntoView({behavior: 'smooth'})">
                <i class="bi bi-eye"></i> Ver previsualización
              </button>
            </div>`;
          
          lastMessage.insertAdjacentHTML('beforeend', previewButtonsHtml);
        }
      }
    }
  }
}

// Mejorar el HTML para previsualización
function enhanceHtmlForPreview(htmlContent) {
  // Verificar si el HTML tiene las etiquetas básicas
  const hasHtmlTag = htmlContent.includes('<html');
  const hasHeadTag = htmlContent.includes('<head');
  const hasBodyTag = htmlContent.includes('<body');
  
  // Contenido básico para cabecera si no existe
  let headContent = `
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <title>Previsualización</title>
    <style>
      /* Estilos básicos para la previsualización */
      body {
        font-family: 'Sora', sans-serif;
        line-height: 1.6;
      }
      .responsive-img {
        max-width: 100%;
        height: auto;
      }
      .card {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
      }
      .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
      }
    </style>`;
  
  // Construir el HTML mejorado
  let enhancedHtml = '';
  
  if (!hasHtmlTag) {
    enhancedHtml += '<!DOCTYPE html>\n<html lang="es">\n';
    
    if (!hasHeadTag) {
      enhancedHtml += '<head>' + headContent + '</head>\n';
    }
    
    if (!hasBodyTag) {
      enhancedHtml += '<body>\n' + htmlContent + '\n</body>\n';
    } else {
      enhancedHtml += htmlContent;
    }
    
    enhancedHtml += '</html>';
  } else {
    // Si ya tiene etiqueta HTML pero no head, insertarla
    if (!hasHeadTag) {
      enhancedHtml = htmlContent.replace('<html', '<html lang="es"').replace('>', '>\n<head>' + headContent + '</head>');
    } else {
      // Si tiene head, añadir solo los estilos
      enhancedHtml = htmlContent.replace('</head>', headContent + '</head>');
    }
  }
  
  return enhancedHtml;
}

// Añadir mensaje del usuario al chat con estilo futurista
function addUserMessage(message) {
  const chatMessages = document.getElementById('chat-messages');
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message user-message';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = `<p>${escapeHtml(message)}</p>`;
  
  const messageInfo = document.createElement('div');
  messageInfo.className = 'message-info';
  messageInfo.innerHTML = `<span class="message-time">${getCurrentTime()}</span>
                           <span class="message-user">Tú</span>`;
  
  messageElement.appendChild(messageContent);
  messageElement.appendChild(messageInfo);
  
  chatMessages.appendChild(messageElement);
  scrollToBottom(chatMessages);
}

// Añadir mensaje del agente al chat con estilo futurista
function addAgentMessage(message, agent) {
  const chatMessages = document.getElementById('chat-messages');
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message agent-message';
  
  // Convertir Markdown a HTML con resaltado de sintaxis mejorado
  const formattedMessage = formatMarkdown(message);
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = formattedMessage;
  
  const messageInfo = document.createElement('div');
  messageInfo.className = 'message-info';
  messageInfo.innerHTML = `<span class="message-time">${getCurrentTime()}</span>
                           <span class="message-agent"><i class="bi ${agent.icon}"></i> ${agent.name}</span>
                           <button class="copy-btn" onclick="copyMessageToClipboard(this)">
                             <i class="bi bi-clipboard"></i>
                           </button>`;
  
  messageElement.appendChild(messageContent);
  messageElement.appendChild(messageInfo);
  
  chatMessages.appendChild(messageElement);
  scrollToBottom(chatMessages);
  
  // Inicializar resaltado de sintaxis mejorado
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
    
    // Añadir botones para copiar código
    const codeContainer = block.parentNode;
    const codeLanguage = block.className.replace('language-', '');
    
    // Crear un contenedor para el encabezado del código
    const codeHeader = document.createElement('div');
    codeHeader.className = 'code-header';
    codeHeader.innerHTML = `
      <span>${codeLanguage}</span>
      <div class="code-actions">
        <button class="code-action-btn" onclick="copyCode(this)">
          <i class="bi bi-clipboard"></i> Copiar
        </button>
      </div>
    `;
    
    // Convertir pre en un código con encabezado
    codeContainer.classList.add('code-block');
    codeContainer.parentNode.insertBefore(codeHeader, codeContainer);
  });
}

// Copiar código al portapapeles
function copyCode(button) {
  const codeBlock = button.closest('.code-header').nextElementSibling.querySelector('code');
  const codeText = codeBlock.textContent;
  
  navigator.clipboard.writeText(codeText)
    .then(() => {
      // Cambiar ícono y texto temporalmente para indicar éxito
      const icon = button.querySelector('i');
      icon.className = 'bi bi-clipboard-check';
      button.innerHTML = '<i class="bi bi-clipboard-check"></i> Copiado';
      
      setTimeout(() => {
        icon.className = 'bi bi-clipboard';
        button.innerHTML = '<i class="bi bi-clipboard"></i> Copiar';
      }, 2000);
    })
    .catch(err => {
      console.error('Error al copiar código: ', err);
    });
}

// Añadir mensaje del sistema al chat
function addSystemMessage(message) {
  const chatMessages = document.getElementById('chat-messages');
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message system-message';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = `<p>${message}</p>`;
  
  messageElement.appendChild(messageContent);
  
  chatMessages.appendChild(messageElement);
  scrollToBottom(chatMessages);
}

// Añadir mensaje de carga al chat con estilo futurista
function addLoadingMessage() {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) {
    console.error("No se encontró el contenedor de mensajes");
    return;
  }
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message agent-message loading-message';
  messageElement.id = 'loading-message';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = `<div class="loading-indicator">
                                <div class="loading-dots">
                                  <span></span><span></span><span></span>
                                </div>
                              </div>`;
  
  messageElement.appendChild(messageContent);
  
  chatMessages.appendChild(messageElement);
  scrollToBottom(chatMessages);
}

// Remover mensaje de carga
function removeLoadingMessage() {
  const loadingMessage = document.getElementById('loading-message');
  if (loadingMessage) {
    loadingMessage.remove();
  } else {
    // Si no se encuentra por ID, buscar por clase
    const loadingMessages = document.querySelectorAll('.chat-message.agent-message.loading-message');
    loadingMessages.forEach(msg => msg.remove());
  }
}

// Formatear markdown y resaltar código con mejoras
function formatMarkdown(text) {
  // Convertir código en bloques con mejoras para la UI
  text = text.replace(/```(\w*)([\s\S]*?)```/g, function(match, language, code) {
    language = language || 'plaintext';
    return `<pre><code class="language-${language}">${escapeHtml(code.trim())}</code></pre>`;
  });
  
  // Código en línea
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Encabezados
  text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
  
  // Énfasis (negrita, cursiva)
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Listas
  text = text.replace(/^\s*- (.*$)/gm, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>\n)+/g, '<ul>$&</ul>');
  
  // Listas numeradas
  text = text.replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>\n)+/g, '<ol>$&</ol>');
  
  // Enlaces
  text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="link-accent">$1</a>');
  
  // Tablas (soporte básico)
  if (text.includes('|')) {
    const lines = text.split('\n');
    let inTable = false;
    let tableLines = [];
    let processedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.trim().startsWith('|') && line.includes('|')) {
        if (!inTable) {
          inTable = true;
          tableLines = [];
        }
        tableLines.push(line);
      } else if (inTable) {
        inTable = false;
        if (tableLines.length >= 2) {
          const tableHTML = convertTableToHTML(tableLines);
          processedLines.push(tableHTML);
        } else {
          processedLines = processedLines.concat(tableLines);
        }
        processedLines.push(line);
      } else {
        processedLines.push(line);
      }
    }
    
    // Manejar tabla al final del texto
    if (inTable && tableLines.length >= 2) {
      const tableHTML = convertTableToHTML(tableLines);
      processedLines.push(tableHTML);
    }
    
    text = processedLines.join('\n');
  }
  
  // Párrafos (asegurarse de que el contenido no dentro de otras etiquetas esté en párrafos)
  text = text.replace(/^(?!<[a-z]).+/gm, function(match) {
    if (match.trim().length === 0) return match;
    return `<p>${match}</p>`;
  });
  
  return text;
}

// Convertir tabla Markdown a HTML
function convertTableToHTML(tableLines) {
  // Eliminar líneas de separación (---)
  const filteredLines = tableLines.filter(line => !line.match(/^\s*\|[\s\-\|]*\|\s*$/));
  
  let tableHTML = '<div class="table-responsive"><table class="table table-dark table-striped">';
  let isHeader = true;
  
  filteredLines.forEach(line => {
    const cells = line.split('|').slice(1, -1); // Remover primero y último vacíos
    
    if (isHeader) {
      tableHTML += '<thead><tr>';
      cells.forEach(cell => {
        tableHTML += `<th>${cell.trim()}</th>`;
      });
      tableHTML += '</tr></thead><tbody>';
      isHeader = false;
    } else {
      tableHTML += '<tr>';
      cells.forEach(cell => {
        tableHTML += `<td>${cell.trim()}</td>`;
      });
      tableHTML += '</tr>';
    }
  });
  
  tableHTML += '</tbody></table></div>';
  return tableHTML;
}

// Copiar mensaje al portapapeles con notificación mejorada
function copyMessageToClipboard(button) {
  const messageElement = button.closest('.chat-message.agent-message');
  const content = messageElement.querySelector('.message-content').textContent;
  
  navigator.clipboard.writeText(content)
    .then(() => {
      // Cambiar ícono temporalmente para indicar éxito
      const icon = button.querySelector('i');
      icon.className = 'bi bi-clipboard-check';
      
      // Mostrar notificación flotante
      const notification = document.createElement('div');
      notification.className = 'position-fixed top-0 end-0 p-3';
      notification.style.zIndex = '5000';
      notification.innerHTML = `
        <div class="toast show bg-success text-white" role="alert">
          <div class="toast-header bg-success text-white">
            <i class="bi bi-check-circle me-2"></i>
            <strong class="me-auto">Éxito</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
          </div>
          <div class="toast-body">
            Contenido copiado al portapapeles
          </div>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        icon.className = 'bi bi-clipboard';
        notification.remove();
      }, 2000);
    })
    .catch(err => {
      console.error('Error al copiar: ', err);
    });
}

// Obtener hora actual formateada
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Desplazarse al fondo del contenedor de mensajes con animación
function scrollToBottom(container) {
  container.scrollTo({
    top: container.scrollHeight,
    behavior: 'smooth'
  });
}

// Escapar HTML para evitar inyección de código
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Exponer funciones necesarias globalmente
window.copyMessageToClipboard = copyMessageToClipboard;
window.copyCode = copyCode;
window.app = window.app || {};
window.app.chat = {
  initialize: initializeChat,
  sendMessage: sendMessage,
  setActiveAgent: setActiveAgent,
  handleCreationCommand: handleCreationCommand
};