
import os
import time
import uuid
import json
import shutil
import logging
import zipfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, render_template
from threading import Thread

# Initialize the blueprint
constructor_bp = Blueprint('constructor', __name__)

# Project storage
PROJECTS_DIR = os.path.join('user_workspaces', 'projects')
os.makedirs(PROJECTS_DIR, exist_ok=True)

# In-memory storage for project status
project_status = {}

# Variable para controlar si el desarrollo está pausado
development_paused = {}

# Function to create a workspace for a project
def create_project_workspace(project_id):
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    return project_dir

# Background task for generating application
def generate_application(project_id, description, agent, model, options, features):
    try:
        # Initialize project status
        project_status[project_id] = {
            'status': 'in_progress',
            'progress': 5,
            'current_stage': 'Analizando requisitos...',
            'console_messages': [],
            'start_time': time.time(),
            'completion_time': None
        }
        
        # Initialize development_paused status
        development_paused[project_id] = False
        
        # Function to update status
        def update_status(progress, stage, message=None):
            project_status[project_id]['progress'] = progress
            
            # Mantener la etiqueta (PAUSADO) si está pausado
            if development_paused.get(project_id, False) and " (PAUSADO)" not in stage:
                stage += " (PAUSADO)"
                
            project_status[project_id]['current_stage'] = stage
            
            if message:
                project_status[project_id]['console_messages'].append({
                    'time': time.time(),
                    'message': message
                })
                logging.info(f"Project {project_id}: {message}")
                
            # Si está pausado, esperar hasta que se reanude
            while development_paused.get(project_id, False) and project_status[project_id]['status'] == 'in_progress':
                time.sleep(1)  # Esperar un segundo antes de verificar nuevamente
        
        # Get project directory
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        
        # Simulate or actually generate the application using AI models
        # Stage 1: Analyzing requirements
        update_status(10, "Analizando requisitos y creando plan de desarrollo...", "Iniciando análisis de requisitos")
        time.sleep(3)  # In production, this would be a real API call
        
        # Create project structure directory
        os.makedirs(os.path.join(project_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'docs'), exist_ok=True)
        
        # Stage 2: Architecture design
        update_status(20, "Diseñando arquitectura...", "Definiendo estructura y componentes")
        time.sleep(3)  # In production, this would be a real API call
        
        # Create architecture diagram
        with open(os.path.join(project_dir, 'architecture.md'), 'w') as f:
            f.write(f"# Architecture Design\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"This document outlines the architecture for the application: {description}\n\n")
            f.write(f"## Components\n\n")
            for feature in features:
                f.write(f"- {feature}\n")
        
        # Stage 3: Code generation
        update_status(40, "Generando código...", "Creando archivos fuente")
        
        # Determine technology stack based on description
        frontend_framework = "React"
        backend_framework = "Flask"
        database = "SQLite"
        
        # Create backend structure
        os.makedirs(os.path.join(project_dir, 'src', 'backend'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'backend', 'models'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'backend', 'routes'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'backend', 'utils'), exist_ok=True)
        
        # Create frontend structure
        os.makedirs(os.path.join(project_dir, 'src', 'frontend'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'frontend', 'components'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'frontend', 'pages'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src', 'frontend', 'styles'), exist_ok=True)
        
        # Generate some initial files
        # app.py
        with open(os.path.join(project_dir, 'src', 'backend', 'app.py'), 'w') as f:
            f.write("""from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status')
def status():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
        
        # requirements.txt
        with open(os.path.join(project_dir, 'requirements.txt'), 'w') as f:
            f.write("""flask==2.0.1
flask-cors==3.0.10
gunicorn==20.1.0
python-dotenv==0.19.1
""")
        
        # README.md
        with open(os.path.join(project_dir, 'README.md'), 'w') as f:
            f.write(f"# {project_id.upper()}\n\n")
            f.write(f"## Descripción\n\n{description}\n\n")
            f.write(f"## Características\n\n")
            for feature in features:
                f.write(f"- {feature}\n")
            f.write(f"\n## Instrucciones\n\n")
            f.write(f"1. Instalar dependencias: `pip install -r requirements.txt`\n")
            f.write(f"2. Ejecutar la aplicación: `python src/backend/app.py`\n")
        
        # Create package.json if frontend is included
        with open(os.path.join(project_dir, 'package.json'), 'w') as f:
            f.write("""{
  "name": "auto-generated-app",
  "version": "1.0.0",
  "description": "Auto-generated application",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-router-dom": "^6.0.2",
    "axios": "^0.24.0"
  },
  "devDependencies": {
    "react-scripts": "5.0.0"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}""")
        
        # Create a simple index.html
        os.makedirs(os.path.join(project_dir, 'src', 'frontend', 'public'), exist_ok=True)
        with open(os.path.join(project_dir, 'src', 'frontend', 'public', 'index.html'), 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Generated Application</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")
        
        # Create App.js
        os.makedirs(os.path.join(project_dir, 'src', 'frontend', 'src'), exist_ok=True)
        with open(os.path.join(project_dir, 'src', 'frontend', 'src', 'App.js'), 'w') as f:
            f.write("""import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [status, setStatus] = useState('Loading...');

  useEffect(() => {
    fetch('/api/status')
      .then(response => response.json())
      .then(data => setStatus(data.status))
      .catch(error => setStatus('Error: ' + error.message));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Auto-Generated Application</h1>
        <p>Backend Status: {status}</p>
      </header>
      <main className="container mt-4">
        <div className="row">
          <div className="col-md-8 offset-md-2">
            <div className="card">
              <div className="card-header">
                Welcome
              </div>
              <div className="card-body">
                <h5 className="card-title">Your application is ready!</h5>
                <p className="card-text">This is an auto-generated application. You can customize it to fit your needs.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;""")
        
        # Create App.css
        with open(os.path.join(project_dir, 'src', 'frontend', 'src', 'App.css'), 'w') as f:
            f.write(""".App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  min-height: 20vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
  margin-bottom: 2rem;
}

.App-link {
  color: #61dafb;
}""")
        
        # Create index.js
        with open(os.path.join(project_dir, 'src', 'frontend', 'src', 'index.js'), 'w') as f:
            f.write("""import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);""")
        
        # Create index.css
        with open(os.path.join(project_dir, 'src', 'frontend', 'src', 'index.css'), 'w') as f:
            f.write("""body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}""")
        
        update_status(60, "Implementando características principales...", "Generando modelos y componentes")
        time.sleep(3)  # In production, this would be a real API call
        
        # If tests are requested, create test files
        if options.get('includeTests', False):
            os.makedirs(os.path.join(project_dir, 'tests'), exist_ok=True)
            with open(os.path.join(project_dir, 'tests', 'test_app.py'), 'w') as f:
                f.write("""import unittest
import sys
import os

# Add the parent directory to the path to import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_status_endpoint(self):
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
""")
            update_status(70, "Generando pruebas...", "Creando tests unitarios")
            time.sleep(2)
        
        # If documentation is requested, create more detailed docs
        if options.get('includeDocs', False):
            with open(os.path.join(project_dir, 'docs', 'api.md'), 'w') as f:
                f.write("""# API Documentation

## Endpoints

### GET /api/status

Returns the status of the application.

**Response**

```json
{
  "status": "ok"
}
```

**Status Codes**

- 200: Success
""")
            
            with open(os.path.join(project_dir, 'docs', 'setup.md'), 'w') as f:
                f.write("""# Setup Guide

## Requirements

- Python 3.8+
- Node.js 14+ (for frontend development)

## Installation

1. Clone the repository
2. Install backend dependencies: `pip install -r requirements.txt`
3. Install frontend dependencies: `cd src/frontend && npm install`

## Running the Application

### Backend

```bash
python src/backend/app.py
```

### Frontend

```bash
cd src/frontend
npm start
```
""")
            update_status(80, "Generando documentación...", "Creando archivos de documentación")
            time.sleep(2)
        
        # If deployment is requested, create deployment files
        if options.get('includeDeployment', False):
            with open(os.path.join(project_dir, 'Procfile'), 'w') as f:
                f.write("web: gunicorn src.backend.app:app")
            
            with open(os.path.join(project_dir, '.env.example'), 'w') as f:
                f.write("""# Environment Variables
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
""")
            update_status(90, "Configurando despliegue...", "Generando archivos para despliegue")
            time.sleep(2)
        
        # If CI/CD is requested, create workflows
        if options.get('includeCICD', False):
            os.makedirs(os.path.join(project_dir, '.github', 'workflows'), exist_ok=True)
            with open(os.path.join(project_dir, '.github', 'workflows', 'ci.yml'), 'w') as f:
                f.write("""name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m unittest discover tests
""")
            update_status(95, "Configurando CI/CD...", "Creando flujos de trabajo de integración continua")
            time.sleep(2)
        
        # Create a zip file of the project
        update_status(98, "Preparando archivos para descarga...", "Comprimiendo proyecto")
        zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, PROJECTS_DIR)
                    zipf.write(file_path, arcname)
        
        # Mark project as completed
        project_status[project_id]['status'] = 'completed'
        project_status[project_id]['progress'] = 100
        project_status[project_id]['current_stage'] = 'Proyecto completado exitosamente'
        project_status[project_id]['completion_time'] = time.time()
        project_status[project_id]['console_messages'].append({
            'time': time.time(),
            'message': "Aplicación generada exitosamente y lista para descargar"
        })
        
    except Exception as e:
        logging.error(f"Error generating application: {str(e)}")
        # Mark project as failed
        if project_id in project_status:
            project_status[project_id]['status'] = 'failed'
            project_status[project_id]['error'] = str(e)
            project_status[project_id]['console_messages'].append({
                'time': time.time(),
                'message': f"Error: {str(e)}"
            })

# Route to analyze features from a description
@constructor_bp.route('/api/constructor/analyze-features', methods=['POST'])
def analyze_features():
    try:
        data = request.json
        description = data.get('description', '')
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Se requiere una descripción'
            }), 400
        
        # Simple keyword-based feature extraction
        # In production, this would use a more sophisticated model
        features = []
        keywords = {
            'autenticación': 'Sistema de autenticación',
            'login': 'Sistema de autenticación',
            'registrar': 'Sistema de registro de usuarios',
            'registro': 'Sistema de registro de usuarios',
            'dashboard': 'Panel de control',
            'admin': 'Panel de administración',
            'gráficos': 'Visualización de datos',
            'gráfico': 'Visualización de datos',
            'gráficas': 'Visualización de datos',
            'pdf': 'Generación de PDF',
            'reportes': 'Generación de reportes',
            'reporte': 'Generación de reportes',
            'api': 'API REST',
            'rest': 'API REST',
            'chat': 'Sistema de chat',
            'mensaje': 'Sistema de mensajería',
            'mensajería': 'Sistema de mensajería',
            'notificación': 'Sistema de notificaciones',
            'notificaciones': 'Sistema de notificaciones',
            'tiempo real': 'Actualizaciones en tiempo real',
            'búsqueda': 'Sistema de búsqueda',
            'buscar': 'Sistema de búsqueda',
            'filtrar': 'Filtros avanzados',
            'filtros': 'Filtros avanzados',
            'móvil': 'Diseño responsivo',
            'celular': 'Diseño responsivo',
            'tablet': 'Diseño responsivo',
            'responsive': 'Diseño responsivo',
            'base de datos': 'Base de datos',
            'sql': 'Base de datos SQL',
            'nosql': 'Base de datos NoSQL',
            'mongodb': 'Base de datos MongoDB',
            'postgres': 'Base de datos PostgreSQL',
            'mysql': 'Base de datos MySQL',
            'pago': 'Sistema de pagos',
            'pagos': 'Sistema de pagos',
            'admin': 'Panel de administración',
            'inventario': 'Gestión de inventario',
            'producto': 'Catálogo de productos',
            'productos': 'Catálogo de productos',
            'email': 'Sistema de correo electrónico',
            'correo': 'Sistema de correo electrónico',
            'archivo': 'Gestión de archivos',
            'archivos': 'Gestión de archivos',
            'subir': 'Carga de archivos',
            'cargar': 'Carga de archivos',
            'upload': 'Carga de archivos',
            'calendario': 'Calendario integrado',
            'fecha': 'Selector de fechas',
            'mapa': 'Integración de mapas',
            'mapas': 'Integración de mapas',
            'geolocalización': 'Geolocalización',
            'formulario': 'Formularios dinámicos',
            'formularios': 'Formularios dinámicos',
            'estadísticas': 'Estadísticas y métricas',
            'métricas': 'Estadísticas y métricas',
        }
        
        # Extract features from description using keywords
        description_lower = description.lower()
        for keyword, feature in keywords.items():
            if keyword in description_lower and feature not in features:
                features.append(feature)
        
        # Add some default features
        if not any('autenticación' in f.lower() for f in features):
            features.append('Gestión de usuarios')
        
        if not any(('base de datos' in f.lower()) for f in features):
            features.append('Base de datos')
        
        # Limit to a reasonable number of features
        features = features[:10]
        
        return jsonify({
            'success': True,
            'features': features
        })
    except Exception as e:
        logging.error(f"Error analyzing features: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route to start application generation
@constructor_bp.route('/api/constructor/generate', methods=['POST'])
def generate_project():
    try:
        data = request.json
        description = data.get('description', '')
        agent = data.get('agent', 'developer')
        model = data.get('model', 'openai')
        options = data.get('options', {})
        features = data.get('features', [])
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Se requiere una descripción del proyecto'
            }), 400
        
        # Generate a unique project ID
        project_id = f"app_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Create a workspace for the project
        create_project_workspace(project_id)
        
        # Start the generation process in a background thread
        thread = Thread(target=generate_application, args=(project_id, description, agent, model, options, features))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Generación de proyecto iniciada',
            'project_id': project_id,
            'estimated_time': '2-5 minutos'
        })
    except Exception as e:
        logging.error(f"Error initiating project generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route to check project status
@constructor_bp.route('/api/constructor/status/<project_id>', methods=['GET'])
def project_status_route(project_id):
    try:
        if project_id not in project_status:
            return jsonify({
                'success': False,
                'error': 'Proyecto no encontrado'
            }), 404
        
        status_data = project_status[project_id]
        
        # Get the most recent console message if any
        console_message = None
        if status_data['console_messages']:
            console_message = status_data['console_messages'][-1]['message']
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'status': status_data['status'],
            'progress': status_data['progress'],
            'current_stage': status_data['current_stage'],
            'console_message': console_message,
            'error': status_data.get('error')
        })
    except Exception as e:
        logging.error(f"Error checking project status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route to download a generated project
@constructor_bp.route('/api/constructor/download/<project_id>', methods=['GET'])
def download_project(project_id):
    try:
        zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
        
        if not os.path.exists(zip_path):
            return jsonify({
                'success': False,
                'error': 'Archivo de proyecto no encontrado'
            }), 404
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{project_id}.zip"
        )
    except Exception as e:
        logging.error(f"Error downloading project: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route to preview a generated project
@constructor_bp.route('/api/constructor/preview/<project_id>', methods=['GET'])
def preview_project(project_id):
    try:
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        
        if not os.path.exists(project_dir):
            return jsonify({
                'success': False,
                'error': 'Proyecto no encontrado'
            }), 404
        
        # Get a list of files in the project
        file_list = []
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                file_list.append(rel_path)
        
        # For preview, render a simplified project view
        return render_template(
            'preview.html',
            project_id=project_id,
            file_list=file_list,
            title=f"Vista previa del proyecto: {project_id}"
        )
    except Exception as e:
        logging.error(f"Error previewing project: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
# Route to pause development
@constructor_bp.route('/api/constructor/pause/<project_id>', methods=['POST'])
def pause_development(project_id):
    try:
        if project_id not in project_status:
            return jsonify({
                'success': False,
                'error': 'Proyecto no encontrado'
            }), 404
        
        # Mark development as paused
        development_paused[project_id] = True
        
        # Update project status
        if project_status[project_id]['status'] == 'in_progress':
            project_status[project_id]['current_stage'] += " (PAUSADO)"
            project_status[project_id]['console_messages'].append({
                'time': time.time(),
                'message': "Desarrollo pausado por el usuario"
            })
        
        return jsonify({
            'success': True,
            'message': 'Desarrollo pausado exitosamente'
        })
    except Exception as e:
        logging.error(f"Error pausing development: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route to resume development
@constructor_bp.route('/api/constructor/resume/<project_id>', methods=['POST'])
def resume_development(project_id):
    try:
        if project_id not in project_status:
            return jsonify({
                'success': False,
                'error': 'Proyecto no encontrado'
            }), 404
        
        # Mark development as resumed
        development_paused[project_id] = False
        
        # Update project status
        if project_status[project_id]['status'] == 'in_progress':
            current_stage = project_status[project_id]['current_stage']
            project_status[project_id]['current_stage'] = current_stage.replace(" (PAUSADO)", "")
            project_status[project_id]['console_messages'].append({
                'time': time.time(),
                'message': "Desarrollo reanudado por el usuario"
            })
        
        return jsonify({
            'success': True,
            'message': 'Desarrollo reanudado exitosamente'
        })
    except Exception as e:
        logging.error(f"Error resuming development: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
