/**
 * CODESTORM - Sistema Multi-Agente Interconectado
 * Este módulo permite la coordinación entre múltiples agentes especializados
 * para trabajar juntos en tareas complejas.
 */

// Namespace global para el sistema multi-agente
window.multiAgentSystem = (function() {
    // Registro de agentes disponibles y sus capacidades
    let agents = {};
    
    // Cola de mensajes para comunicación entre agentes
    let messageQueue = [];
    
    // Estado actual de la conversación y contexto
    let conversationContext = {
        history: [],
        currentTask: null,
        activeAgents: []
    };
    
    // Peso de confianza para cada agente (0-100)
    let agentConfidence = {};
    
    // Umbrales de confianza para derivación a otros agentes
    const CONFIDENCE_THRESHOLD = 70;
    
    // Eventos personalizados para comunicación
    const events = {
        MESSAGE_RECEIVED: 'agentMessageReceived',
        AGENT_ACTIVATED: 'agentActivated',
        AGENT_COMPLETED: 'agentTaskCompleted',
        CONTEXT_UPDATED: 'contextUpdated'
    };
    
    // Inicializar el sistema
    function initialize() {
        // Inicializar con los agentes predefinidos en SPECIALIZED_AGENTS
        if (window.SPECIALIZED_AGENTS) {
            for (const agentId in window.SPECIALIZED_AGENTS) {
                registerAgent(
                    agentId,
                    window.SPECIALIZED_AGENTS[agentId].name,
                    window.SPECIALIZED_AGENTS[agentId].description,
                    window.SPECIALIZED_AGENTS[agentId].capabilities || [],
                    window.SPECIALIZED_AGENTS[agentId].icon || 'bi-robot'
                );
            }
        }
        
        // Configurar eventos personalizados
        setupEventListeners();
        
        console.log("Sistema Multi-Agente inicializado:", agents);
    }
    
    // Configurar listeners de eventos
    function setupEventListeners() {
        document.addEventListener(events.MESSAGE_RECEIVED, handleAgentMessage);
        document.addEventListener(events.AGENT_ACTIVATED, handleAgentActivation);
        document.addEventListener(events.AGENT_COMPLETED, handleAgentCompletion);
    }
    
    // Registrar un nuevo agente en el sistema
    function registerAgent(id, name, description, capabilities, icon) {
        agents[id] = {
            id: id,
            name: name,
            description: description,
            capabilities: capabilities,
            icon: icon,
            isActive: false,
            lastResponse: null
        };
        
        // Inicializar confianza
        agentConfidence[id] = 90; // Valor inicial de confianza
        
        return agents[id];
    }
    
    // Analizar mensaje y determinar el agente más adecuado
    function analyzeMessage(message) {
        // Palabras clave asociadas con cada tipo de agente
        const keywordMapping = {
            developer: [
                'código', 'programar', 'función', 'clase', 'método', 'bug', 'error',
                'depurar', 'implementar', 'refactorizar', 'optimizar', 'compilar',
                'desarrollo', 'api', 'biblioteca', 'framework', 'javascript', 'python',
                'html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'flask'
            ],
            architect: [
                'arquitectura', 'sistema', 'diseño', 'patrón', 'estructura', 'componente',
                'módulo', 'escalabilidad', 'mantenibilidad', 'microservicio', 'monolito',
                'acoplamiento', 'cohesión', 'mvc', 'mvvm', 'api', 'interfaz', 'backend',
                'frontend', 'base de datos', 'modelo', 'diagrama', 'uml'
            ],
            designer: [
                'diseño', 'ui', 'ux', 'interfaz', 'usuario', 'experiencia', 'visual', 'color',
                'layout', 'responsive', 'web', 'móvil', 'accesibilidad', 'usabilidad',
                'wireframe', 'prototipo', 'maqueta', 'estilo', 'css', 'componente', 'tema',
                'fuente', 'tipografía', 'icono', 'botón', 'formulario', 'animación'
            ]
        };
        
        // Calcular puntuación para cada agente
        const scores = {};
        const messageLower = message.toLowerCase();
        
        for (const agentId in keywordMapping) {
            scores[agentId] = 0;
            
            // Contar palabras clave presentes
            keywordMapping[agentId].forEach(keyword => {
                if (messageLower.includes(keyword)) {
                    scores[agentId] += 1;
                }
            });
            
            // Normalizar puntuación (0-100)
            const maxPossible = keywordMapping[agentId].length * 0.3; // Factor de normalización
            scores[agentId] = Math.min(100, Math.round((scores[agentId] / maxPossible) * 100));
        }
        
        // Encontrar el agente con mayor puntuación
        let bestAgent = null;
        let highestScore = 0;
        
        for (const agentId in scores) {
            if (scores[agentId] > highestScore) {
                highestScore = scores[agentId];
                bestAgent = agentId;
            }
        }
        
        // Si ningún agente alcanza un umbral mínimo, usar desarrollador como fallback
        if (highestScore < 20) {
            return {
                agentId: 'developer',
                confidence: 30, // Baja confianza
                message: "No estoy seguro de qué agente es el más adecuado para esta tarea. Usaré el Agente de Desarrollo por defecto."
            };
        }
        
        return {
            agentId: bestAgent,
            confidence: highestScore,
            scores: scores
        };
    }
    
    // Activar un agente específico
    function activateAgent(agentId, task) {
        if (!agents[agentId]) {
            console.error(`Agente ${agentId} no encontrado`);
            return false;
        }
        
        // Desactivar agentes actualmente activos
        for (const id in agents) {
            if (agents[id].isActive && id !== agentId) {
                agents[id].isActive = false;
            }
        }
        
        // Activar el nuevo agente
        agents[agentId].isActive = true;
        conversationContext.activeAgents.push(agentId);
        conversationContext.currentTask = task;
        
        // Disparar evento de activación
        const event = new CustomEvent(events.AGENT_ACTIVATED, {
            detail: {
                agentId: agentId,
                task: task,
                timestamp: new Date().toISOString()
            }
        });
        document.dispatchEvent(event);
        
        return true;
    }
    
    // Enviar mensaje al agente activo
    function sendMessageToAgent(message) {
        // Primero, analizar el mensaje para determinar el agente más adecuado
        const analysis = analyzeMessage(message);
        
        // Si no hay un agente activo, o hay uno mejor para esta tarea, activar el recomendado
        const activeAgentId = getActiveAgentId();
        if (!activeAgentId || (analysis.confidence > CONFIDENCE_THRESHOLD && activeAgentId !== analysis.agentId)) {
            activateAgent(analysis.agentId, message);
        }
        
        // Actualizar el contexto de la conversación
        conversationContext.history.push({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
        
        // Si hay un procesador natural de comandos, intentar procesarlo
        if (window.naturalCommandProcessor) {
            const parsedRequest = window.naturalCommandProcessor.processRequest(message);
            if (parsedRequest.success) {
                // Es un comando para manipular archivos o ejecutar comandos
                window.naturalCommandProcessor.executeAction(parsedRequest)
                    .then(result => {
                        // Agregar respuesta al historial
                        const response = {
                            role: 'assistant',
                            agentId: getActiveAgentId(),
                            content: result.message,
                            data: result.data,
                            timestamp: new Date().toISOString()
                        };
                        
                        conversationContext.history.push(response);
                        
                        // Disparar evento de mensaje recibido
                        const event = new CustomEvent(events.MESSAGE_RECEIVED, {
                            detail: response
                        });
                        document.dispatchEvent(event);
                    })
                    .catch(error => {
                        // Manejar error en la ejecución
                        const errorResponse = {
                            role: 'assistant',
                            agentId: getActiveAgentId(),
                            content: `Error: ${error.message}`,
                            error: true,
                            timestamp: new Date().toISOString()
                        };
                        
                        conversationContext.history.push(errorResponse);
                        
                        // Disparar evento de mensaje recibido (error)
                        const event = new CustomEvent(events.MESSAGE_RECEIVED, {
                            detail: errorResponse
                        });
                        document.dispatchEvent(event);
                    });
                
                return true;
            }
        }
        
        // Si no es un comando o no se pudo procesar, enviarlo al backend
        return sendToBackend(message, getActiveAgentId());
    }
    
    // Enviar al backend para procesamiento
    function sendToBackend(message, agentId) {
        // Asegurarse de que hay un agente activo
        if (!agentId) {
            console.error("No hay un agente activo para procesar el mensaje");
            return false;
        }
        
        // Obtener el modelo seleccionado
        const modelSelect = document.getElementById('model-select');
        const selectedModel = modelSelect ? modelSelect.value : 'openai';
        
        // Preparar prompt con contexto específico del agente
        const agentPrompt = agents[agentId].prompt || 
            `Eres un asistente especializado en ${agents[agentId].description}. Ayuda al usuario con su solicitud.`;
        
        // Enviar al backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                agent_id: agentId,
                agent_prompt: agentPrompt,
                context: conversationContext.history.slice(-5), // Últimos 5 mensajes como contexto
                model: selectedModel
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                // Actualizar el historial y la respuesta del agente
                const response = {
                    role: 'assistant',
                    agentId: agentId,
                    content: data.response,
                    timestamp: new Date().toISOString()
                };
                
                agents[agentId].lastResponse = response;
                conversationContext.history.push(response);
                
                // Disparar evento de mensaje recibido
                const event = new CustomEvent(events.MESSAGE_RECEIVED, {
                    detail: response
                });
                document.dispatchEvent(event);
                
                // Verificar si el agente ha completado la tarea
                checkTaskCompletion(data.response, agentId);
            }
        })
        .catch(error => {
            console.error('Error en la comunicación con el backend:', error);
        });
        
        return true;
    }
    
    // Verificar si la tarea ha sido completada
    function checkTaskCompletion(response, agentId) {
        // Patrones que indican completitud
        const completionPatterns = [
            /he\s+(?:completado|terminado|finalizado|concluido)/i,
            /(?:tarea|solicitud)\s+(?:completada|terminada|finalizada|concluida)/i,
            /(?:listo|hecho|completo|terminado)[\.\!]/i
        ];
        
        // Verificar si algún patrón coincide
        const isCompleted = completionPatterns.some(pattern => pattern.test(response));
        
        if (isCompleted) {
            // Marcar la tarea como completada
            const event = new CustomEvent(events.AGENT_COMPLETED, {
                detail: {
                    agentId: agentId,
                    task: conversationContext.currentTask,
                    timestamp: new Date().toISOString()
                }
            });
            document.dispatchEvent(event);
        }
        
        return isCompleted;
    }
    
    // Obtener el agente activo actual
    function getActiveAgentId() {
        for (const id in agents) {
            if (agents[id].isActive) {
                return id;
            }
        }
        return null;
    }
    
    // Manejador de eventos para mensajes recibidos
    function handleAgentMessage(event) {
        const message = event.detail;
        
        // Actualizar confianza del agente basado en la calidad de respuesta
        // (esto podría mejorarse con feedback explícito del usuario)
        if (message.agentId) {
            // Mantener la confianza estable o ajustarla ligeramente
            agentConfidence[message.agentId] = Math.min(100, 
                agentConfidence[message.agentId] + (message.error ? -5 : 1));
        }
        
        // Aquí se podrían implementar más acciones como feedback automático
        
        // Si hay una interfaz UI para mostrar mensajes
        if (window.app && window.app.chat && typeof window.app.chat.addAgentMessage === 'function') {
            window.app.chat.addAgentMessage(message.content, agents[message.agentId]);
        }
    }
    
    // Manejador para activación de agentes
    function handleAgentActivation(event) {
        const { agentId } = event.detail;
        
        // Actualizar UI para mostrar el agente activo
        if (window.app && window.app.chat && typeof window.app.chat.setActiveAgent === 'function') {
            window.app.chat.setActiveAgent(agentId);
        }
    }
    
    // Manejador para completitud de tareas
    function handleAgentCompletion(event) {
        const { agentId, task } = event.detail;
        
        // Limpiar el estado de la tarea actual
        conversationContext.currentTask = null;
        
        // Agregar mensaje de sistema indicando que la tarea fue completada
        if (window.app && window.app.chat && typeof window.app.chat.addSystemMessage === 'function') {
            window.app.chat.addSystemMessage(`El ${agents[agentId].name} ha completado la tarea solicitada.`);
        }
    }
    
    // Derivar a otro agente
    function delegateToAgent(targetAgentId, reason) {
        const sourceAgentId = getActiveAgentId();
        
        if (!agents[targetAgentId]) {
            console.error(`No se puede derivar al agente ${targetAgentId} porque no existe`);
            return false;
        }
        
        // Agregar mensaje de transición
        const transitionMessage = {
            role: 'system',
            content: `${agents[sourceAgentId].name} ha derivado esta tarea a ${agents[targetAgentId].name}. Motivo: ${reason}`,
            timestamp: new Date().toISOString()
        };
        
        conversationContext.history.push(transitionMessage);
        
        // Activar el nuevo agente
        activateAgent(targetAgentId, conversationContext.currentTask);
        
        // Mostrar mensaje de transición en la UI
        if (window.app && window.app.chat && typeof window.app.chat.addSystemMessage === 'function') {
            window.app.chat.addSystemMessage(transitionMessage.content);
        }
        
        return true;
    }
    
    // Obtener recomendaciones de otros agentes
    function getRecommendationsFromAgents(query) {
        const activeAgentId = getActiveAgentId();
        const recommendations = [];
        
        // Simular consultas a otros agentes para obtener sus perspectivas
        // En una implementación real, esto podría involucrar solicitudes paralelas a cada agente
        
        for (const agentId in agents) {
            if (agentId !== activeAgentId) {
                const analysis = analyzeMessage(query);
                
                if (analysis.scores && analysis.scores[agentId] > 50) {
                    recommendations.push({
                        agentId: agentId,
                        confidence: analysis.scores[agentId],
                        message: `Recomendación del ${agents[agentId].name}: Este agente podría tener una perspectiva valiosa sobre este tema.`
                    });
                }
            }
        }
        
        return recommendations.sort((a, b) => b.confidence - a.confidence);
    }
    
    // Realizar una consulta colaborativa entre múltiples agentes
    function collaborativeQuery(query) {
        // Obtener recomendaciones
        const recommendations = getRecommendationsFromAgents(query);
        
        // Si hay recomendaciones con alta confianza, sugerir cambio de agente
        if (recommendations.length > 0 && recommendations[0].confidence > 80) {
            const topRecommendation = recommendations[0];
            
            // Sugerir el cambio al usuario
            if (window.app && window.app.chat && typeof window.app.chat.addSystemMessage === 'function') {
                window.app.chat.addSystemMessage(
                    `Sugerencia: El ${agents[topRecommendation.agentId].name} podría estar mejor equipado para ayudarte con esta consulta.`
                );
            }
        }
        
        // Proceder con el agente actual
        return sendMessageToAgent(query);
    }
    
    // Interfaz pública del módulo
    return {
        initialize: initialize,
        registerAgent: registerAgent,
        activateAgent: activateAgent,
        sendMessage: sendMessageToAgent,
        getActiveAgent: getActiveAgentId,
        delegateToAgent: delegateToAgent,
        collaborativeQuery: collaborativeQuery,
        getAgents: function() { return {...agents}; },
        getContext: function() { return {...conversationContext}; }
    };
})();