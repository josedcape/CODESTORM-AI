
// Controlador de selección de tecnologías
class TechSelector {
  constructor() {
    this.selectedTech = {
      backend: null,
      frontend: null,
      database: null,
      additionalFeatures: []
    };

    this.options = {
      backend: [
        { id: 'flask', name: 'Flask', icon: 'fa-flask', description: 'Framework web minimalista para Python' },
        { id: 'django', name: 'Django', icon: 'fa-layer-group', description: 'Framework web completo para Python con admin incorporado' },
        { id: 'fastapi', name: 'FastAPI', icon: 'fa-bolt', description: 'Framework moderno y rápido para APIs' },
        { id: 'streamlit', name: 'Streamlit', icon: 'fa-chart-line', description: 'Framework para aplicaciones de datos interactivas' },
        { id: 'node', name: 'Node.js', icon: 'fa-node-js', description: 'Entorno de ejecución para JavaScript' },
        { id: 'express', name: 'Express.js', icon: 'fa-server', description: 'Framework web para Node.js' },
        { id: 'nestjs', name: 'NestJS', icon: 'fa-feather', description: 'Framework progresivo para Node.js con TypeScript' }
      ],
      frontend: [
        { id: 'html', name: 'HTML/CSS/JS', icon: 'fa-html5', description: 'Tecnologías web básicas' },
        { id: 'bootstrap', name: 'Bootstrap', icon: 'fa-bootstrap', description: 'Framework CSS para diseño responsivo' },
        { id: 'react', name: 'React', icon: 'fa-react', description: 'Biblioteca para construir interfaces de usuario' },
        { id: 'vue', name: 'Vue.js', icon: 'fa-vuejs', description: 'Framework progresivo para interfaces' },
        { id: 'angular', name: 'Angular', icon: 'fa-angular', description: 'Framework completo para aplicaciones web' },
        { id: 'svelte', name: 'Svelte', icon: 'fa-code', description: 'Compilador con enfoque moderno' }
      ],
      database: [
        { id: 'sqlite', name: 'SQLite', icon: 'fa-database', description: 'Base de datos relacional ligera' },
        { id: 'mysql', name: 'MySQL', icon: 'fa-database', description: 'Sistema de base de datos relacional' },
        { id: 'postgresql', name: 'PostgreSQL', icon: 'fa-database', description: 'Sistema de base de datos relacional avanzado' },
        { id: 'mongodb', name: 'MongoDB', icon: 'fa-leaf', description: 'Base de datos NoSQL orientada a documentos' },
        { id: 'redis', name: 'Redis', icon: 'fa-database', description: 'Almacén de datos en memoria' }
      ],
      additionalFeatures: [
        { id: 'api', name: 'API REST', icon: 'fa-exchange-alt', description: 'Endpoints para comunicación entre servicios' },
        { id: 'auth', name: 'Autenticación', icon: 'fa-lock', description: 'Sistema de login y registro' },
        { id: 'file-upload', name: 'Subida de archivos', icon: 'fa-upload', description: 'Gestión de archivos' },
        { id: 'charts', name: 'Gráficos', icon: 'fa-chart-bar', description: 'Visualización de datos' },
        { id: 'admin', name: 'Panel Admin', icon: 'fa-user-shield', description: 'Interfaz de administración' },
        { id: 'realtime', name: 'Tiempo real', icon: 'fa-bolt', description: 'WebSockets/comunicación en tiempo real' },
        { id: 'pdf', name: 'Generación PDF', icon: 'fa-file-pdf', description: 'Crear documentos PDF' },
        { id: 'payment', name: 'Pagos', icon: 'fa-credit-card', description: 'Integración con pasarelas de pago' },
        { id: 'email', name: 'Email', icon: 'fa-envelope', description: 'Sistema de correo electrónico' },
        { id: 'map', name: 'Mapas', icon: 'fa-map-marker-alt', description: 'Integración de mapas' }
      ]
    };

    this.presetStacks = [
      { 
        name: 'Stack MERN', 
        backend: 'node', 
        frontend: 'react', 
        database: 'mongodb',
        description: 'MongoDB, Express, React y Node.js - Stack moderno de JavaScript'
      },
      { 
        name: 'Stack LAMP', 
        backend: 'flask', 
        frontend: 'bootstrap', 
        database: 'mysql',
        description: 'Clásico stack de desarrollo web: Linux, Apache, MySQL y Python'
      },
      { 
        name: 'Stack de datos', 
        backend: 'streamlit', 
        frontend: 'html', 
        database: 'postgresql',
        description: 'Ideal para análisis de datos y dashboards interactivos'
      },
      { 
        name: 'Stack empresarial', 
        backend: 'django', 
        frontend: 'angular', 
        database: 'postgresql',
        description: 'Para aplicaciones empresariales robustas y escalables'
      },
      { 
        name: 'Stack API moderno', 
        backend: 'fastapi', 
        frontend: 'vue', 
        database: 'mongodb',
        description: 'Para APIs de alto rendimiento con UI reactiva'
      }
    ];

    // Añadir estilos para notificaciones
    this.initNotificationStyles();
  }

