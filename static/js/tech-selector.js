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
  }

  // Generar HTML para opciones de tecnología
  generateTechOptions(categoryName, options) {
    let html = '';
    options.forEach(option => {
      html += `
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
      `;
    });
    return html;
  }

  // Generar HTML para características adicionales
  generateFeatureOptions(features) {
    let html = '';
    features.forEach(feature => {
      html += `
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
      `;
    });
    return html;
  }

  // Generar HTML para plantillas predefinidas
  generatePresetOptions(presets) {
    let html = '';
    presets.forEach((preset, index) => {
      html += `
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
      `;
    });
    return html;
  }

  // Obtener nombre de tecnología por ID
  getTechName(category, techId) {
    const tech = this.options[category].find(t => t.id === techId);
    return tech ? tech.name : 'Desconocido';
  }

  // Aplicar una plantilla predefinida
  applyPreset(presetIndex) {
    const preset = this.presetStacks[presetIndex];
    if (!preset) return false;

    this.selectTech('backend', preset.backend);
    this.selectTech('frontend', preset.frontend);
    this.selectTech('database', preset.database);

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
    }

    // Actualizar resumen
    this.updateSummary();

    return true;
  }

  // Alternar una característica adicional
  toggleFeature(featureId) {
    const index = this.selectedTech.additionalFeatures.indexOf(featureId);

    if (index === -1) {
      // Añadir la característica
      this.selectedTech.additionalFeatures.push(featureId);

      // Actualizar UI
      const featureEl = document.querySelector(`[data-feature-id="${featureId}"]`);
      if (featureEl) featureEl.classList.add('selected');
    } else {
      // Quitar la característica
      this.selectedTech.additionalFeatures.splice(index, 1);

      // Actualizar UI
      const featureEl = document.querySelector(`[data-feature-id="${featureId}"]`);
      if (featureEl) featureEl.classList.remove('selected');
    }

    // Actualizar resumen
    this.updateSummary();

    return true;
  }

  // Actualizar el resumen de selección
  updateSummary() {
    const summaryEl = document.getElementById('tech-selection-summary');
    if (!summaryEl) return;

    let backendName = 'No seleccionado';
    let frontendName = 'No seleccionado';
    let databaseName = 'No seleccionado';

    if (this.selectedTech.backend) {
      const backend = this.options.backend.find(b => b.id === this.selectedTech.backend);
      if (backend) backendName = backend.name;
    }

    if (this.selectedTech.frontend) {
      const frontend = this.options.frontend.find(f => f.id === this.selectedTech.frontend);
      if (frontend) frontendName = frontend.name;
    }

    if (this.selectedTech.database) {
      const database = this.options.database.find(d => d.id === this.selectedTech.database);
      if (database) databaseName = database.name;
    }

    // Calcular compatibilidad y complejidad
    const compatibility = this.calculateCompatibility();
    const complexity = this.calculateComplexity();

    // Construir HTML del resumen
    const html = `
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

    summaryEl.innerHTML = html;

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
        const appDescription = document.getElementById('app-description').value;

        // Añadir información específica sobre las tecnologías seleccionadas al prompt
        let enhancedDescription = appDescription;

        if (this.selectedTech.backend) {
            enhancedDescription += `\nUtilizando ${this.selectedTech.backend} como backend.`;
        }

        if (this.selectedTech.frontend) {
            enhancedDescription += `\nUtilizando ${this.selectedTech.frontend} para el frontend.`;
        }

        if (this.selectedTech.database) {
            enhancedDescription += `\nCon ${this.selectedTech.database} como base de datos.`;
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
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
  if (document.getElementById('tech-selector-container')) {
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

    // Asignar eventos
    // Selección de tecnología
    document.querySelectorAll('.tech-option-card').forEach(card => {
      card.addEventListener('click', function() {
        const techId = this.dataset.techId;
        const category = this.dataset.category;
        window.techSelector.selectTech(category, techId);
      });
    });

    // Selección de características
    document.querySelectorAll('.feature-card').forEach(card => {
      card.addEventListener('click', function() {
        const featureId = this.dataset.featureId;
        window.techSelector.toggleFeature(featureId);
      });
    });

    // Selección de plantillas
    document.querySelectorAll('.select-preset-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        const presetCard = this.closest('.preset-card');
        if (presetCard) {
          const presetIndex = parseInt(presetCard.dataset.presetIndex);
          window.techSelector.applyPreset(presetIndex);
        }
      });
    });

    // Continuar con la selección
    document.getElementById('tech-selection-continue').addEventListener('click', function() {
      // Ocultar selector y mostrar constructor
      document.getElementById('tech-selector-container').style.display = 'none';
      document.getElementById('constructor-container').style.display = 'block';

      // Pasar la selección al proceso de construcción
      const techSelection = window.techSelector.getSelectionData();
      document.getElementById('project-tech-data').value = window.techSelector.exportSelection();

      // Actualizar resumen en la interfaz de construcción
      document.getElementById('selected-tech-summary').innerHTML = `
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
      if (techSelection.features.length > 0) {
        let featuresHtml = '<div class="selected-features-list mt-3">';
        techSelection.features.forEach(featureId => {
          const feature = window.techSelector.options.additionalFeatures.find(f => f.id === featureId);
          if (feature) {
            featuresHtml += `<span class="badge bg-secondary me-2 mb-2">${feature.name}</span>`;
          }
        });
        featuresHtml += '</div>';
        document.getElementById('selected-features').innerHTML = featuresHtml;
      }
    });

    // Inicializar resumen
    window.techSelector.updateSummary();
  }

  // Función auxiliar para obtener icono
  function getTechIcon(category, techId) {
    const tech = window.techSelector.options[category].find(t => t.id === techId);
    return tech ? tech.icon : 'fa-code';
  }
});


