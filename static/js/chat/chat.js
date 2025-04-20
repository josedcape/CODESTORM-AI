// CODESTORM - Sistema de chat con agentes especializados

// Función principal para inicializar el chat
function initializeChat() {
  const chatContainer = document.getElementById('chat-container');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const agentSelector = document.getElementById('agent-selector');
  
  // Cargar los agentes en el selector
  loadAgentSelector();
  
  // Evento para enviar mensaje
  chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (message) {
      sendMessage(message);
      chatInput.value = '';
    }
  });
  
  // Evento para cambiar de agente
  agentSelector.addEventListener('change', function() {
    const selectedAgentId = agentSelector.value;
    setActiveAgent(selectedAgentId);
  });
}

// Cargar los agentes en el selector
function loadAgentSelector() {
  const agentSelector = document.getElementById('agent-selector');
  agentSelector.innerHTML = '';
  
  // Opción por defecto (Developer)
  const defaultOption = document.createElement('option');
  defaultOption.value = 'developer';
  defaultOption.textContent = 'Agente de Desarrollo';
  defaultOption.selected = true;
  agentSelector.appendChild(defaultOption);
  
  // Añadir el resto de agentes
  Object.values(SPECIALIZED_AGENTS).forEach(agent => {
    if (agent.id !== 'developer') {
      const option = document.createElement('option');
      option.value = agent.id;
      option.textContent = agent.name;
      agentSelector.appendChild(option);
    }
  });
}

// Establecer el agente activo
function setActiveAgent(agentId) {
  window.app.activeAgent = SPECIALIZED_AGENTS[agentId] || SPECIALIZED_AGENTS.developer;
  
  // Actualizar la descripción del agente
  updateAgentDescription(window.app.activeAgent);
  
  // Añadir mensaje informativo al chat
  addSystemMessage(`Has cambiado al <strong>${window.app.activeAgent.name}</strong>. Este agente se especializa en: ${window.app.activeAgent.description}.`);
}

// Actualizar la descripción del agente
function updateAgentDescription(agent) {
  const agentDescription = document.getElementById('agent-description');
  const agentCapabilities = document.getElementById('agent-capabilities');
  
  if (agentDescription && agentCapabilities) {
    agentDescription.textContent = agent.description;
    
    // Mostrar capacidades
    agentCapabilities.innerHTML = '';
    agent.capabilities.forEach(capability => {
      const li = document.createElement('li');
      li.textContent = capability;
      agentCapabilities.appendChild(li);
    });
  }
}

// Enviar mensaje al backend
function sendMessage(message) {
  // Añadir mensaje del usuario al chat
  addUserMessage(message);
  
  // Obtener el agente activo
  const activeAgent = window.app.activeAgent || SPECIALIZED_AGENTS.developer;
  
  // Mostrar indicador de carga
  addLoadingMessage();
  
  // Enviar al backend con el modelo seleccionado
  const modelSelect = document.getElementById('model-select');
  const selectedModel = modelSelect ? modelSelect.value : 'openai';
  
  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      agent_prompt: activeAgent.prompt,
      model: selectedModel
    }),
  })
  .then(response => response.json())
  .then(data => {
    // Remover indicador de carga
    removeLoadingMessage();
    
    // Añadir respuesta del agente
    if (data.response) {
      addAgentMessage(data.response, activeAgent);
    } else {
      addSystemMessage('Error al procesar la solicitud. Por favor, intenta de nuevo.');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    removeLoadingMessage();
    addSystemMessage('Error de conexión. Por favor, verifica tu conexión e intenta de nuevo.');
  });
}

// Añadir mensaje del usuario al chat
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

// Añadir mensaje del agente al chat
function addAgentMessage(message, agent) {
  const chatMessages = document.getElementById('chat-messages');
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message agent-message';
  
  // Convertir Markdown a HTML con resaltado de sintaxis
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
  
  // Inicializar resaltado de sintaxis
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
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

// Añadir mensaje de carga al chat
function addLoadingMessage() {
  const chatMessages = document.getElementById('chat-messages');
  
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message agent-message loading-message';
  messageElement.id = 'loading-message';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = `<div class="loading-indicator">
                                <span class="loading-dot"></span>
                                <span class="loading-dot"></span>
                                <span class="loading-dot"></span>
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
  }
}

// Formatear markdown y resaltar código
function formatMarkdown(text) {
  // Función simple para formatear markdown básico
  // En una implementación real, utilizaríamos una librería como marked.js
  
  // Convertir código en bloques
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
  
  // Enlaces
  text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
  
  // Párrafos (asegurarse de que el contenido no dentro de otras etiquetas esté en párrafos)
  text = text.replace(/^(?!<[a-z]).+/gm, function(match) {
    return `<p>${match}</p>`;
  });
  
  return text;
}

// Copiar mensaje al portapapeles
function copyMessageToClipboard(button) {
  const messageElement = button.closest('.chat-message');
  const content = messageElement.querySelector('.message-content').textContent;
  
  navigator.clipboard.writeText(content)
    .then(() => {
      // Cambiar ícono temporalmente para indicar éxito
      const icon = button.querySelector('i');
      icon.className = 'bi bi-clipboard-check';
      
      setTimeout(() => {
        icon.className = 'bi bi-clipboard';
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

// Desplazarse al fondo del contenedor de mensajes
function scrollToBottom(container) {
  container.scrollTop = container.scrollHeight;
}

// Escapar HTML para evitar inyección de código
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Exponer funciones necesarias globalmente
window.copyMessageToClipboard = copyMessageToClipboard;
window.app = window.app || {};
window.app.chat = {
  initialize: initializeChat,
  sendMessage: sendMessage,
  setActiveAgent: setActiveAgent
};