  // Inicializar estilos para notificaciones
  initNotificationStyles() {
    if (!document.getElementById('notification-styles')) {
      const style = document.createElement('style');
      style.id = 'notification-styles';
      style.textContent = `
        .notification {
          position: fixed;
          bottom: 20px;
          right: 20px;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          display: flex;
          align-items: center;
          min-width: 300px;
          max-width: 450px;
          z-index: 9999;
          animation: slideIn 0.3s ease-out, fadeOut 0.5s ease-out 2.5s forwards;
        }
        .notification-success {
          background: #28a745;
          color: white;
        }
        .notification-info {
          background: #17a2b8;
          color: white;
        }
        .notification-warning {
          background: #ffc107;
          color: #212529;
        }
        .notification-icon {
          font-size: 24px;
          margin-right: 15px;
        }
        .notification-content p {
          margin: 0;
        }
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        @keyframes fadeOut {
          from { opacity: 1; }
          to { opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }
  }

  // Mostrar notificación
  showNotification(message, type = 'success') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-icon">
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'warning' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
      </div>
      <div class="notification-content">
        <p>${message}</p>
      </div>
    `;

    // Añadir al DOM
    document.body.appendChild(notification);

    // Eliminar después de 3 segundos
    setTimeout(() => {
      if (document.body.contains(notification)) {
        notification.remove();
      }
    }, 3000);
  }

  // Generar HTML para opciones de tecnología
  generateTechOptions(categoryName, options) {
    return options.map(option => `
      <div class="tech-option-card" data-tech-id="${option.id}" data-category="${categoryName}">
        <div class="tech-icon">
          <i class="fab ${option.icon}"></i>
        </div>
        <div class="tech-details">
          <h5>${option.name}</h5>
          <p class="tech-description">${option.description}</p>
        </div>
        <div class="tech-select">
          <div class="form-check">
            <input class="form-check-input tech-checkbox" type="radio" name="${categoryName}" id="${option.id}">
            <label class="form-check-label" for="${option.id}">
              Seleccionar
            </label>
          </div>
        </div>
      </div>
    `).join('');
  }

  // Generar HTML para características adicionales
  generateFeatureOptions(features) {
    return features.map(feature => `
      <div class="col-md-6 col-lg-4 mb-3">
        <div class="feature-card" data-feature-id="${feature.id}">
          <div class="feature-icon">
            <i class="fas ${feature.icon}"></i>
          </div>
          <div class="feature-details">
            <h6>${feature.name}</h6>
            <p class="feature-description small">${feature.description}</p>
          </div>
          <div class="feature-select">
            <div class="form-check">
              <input class="form-check-input feature-checkbox" type="checkbox" id="feature-${feature.id}">
              <label class="form-check-label" for="feature-${feature.id}"></label>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  }

  // Generar HTML para plantillas predefinidas
  generatePresetOptions(presets) {
    return presets.map((preset, index) => `
      <div class="col-md-6 mb-3">
        <div class="preset-card" data-preset-index="${index}">
          <h5>${preset.name}</h5>
          <p>${preset.description}</p>
          <div class="preset-tech-pills">
            <span class="badge bg-primary">${this.getTechName('backend', preset.backend)}</span>
            <span class="badge bg-success">${this.getTechName('frontend', preset.frontend)}</span>
            <span class="badge bg-info">${this.getTechName('database', preset.database)}</span>
          </div>
          <button class="btn btn-sm btn-outline-primary mt-2 select-preset-btn">Seleccionar</button>
        </div>
      </div>
    `).join('');
  }

  // Obtener nombre de tecnología por ID
  getTechName(category, techId) {
    const tech = this.options[category].find(t => t.id === techId);
    return tech ? tech.name : 'Desconocido';
  }

  // Método auxiliar para obtener nombre legible de categoría
  getCategoryName(category) {
    const names = {
      'backend': 'backend',
      'frontend': 'frontend',
      'database': 'base de datos'
    };
    return names[category] || category;
  }

  // Aplicar una plantilla predefinida
  applyPreset(presetIndex) {
    const preset = this.presetStacks[presetIndex];
    if (!preset) return false;

    // Seleccionar tecnologías
    this.selectTech('backend', preset.backend);
    this.selectTech('frontend', preset.frontend);
    this.selectTech('database', preset.database);

    // Mostrar notificación
    this.showNotification(`¡Stack aplicado! Has seleccionado el stack "${preset.name}".`, 'success');

    return true;
  }

  // Seleccionar una tecnología
  selectTech(category, techId) {
    this.selectedTech[category] = techId;

    // Actualizar UI
    document.querySelectorAll(`[data-category="${category}"]`).forEach(el => {
      el.classList.remove('selected');
    });

    const selectedEl = document.querySelector(`[data-category="${category}"][data-tech-id="${techId}"]`);
    if (selectedEl) {
      selectedEl.classList.add('selected');
      const radio = selectedEl.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      // Mostrar notificación
      const techName = this.getTechName(category, techId);
      this.showNotification(`Has seleccionado ${techName} como ${this.getCategoryName(category)}`, 'info');
    }

    // Actualizar resumen
    this.updateSummary();

    return true;
  }

  // Alternar una característica adicional
  toggleFeature(featureId) {
    const index = this.selectedTech.additionalFeatures.indexOf(featureId);
    const feature = this.options.additionalFeatures.find(f => f.id === featureId);
    if (!feature) return false;

    if (index === -1) {
      // Añadir la característica
      this.selectedTech.additionalFeatures.push(featureId);

      // Actualizar UI
      const featureEl = document.querySelector(`[data-feature-id="${featureId}"]`);
      if (featureEl) featureEl.classList.add('selected');

      // Marcar el checkbox
      const checkbox = document.getElementById(`feature-${featureId}`);
      if (checkbox) checkbox.checked = true;

      // Mostrar notificación
      this.showNotification(`Has añadido la característica: ${feature.name}`, 'info');
    } else {
      // Quitar la característica
      this.selectedTech.additionalFeatures.splice(index, 1);

      // Actualizar UI
      const featureEl = document.querySelector(`[data-feature-id="${featureId}"]`);
      if (featureEl) featureEl.classList.remove('selected');

      // Desmarcar el checkbox
      const checkbox = document.getElementById(`feature-${featureId}`);
      if (checkbox) checkbox.checked = false;

      // Mostrar notificación
      this.showNotification(`Has eliminado la característica: ${feature.name}`, 'warning');
    }

    // Actualizar resumen
    this.updateSummary();

    return true;
  }

  // Actualizar el resumen de selección
  updateSummary() {
    const summaryEl = document.getElementById('tech-selection-summary');
    if (!summaryEl) return;

    const backendTech = this.options.backend.find(b => b.id === this.selectedTech.backend);
    const frontendTech = this.options.frontend.find(f => f.id === this.selectedTech.frontend);
    const databaseTech = this.options.database.find(d => d.id === this.selectedTech.database);

    const backendName = backendTech ? backendTech.name : 'No seleccionado';
    const frontendName = frontendTech ? frontendTech.name : 'No seleccionado';
    const databaseName = databaseTech ? databaseTech.name : 'No seleccionado';

    // Calcular compatibilidad y complejidad
    const compatibility = this.calculateCompatibility();
    const complexity = this.calculateComplexity();

    // Construir HTML del resumen
    summaryEl.innerHTML = `
      <div class="stack-summary-header">
        <h5>Tu Stack Tecnológico</h5>
      </div>
      <div class="stack-summary-content">
        <div class="row">
          <div class="col-md-4">
            <div class="tech-summary-item">
              <span class="tech-label">Backend:</span>
              <span class="tech-value badge bg-primary">${backendName}</span>
            </div>
          </div>
          <div class="col-md-4">
            <div class="tech-summary-item">
              <span class="tech-label">Frontend:</span>
              <span class="tech-value badge bg-success">${frontendName}</span>
            </div>
          </div>
          <div class="col-md-4">
            <div class="tech-summary-item">
              <span class="tech-label">Base de datos:</span>
              <span class="tech-value badge bg-info">${databaseName}</span>
            </div>
          </div>
        </div>

        <div class="tech-indicators mt-3">
          <div class="row">
            <div class="col-md-6">
              <div class="indicator">
                <label>Compatibilidad</label>
                <div class="progress">
                  <div class="progress-bar bg-${this.getCompatibilityColor(compatibility)}" style="width: ${compatibility}%"></div>
                </div>
                <span class="small">${this.getCompatibilityText(compatibility)}</span>
              </div>
            </div>
            <div class="col-md-6">
              <div class="indicator">
                <label>Complejidad</label>
                <div class="progress">
                  <div class="progress-bar bg-${this.getComplexityColor(complexity)}" style="width: ${complexity}%"></div>
                </div>
                <span class="small">${this.getComplexityText(complexity)}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="selected-features mt-3">
          <h6>Características adicionales (${this.selectedTech.additionalFeatures.length}):</h6>
          <div class="feature-pills">
            ${this.selectedTech.additionalFeatures.map(featureId => {
              const feature = this.options.additionalFeatures.find(f => f.id === featureId);
              return feature ? `<span class="badge bg-secondary me-2 mb-2">${feature.name}</span>` : '';
            }).join('')}
          </div>
        </div>
      </div>
    `;

    // Actualizar estado del botón de continuar
    const continueBtn = document.getElementById('tech-selection-continue');
    if (continueBtn) {
      const isComplete = this.selectedTech.backend && this.selectedTech.frontend && this.selectedTech.database;
      continueBtn.disabled = !isComplete;
    }
  }

  // Calcular compatibilidad del stack
  calculateCompatibility() {
    if (!this.selectedTech.backend || !this.selectedTech.frontend || !this.selectedTech.database) {
      return 30; // Compatibilidad baja si falta algún componente
    }

    // Mapeo de stacks compatibles
    const compatibilityMap = {
      'node-react-mongodb': 95,
      'node-react-mysql': 85,
      'node-vue-mongodb': 90,
      'node-angular-mongodb': 85,
      'express-react-mongodb': 95,
      'express-vue-mongodb': 90,
      'flask-react-postgresql': 85,
      'flask-bootstrap-sqlite': 90,
      'flask-bootstrap-mysql': 90,
      'django-bootstrap-postgresql': 95,
      'django-react-postgresql': 90,
      'fastapi-react-postgresql': 90,
      'fastapi-vue-mongodb': 85,
      'streamlit-html-sqlite': 90,
      'streamlit-html-postgresql': 85
    };

    const key = `${this.selectedTech.backend}-${this.selectedTech.frontend}-${this.selectedTech.database}`;
    return compatibilityMap[key] || 75; // 75% por defecto para combinaciones no mapeadas
  }

  // Calcular complejidad del stack
  calculateComplexity() {
    if (!this.selectedTech.backend || !this.selectedTech.frontend || !this.selectedTech.database) {
      return 20; // Complejidad baja si falta algún componente
    }

    // Complejidad base por tecnología
    const complexityScores = {
      backend: {
        'flask': 30,
        'django': 60,
        'fastapi': 50,
        'streamlit': 25,
        'node': 40,
        'express': 45,
        'nestjs': 75
      },
      frontend: {
        'html': 20,
        'bootstrap': 30,
        'react': 65,
        'vue': 60,
        'angular': 80,
        'svelte': 55
      },
      database: {
        'sqlite': 20,
        'mysql': 45,
        'postgresql': 55,
        'mongodb': 50,
        'redis': 60
      }
    };

    // Calcular complejidad base
    let complexity = 0;
    complexity += complexityScores.backend[this.selectedTech.backend] || 40;
    complexity += complexityScores.frontend[this.selectedTech.frontend] || 40;
    complexity += complexityScores.database[this.selectedTech.database] || 40;

    // Ajustar por cantidad de características
    complexity += this.selectedTech.additionalFeatures.length * 5;

    // Normalizar a escala de 100
    complexity = Math.min(Math.round(complexity / 3), 100);

    return complexity;
  }

  // Obtener color para indicador de compatibilidad
  getCompatibilityColor(value) {
    if (value >= 80) return 'success';
    if (value >= 60) return 'info';
    if (value >= 40) return 'warning';
    return 'danger';
  }

  // Obtener texto para indicador de compatibilidad
  getCompatibilityText(value) {
    if (value >= 80) return 'Excelente compatibilidad';
    if (value >= 60) return 'Buena compatibilidad';
    if (value >= 40) return 'Compatibilidad moderada';
    return 'Compatibilidad limitada';
  }

  // Obtener color para indicador de complejidad
  getComplexityColor(value) {
    if (value <= 30) return 'success';
    if (value <= 60) return 'info';
    if (value <= 80) return 'warning';
    return 'danger';
  }

  // Obtener texto para indicador de complejidad
  getComplexityText(value) {
    if (value <= 30) return 'Baja complejidad - ideal para principiantes';
    if (value <= 60) return 'Complejidad moderada';
    if (value <= 80) return 'Complejidad considerable';
    return 'Alta complejidad - para desarrolladores avanzados';
  }

  // Obtener los datos seleccionados
  getSelectionData() {
    return {
      backend: this.selectedTech.backend,
      frontend: this.selectedTech.frontend,
      database: this.selectedTech.database,
      features: this.selectedTech.additionalFeatures
    };
  }

  // Exportar selección como JSON
  exportSelection() {
    return JSON.stringify(this.getSelectionData());
  }

  // Enviar datos al backend para iniciar la generación
  startGeneration() {
    // Obtener datos adicionales para mejorar la generación de código
    const appDescription = document.getElementById('app-description')?.value || '';

    // Añadir información específica sobre las tecnologías seleccionadas al prompt
    let enhancedDescription = appDescription;

    if (this.selectedTech.backend) {
      const backendName = this.getTechName('backend', this.selectedTech.backend);
      enhancedDescription += `\nUtilizando ${backendName} como backend.`;
    }

    if (this.selectedTech.frontend) {
      const frontendName = this.getTechName('frontend', this.selectedTech.frontend);
      enhancedDescription += `\nUtilizando ${frontendName} para el frontend.`;
    }

    if (this.selectedTech.database) {
      const databaseName = this.getTechName('database', this.selectedTech.database);
      enhancedDescription += `\nCon ${databaseName} como base de datos.`;
    }

    // Añadir información sobre las características seleccionadas
    if (this.selectedTech.additionalFeatures.length > 0) {
      enhancedDescription += "\nCaracterísticas específicas que debe implementar:";
      this.selectedTech.additionalFeatures.forEach(feature => {
        const featureName = this.options.additionalFeatures.find(f => f.id === feature)?.name || feature;
        enhancedDescription += `\n- ${featureName}`;
      });
    }

    // Añadir instrucciones específicas para la generación de código real
    enhancedDescription += "\n\nIMPORTANTE: Generar código funcional completo, no esqueletos o plantillas. Implementar todas las características solicitadas con código real.";

    const projectData = {
      description: enhancedDescription,
      features: this.selectedTech.additionalFeatures,
      agent: "developer", // Usar el agente desarrollador para código real
      model: "openai", // Usar OpenAI por defecto para máxima calidad
      tech_data: {
        backend: this.selectedTech.backend,
        frontend: this.selectedTech.frontend,
        database: this.selectedTech.database,
        features: this.selectedTech.additionalFeatures,
        generationMode: "fullCode" // Modo de generación completa
      },
      options: {
        includeTests: document.getElementById('include-tests')?.checked || false,
        includeDocs: document.getElementById('include-docs')?.checked || false,
        generateCompleteCode: true, // Flag explícito para generar código completo
        optimizeForProduction: true
      }
    };

    // Mostrar mensaje de espera
    this.showWaitingMessage("Preparando la generación de código completo...");

    fetch('/api/constructor/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(projectData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Error de servidor: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        console.log('Generación iniciada:', data);

        // Guardar el ID del proyecto
        sessionStorage.setItem('current_project_id', data.project_id);

        // Iniciar el polling de estado
        this.startStatusPolling(data.project_id);

        // Actualizar la UI para mostrar la pantalla de progreso
        this.showProgressScreen(data.project_id);
      } else {
        console.error('Error iniciando generación:', data.error);
        this.showError(data.error);
      }
    })
    .catch(error => {
      console.error('Error en la solicitud:', error);
      this.showError('Error de conexión: ' + error.message);

      // Reactivar el botón después de un error
      document.getElementById('generate-button').disabled = false;
    });
  }

  // Mostrar mensaje de espera durante la preparación
  showWaitingMessage(message) {
    const waitingElement = document.createElement('div');
    waitingElement.className = 'waiting-message';
    waitingElement.innerHTML = `
      <div class="spinner"></div>
      <p>${message}</p>
      <p class="small">Estamos preparando todo para generar código real y completo según tus especificaciones</p>
    `;

    // Añadir estilos para el spinner
    const style = document.createElement('style');
    style.textContent = `
      .waiting-message {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        color: white;
        text-align: center;
        padding: 20px;
      }
      .waiting-message p {
        margin: 15px 0;
        font-size: 18px;
      }
      .waiting-message .small {
        font-size: 14px;
        opacity: 0.8;
      }
      .spinner {
        width: 50px;
        height: 50px;
        border: 5px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(waitingElement);

    // Eliminar después de mostrar la pantalla de progreso
    setTimeout(() => {
      if (document.body.contains(waitingElement)) {
        document.body.removeChild(waitingElement);
      }
    }, 5000);
  }

  // Mostrar pantalla de progreso
  showProgressScreen(projectId) {
    // Implementar la visualización de la pantalla de progreso
    const progressContainer = document.getElementById('generation-progress-container');
    if (progressContainer) {
      document.getElementById('tech-selector-container').style.display = 'none';
      document.getElementById('constructor-container').style.display = 'none';
      progressContainer.style.display = 'block';

      // Actualizar el ID del proyecto en la interfaz
      const projectIdElement = document.getElementById('project-id-display');
      if (projectIdElement) {
        projectIdElement.textContent = projectId;
      }
    }
      }

      // Iniciar polling de estado
      startStatusPolling(projectId) {
        // Implementar el polling de estado
        const checkStatus = () => {
          fetch(`/api/constructor/status/${projectId}`)
            .then(response => response.json())
            .then(data => {
              this.updateProgressUI(data);

              if (data.status !== 'completed' && data.status !== 'failed') {
                setTimeout(checkStatus, 3000); // Verificar cada 3 segundos
              }
            })
            .catch(error => {
              console.error('Error al verificar estado:', error);
              setTimeout(checkStatus, 5000); // Reintentar después de 5 segundos en caso de error
            });
        };

        checkStatus(); // Iniciar el proceso de verificación
      }

      // Actualizar UI de progreso
      updateProgressUI(statusData) {
        const progressBar = document.getElementById('generation-progress-bar');
        const statusText = document.getElementById('generation-status-text');
        const logContainer = document.getElementById('generation-log');

        if (!progressBar || !statusText || !logContainer) return;

        // Actualizar barra de progreso
        const progressPercentage = statusData.progress || 0;
        progressBar.style.width = `${progressPercentage}%`;
        progressBar.setAttribute('aria-valuenow', progressPercentage);

        // Actualizar texto de estado
        statusText.textContent = statusData.status_message || statusData.status || 'Procesando...';

        // Añadir nuevos mensajes al log
        if (statusData.logs && Array.isArray(statusData.logs)) {
          statusData.logs.forEach(log => {
            // Verificar si el mensaje ya existe para evitar duplicados
            const messageId = `log-${log.timestamp}-${log.message.substring(0, 20).replace(/\s+/g, '-')}`;
            if (!document.getElementById(messageId)) {
              const logEntry = document.createElement('div');
              logEntry.id = messageId;
              logEntry.className = `log-entry log-${log.level || 'info'}`;
              logEntry.innerHTML = `
                <span class="log-time">${new Date(log.timestamp).toLocaleTimeString()}</span>
                <span class="log-message">${log.message}</span>
              `;
              logContainer.appendChild(logEntry);
              logContainer.scrollTop = logContainer.scrollHeight;
            }
          });
        }

        // Si el proceso ha finalizado, mostrar botones de acción
        if (statusData.status === 'completed') {
          const actionsContainer = document.getElementById('generation-actions');
          if (actionsContainer) {
            actionsContainer.innerHTML = `
              <button class="btn btn-success" onclick="downloadProject('${statusData.project_id}')">
                <i class="fas fa-download"></i> Descargar Proyecto
              </button>
              <button class="btn btn-primary" onclick="viewProjectDetails('${statusData.project_id}')">
                <i class="fas fa-info-circle"></i> Ver Detalles
              </button>
            `;
            actionsContainer.style.display = 'block';
          }
        } else if (statusData.status === 'failed') {
          const actionsContainer = document.getElementById('generation-actions');
          if (actionsContainer) {
            actionsContainer.innerHTML = `
              <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> Error: ${statusData.error || 'Ha ocurrido un error durante la generación'}
              </div>
              <button class="btn btn-warning" onclick="retryGeneration('${statusData.project_id}')">
                <i class="fas fa-redo"></i> Reintentar
              </button>
            `;
            actionsContainer.style.display = 'block';
          }
        }
      }

      // Mostrar mensaje de error
      showError(errorMessage) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="error-content">
            <h4>Error</h4>
            <p>${errorMessage}</p>
            <button class="btn btn-sm btn-outline-light mt-2 close-error-btn">Cerrar</button>
          </div>
        `;

        // Añadir estilos para el mensaje de error
        const style = document.createElement('style');
        style.textContent = `
          .error-message {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            display: flex;
            max-width: 400px;
          }
          .error-icon {
            font-size: 24px;
            margin-right: 15px;
            display: flex;
            align-items: center;
          }
          .error-content h4 {
            margin: 0 0 10px 0;
          }
          .error-content p {
            margin: 0;
            opacity: 0.9;
          }
        `;
        document.head.appendChild(style);
        document.body.appendChild(errorElement);

        // Configurar el botón para cerrar el mensaje
        const closeBtn = errorElement.querySelector('.close-error-btn');
        if (closeBtn) {
          closeBtn.addEventListener('click', () => {
            if (document.body.contains(errorElement)) {
              document.body.removeChild(errorElement);
            }
          });
        }

        // Auto-eliminar después de 10 segundos
        setTimeout(() => {
          if (document.body.contains(errorElement)) {
            document.body.removeChild(errorElement);
          }
        }, 10000);
      }
    }

    // Inicializar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
      const techSelectorContainer = document.getElementById('tech-selector-container');
      if (techSelectorContainer) {
        window.techSelector = new TechSelector();

        // Generar HTML de opciones
        document.getElementById('backend-options').innerHTML = 
          window.techSelector.generateTechOptions('backend', window.techSelector.options.backend);

        document.getElementById('frontend-options').innerHTML = 
          window.techSelector.generateTechOptions('frontend', window.techSelector.options.frontend);

        document.getElementById('database-options').innerHTML = 
          window.techSelector.generateTechOptions('database', window.techSelector.options.database);

        document.getElementById('features-options').innerHTML = 
          window.techSelector.generateFeatureOptions(window.techSelector.options.additionalFeatures);

        document.getElementById('preset-stacks').innerHTML = 
          window.techSelector.generatePresetOptions(window.techSelector.presetStacks);

        // Asignar eventos mediante delegación
        document.addEventListener('click', function(e) {
          // Manejo específico para botones de plantillas
          if (e.target.classList.contains('select-preset-btn')) {
            const presetCard = e.target.closest('.preset-card');
            if (presetCard) {
              const presetIndex = parseInt(presetCard.dataset.presetIndex);
              window.techSelector.applyPreset(presetIndex);
            }
            return; // Evitar procesamiento adicional
          }

          // Manejo de tarjetas de tecnología
          if (e.target.closest('.tech-option-card')) {
            const card = e.target.closest('.tech-option-card');
            const techId = card.dataset.techId;
            const category = card.dataset.category;
            window.techSelector.selectTech(category, techId);
          }

          // Manejo de tarjetas de características
          if (e.target.closest('.feature-card')) {
            const card = e.target.closest('.feature-card');
            const featureId = card.dataset.featureId;
            window.techSelector.toggleFeature(featureId);
          }

          // Manejo del botón continuar
          if (e.target.id === 'tech-selection-continue') {
            // Ocultar selector y mostrar constructor
            document.getElementById('tech-selector-container').style.display = 'none';
            document.getElementById('constructor-container').style.display = 'block';

            // Pasar la selección al proceso de construcción
            const techSelection = window.techSelector.getSelectionData();
            document.getElementById('project-tech-data').value = window.techSelector.exportSelection();

            // Actualizar resumen en la interfaz de construcción
            updateConstructorSummary(techSelection);

            // Mostrar notificación
            window.techSelector.showNotification('¡Selección completada! Ahora puedes describir tu proyecto.', 'success');
          }

          // Manejo del botón generar
          if (e.target.id === 'generate-button') {
            e.target.disabled = true;
            window.techSelector.startGeneration();
          }
        });

        // Inicializar resumen
        window.techSelector.updateSummary();
      }

      // Función auxiliar para actualizar resumen en el constructor
      function updateConstructorSummary(techSelection) {
        const summaryElement = document.getElementById('selected-tech-summary');
        if (!summaryElement) return;

        summaryElement.innerHTML = `
          <div class="d-flex align-items-center mb-3">
            <div class="tech-badge bg-primary me-2">
              <i class="fab ${getTechIcon('backend', techSelection.backend)}"></i>
            </div>
            <span>${window.techSelector.getTechName('backend', techSelection.backend)}</span>
          </div>
          <div class="d-flex align-items-center mb-3">
            <div class="tech-badge bg-success me-2">
              <i class="fab ${getTechIcon('frontend', techSelection.frontend)}"></i>
            </div>
            <span>${window.techSelector.getTechName('frontend', techSelection.frontend)}</span>
          </div>
          <div class="d-flex align-items-center">
            <div class="tech-badge bg-info me-2">
              <i class="fas fa-database"></i>
            </div>
            <span>${window.techSelector.getTechName('database', techSelection.database)}</span>
          </div>
        `;

        // Mostrar características seleccionadas
        const featuresElement = document.getElementById('selected-features');
        if (featuresElement && techSelection.features.length > 0) {
          let featuresHtml = '<div class="selected-features-list mt-3">';
          techSelection.features.forEach(featureId => {
            const feature = window.techSelector.options.additionalFeatures.find(f => f.id === featureId);
            if (feature) {
              featuresHtml += `<span class="badge bg-secondary me-2 mb-2">${feature.name}</span>`;
            }
          });
          featuresHtml += '</div>';
          featuresElement.innerHTML = featuresHtml;
        }
      }

      // Función auxiliar para obtener icono
      function getTechIcon(category, techId) {
        const tech = window.techSelector?.options[category]?.find(t => t.id === techId);
        return tech ? tech.icon : 'fa-code';
      }
    });

    // Funciones globales para acciones de proyecto
    function downloadProject(projectId) {
      window.location.href = `/api/constructor/download/${projectId}`;
    }

    function viewProjectDetails(projectId) {
      window.location.href = `/projects/${projectId}`;
    }

    function retryGeneration(projectId) {
      fetch(`/api/constructor/retry/${projectId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Reiniciar la UI de progreso
          const progressBar = document.getElementById('generation-progress-bar');
          const statusText = document.getElementById('generation-status-text');
          const actionsContainer = document.getElementById('generation-actions');

          if (progressBar) progressBar.style.width = '0%';
          if (statusText) statusText.textContent = 'Reiniciando generación...';
          if (actionsContainer) actionsContainer.style.display = 'none';

          // Reiniciar el polling de estado
          window.techSelector.startStatusPolling(projectId);

          // Mostrar notificación
          window.techSelector.showNotification('Reiniciando la generación del proyecto...', 'info');
        } else {
          window.techSelector.showError(data.error || 'Error al reintentar la generación');
        }
      })
      .catch(error => {
        window.techSelector.showError('Error de conexión: ' + error.message);
      });
    }

    // Función para obtener características seleccionadas (para el formulario constructor)
    function getSelectedFeatures() {
      const features = [];
      document.querySelectorAll('.feature-checkbox:checked').forEach(checkbox => {
        const featureId = checkbox.id.replace('feature-', '');
        features.push(featureId);
      });
      return features;
    }
