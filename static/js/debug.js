
/**
 * Script de diagnóstico para detectar problemas de comunicación en el chat
 */

console.log('Script de diagnóstico cargado');

// Función para detectar errores de sintaxis comunes
window.detectSyntaxErrors = function(script) {
  try {
    // Intentar compilar el script para detectar errores de sintaxis
    new Function(script);
    return { success: true };
  } catch (e) {
    console.error('Error de sintaxis detectado:', e);
    return { 
      success: false, 
      error: e.message,
      line: e.lineNumber,
      column: e.columnNumber
    };
  }
};

// Verificar estructura de window.app
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM cargado, iniciando diagnóstico');
  
  // Verificar estructura global
  console.log('Estructura de window.app:', window.app);
  
  // Verificar endpoints
  if (window.app && window.app.apiEndpoints) {
    console.log('API Endpoints disponibles:', window.app.apiEndpoints);
  } else {
    console.error('ERROR: API Endpoints no disponibles');
  }
  
  // Verificar chat
  if (window.app && window.app.chat) {
    console.log('Objeto chat disponible:', window.app.chat);
  } else {
    console.error('ERROR: Objeto chat no disponible');
  }
  
  // Probar comunicación con el servidor
  fetch('/api/health')
    .then(response => response.json())
    .then(data => {
      console.log('Estado del servidor:', data);
    })
    .catch(error => {
      console.error('Error al conectar con el servidor:', error);
    });
    
  // Monitorear envío de mensajes
  const originalFetch = window.fetch;
  window.fetch = function(url, options) {
    console.log('Interceptado fetch a:', url, options);
    return originalFetch.apply(this, arguments)
      .then(response => {
        console.log('Respuesta recibida:', response.status);
        return response;
      })
      .catch(error => {
        console.error('Error en fetch:', error);
        throw error;
      });
  };
});

// Función para probar el envío de mensajes directamente
window.testChatMessage = function(message) {
  console.log('Probando envío de mensaje:', message);
  
  const testData = {
    message: message || 'Mensaje de prueba desde diagnóstico',
    agent_id: 'general',
    model: 'openai',
    context: []
  };
  
  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(testData)
  })
  .then(response => {
    console.log('Estado de respuesta:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Datos de respuesta:', data);
  })
  .catch(error => {
    console.error('Error en prueba de chat:', error);
  });
};