// Evento de envío del formulario
    constructorForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Obtener valores del formulario
        const description = projectDescription.value.trim();
        const agent = document.getElementById('agent-selector').value;
        const model = document.getElementById('model-selector').value;
        const includeTests = document.getElementById('include-tests').checked;
        const includeDocs = document.getElementById('include-docs').checked;
        const includeDeployment = document.getElementById('include-deployment').checked;
        const includeCICD = document.getElementById('include-ci-cd').checked;
        const features = getSelectedFeatures();
        const techData = document.getElementById('project-tech-data').value;

        if (!description) {
            alert('Por favor, describe tu aplicación');
            return;
        }

        // Mostrar sección de progreso
        progressSection.style.display = 'block';
        resultSection.style.display = 'none';
        generateBtn.disabled = true;
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.textContent = '0%';
        generationConsole.innerHTML = '';

        // Iniciar generación del proyecto
        fetch('/api/constructor/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                agent: agent,
                model: model,
                options: {
                    includeTests,
                    includeDocs,
                    includeDeployment,
                    includeCICD
                },
                features: features,
                tech_data: techData // Incluir datos de tecnología seleccionada
            }),
        })
        .then(response => {
            // Verificar si la respuesta es JSON válido antes de procesarla
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            } else {
                // Si no es JSON, convertir a texto y luego lanzar error
                return response.text().then(text => {
                    throw new Error(`Respuesta no válida del servidor: ${text.substring(0, 100)}...`);
                });
            }
        })
        .then(data => {
            if (data.success) {
                projectId = data.project_id;
                addConsoleMessage(`Proyecto iniciado con ID: ${projectId}`);
                addConsoleMessage(`Tiempo estimado: ${data.estimated_time}`);
                startStatusCheck(projectId);

                // Actualizar progreso inicial
                progressBar.style.width = '5%';
                progressBar.setAttribute('aria-valuenow', 5);
                progressBar.textContent = '5%';
            } else {
                showFailedState(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFailedState(error.message || "Error de conexión con el servidor");

            // Intentar recuperar el estado automáticamente
            setTimeout(() => {
                addConsoleMessage("Intentando recuperar estado automáticamente...", "info");

                // Generar un ID de proyecto temporal si es necesario
                if (!projectId) {
                    projectId = 'app_' + Math.random().toString(36).substring(2, 10) + '_' + Math.floor(Date.now() / 1000);
                    addConsoleMessage(`Usando ID temporal: ${projectId}`, "info");
                }

                startStatusCheck(projectId);
            }, 3000);
        });
    });