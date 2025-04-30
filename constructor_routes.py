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
            'completion_time': None,
            'framework': None,  # Almacenará el framework seleccionado
            'techstack': {},    # Detalles del stack tecnológico
            'plan': {           # Plan de desarrollo
                'selected_technologies': [],
                'development_phases': [],
                'estimated_time': ''
            }
        }

        # Initialize development_paused status
        development_paused[project_id] = False

        # Function to update status
        def update_status(progress, stage, message=None):
            # Actualizar solo si el proyecto existe
            if project_id not in project_status:
                return

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

            # Si está pausado, esperar hasta que se reanude pero con timeout
            pause_start_time = time.time()
            while (development_paused.get(project_id, False) and
                  project_id in project_status and
                  project_status[project_id]['status'] == 'in_progress'):
                # Si ha estado pausado por más de 5 minutos, continuar
                if time.time() - pause_start_time > 300:
                    logging.warning(f"Project {project_id} auto-resumed after 5 minutes of pause")
                    development_paused[project_id] = False
                    break
                time.sleep(1)

        # Determinar el stack tecnológico basado en la descripción
        frameworks = determine_frameworks(description.lower())
        if frameworks.get('recommended'):
            project_status[project_id]['framework'] = frameworks['recommended']['name']
            project_status[project_id]['techstack'] = {
                'backend': frameworks['recommended']['backend']['id'],
                'frontend': frameworks['recommended']['frontend']['id'],
                'database': frameworks['recommended']['database']['id'] if frameworks['recommended']['database'] else 'sqlite'
            }

            # Añadir mensaje sobre el stack tecnológico
            update_status(
                8, 
                "Analizando requisitos y seleccionando tecnologías...",
                f"Stack tecnológico seleccionado: {frameworks['recommended']['name']}"
            )
        else:
            # Si no hay recomendación, usar Flask por defecto
            project_status[project_id]['framework'] = "Flask + Bootstrap + SQLite"
            project_status[project_id]['techstack'] = {
                'backend': 'flask',
                'frontend': 'bootstrap',
                'database': 'sqlite'
            }
            update_status(
                8, 
                "Analizando requisitos y seleccionando tecnologías...",
                "Stack tecnológico seleccionado por defecto: Flask + Bootstrap + SQLite"
            )

        # Get project directory
        project_dir = os.path.join(PROJECTS_DIR, project_id)

        # Create project structure directory
        os.makedirs(project_dir, exist_ok=True)

        # Stage 1: Analyzing requirements
        update_status(10, "Analizando requisitos...", "Iniciando análisis de requisitos")
        time.sleep(1)  # Reduce wait time

        # Create base structure
        os.makedirs(os.path.join(project_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'docs'), exist_ok=True)

        # Stage 2: Design
        update_status(20, "Diseñando la aplicación...", "Definiendo estructura")

        # Create README with features
        with open(os.path.join(project_dir, 'README.md'), 'w') as f:
            f.write(f"# Aplicación: {description}\n\n")
            f.write(f"## Características\n\n")
            for feature in features:
                f.write(f"- {feature}\n")
            f.write(f"\n## Instrucciones\n\n")
            f.write(f"1. Instalar dependencias: `pip install -r requirements.txt`\n")
            f.write(f"2. Ejecutar la aplicación: `python app.py`\n")

        # Stage 3: Generate app structure - faster and simpler
        update_status(40, "Generando estructura básica...", "Creando archivos principales")

        # Determine if it's a web app or CLI app based on features
        is_web_app = any(["web" in feature.lower() or
                          "ui" in feature.lower() or
                          "interfaz" in feature.lower() or
                          "página" in feature.lower() or
                          "frontend" in feature.lower() or
                          "html" in feature.lower()
                         for feature in features])

        # Create app.py - core file
        with open(os.path.join(project_dir, 'app.py'), 'w') as f:
            if is_web_app:
                f.write("""from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html', title="Aplicación Generada")

@app.route('/api/status')
def status():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
            else:
                f.write("""import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Aplicación CLI generada")
    parser.add_argument('--accion', type=str, help='Acción a realizar')
    args = parser.parse_args()

    print(f"Aplicación: {args.accion if args.accion else 'Sin acción especificada'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")

        # Create requirements.txt
        with open(os.path.join(project_dir, 'requirements.txt'), 'w') as f:
            if is_web_app:
                f.write("""flask==2.0.1
flask-cors==3.0.10
""")
            else:
                f.write("""# No external dependencies
""")

        # Create templates folder for web apps
        if is_web_app:
            os.makedirs(os.path.join(project_dir, 'templates'), exist_ok=True)
            os.makedirs(os.path.join(project_dir, 'static'), exist_ok=True)
            os.makedirs(os.path.join(project_dir, 'static', 'css'), exist_ok=True)
            os.makedirs(os.path.join(project_dir, 'static', 'js'), exist_ok=True)

            # Create index.html
            with open(os.path.join(project_dir, 'templates', 'index.html'), 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
    </header>
    <main>
        <div class="container">
            <div class="card">
                <h2>Aplicación generada correctamente</h2>
                <p>Esta es una aplicación generada automáticamente.</p>
                <div id="status">Cargando estado...</div>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; Aplicación generada por Codestorm Assistant</p>
    </footer>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>""")

            # Create CSS
            with open(os.path.join(project_dir, 'static', 'css', 'style.css'), 'w') as f:
                f.write("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

header {
    background-color: #333;
    color: white;
    padding: 1rem;
    text-align: center;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

.card {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 1rem;
    margin: 1rem 0;
}

footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
}""")

            # Create JS
            with open(os.path.join(project_dir, 'static', 'js', 'main.js'), 'w') as f:
                f.write("""document.addEventListener('DOMContentLoaded', function() {
    // Verificar el estado de la API
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('status').textContent = 'Estado del servidor: ' + data.status;
        })
        .catch(error => {
            document.getElementById('status').textContent = 'Error: ' + error.message;
        });
});""")

        update_status(60, "Implementando funcionalidades...", "Generando código específico")

        # Generate module files based on features
        for i, feature in enumerate(features[:5]):  # Limit to first 5 features to speed up
            # Sanitizar el nombre de la característica para usar como nombre de archivo
            feature_name = feature.lower().replace(' ', '_').replace('-', '_').replace(':', '_').replace(';', '_')
            # Eliminar caracteres especiales adicionales
            import re
            feature_name = re.sub(r'[^a-z0-9_]', '', feature_name)
            
            # Asegurarse de que no esté vacío y comience con una letra
            if not feature_name or not feature_name[0].isalpha():
                feature_name = f"feature_{i}"

            if is_web_app:
                # Add a route for this feature
                with open(os.path.join(project_dir, f'{feature_name}.py'), 'w') as f:
                    f.write(f"""# Módulo para la característica: {feature}

def get_{feature_name}_data():
    \"\"\"
    Obtiene datos para la característica {feature}
    \"\"\"
    return {{
        "name": "{feature}",
        "enabled": True,
        "description": "Implementación de {feature}"
    }}
""")

                # Add feature template
                os.makedirs(os.path.join(project_dir, 'templates'), exist_ok=True)
                with open(os.path.join(project_dir, 'templates', f'{feature_name}.html'), 'w') as f:
                    template_content = f"""
{{% extends "base.html" %}}

{{% block title %}}{feature}{{% endblock %}}

{{% block content %}}
<div class="feature-container">
    <h1>{feature}</h1>
    <div class="feature-content">
        <p>Esta es la página para la característica {feature}.</p>
    </div>
</div>
{{% endblock %}}"""
                    f.write(template_content)
            else:
                # Add a module for this feature
                with open(os.path.join(project_dir, f'{feature_name}.py'), 'w') as f:
                    f.write(f"""# Módulo para la característica: {feature}

class {feature_name.capitalize()}:
    \"\"\"
    Implementación de la característica {feature}
    \"\"\"

    def __init__(self):
        self.name = "{feature}"
        self.enabled = True

    def execute(self):
        \"\"\"
        Ejecuta la funcionalidad principal
        \"\"\"
        print(f"Ejecutando {self.name}...")
        return True

    def get_info(self):
        \"\"\"
        Devuelve información sobre esta característica
        \"\"\"
        return {{
            "name": self.name,
            "enabled": self.enabled,
            "type": "CLI Feature"
        }}
""")

            # Update progress incrementally
            progress = 60 + int((i+1) * 30 / len(features[:5]))
            update_status(progress, f"Implementando característica: {feature}", f"Generando código para {feature}")
            # Breve pausa para evitar bloqueos
            time.sleep(0.5)

        # Stage 4: Create a base template for web apps
        if is_web_app:
            with open(os.path.join(project_dir, 'templates', 'base.html'), 'w') as f:
                base_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Aplicación{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header>
        <h1>Aplicación</h1>
        <nav>
            <ul>
                <li><a href="/">Inicio</a></li>
                {% for feature in features %}
                <li><a href="/{{ feature.url }}">{{ feature.name }}</a></li>
                {% endfor %}
            </ul>
        </nav>
    </header>

    <main>
        <div class="container">
            {% block content %}{% endblock %}
        </div>
    </main>

    <footer>
        <p>&copy; Aplicación generada por Codestorm Assistant</p>
    </footer>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>"""
                f.write(base_template)

        # Create a zip file of the project
        update_status(95, "Finalizando...", "Preparando archivos para descarga")
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

        # Determine appropriate frameworks based on description
        frameworks = determine_frameworks(description_lower)

        # Limit to a reasonable number of features
        features = features[:10]

        return jsonify({
            'success': True,
            'features': features,
            'frameworks': frameworks
        })
    except Exception as e:
        logging.error(f"Error analyzing features: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def determine_frameworks(description):
    """
    Determina los frameworks más adecuados basándose en la descripción
    del proyecto y devuelve una estructura con opciones y recomendaciones.
    """
    frameworks = {
        'backend': [],
        'frontend': [],
        'database': [],
        'recommended': None
    }

    # Detectar frameworks de backend
    backend_frameworks = [
        {
            'id': 'flask',
            'name': 'Flask',
            'description': 'Framework web ligero y flexible para Python',
            'use_cases': 'APIs, aplicaciones web pequeñas y medianas, microservicios',
            'score': 0
        },
        {
            'id': 'django',
            'name': 'Django',
            'description': 'Framework web completo para Python con admin incorporado',
            'use_cases': 'CMS, grandes aplicaciones web, sitios complejos',
            'score': 0
        },
        {
            'id': 'fastapi',
            'name': 'FastAPI',
            'description': 'Framework web moderno y rápido con validación automática',
            'use_cases': 'APIs REST de alto rendimiento, microservicios',
            'score': 0
        },
        {
            'id': 'streamlit',
            'name': 'Streamlit',
            'description': 'Framework para crear aplicaciones de datos interactivas',
            'use_cases': 'Dashboards, visualización de datos, prototipos rápidos',
            'score': 0
        },
        {
            'id': 'express',
            'name': 'Express.js',
            'description': 'Framework web minimalista para Node.js',
            'use_cases': 'APIs, aplicaciones web en tiempo real, microservicios',
            'score': 0
        },
        {
            'id': 'nestjs',
            'name': 'NestJS',
            'description': 'Framework progresivo para Node.js con TypeScript',
            'use_cases': 'Aplicaciones escalables del lado del servidor',
            'score': 0
        }
    ]

    # Puntuar frameworks de backend según la descripción
    for framework in backend_frameworks:
        if framework['id'] in description:
            framework['score'] += 10

        if 'api' in description and framework['id'] in ['fastapi', 'express', 'flask']:
            framework['score'] += 5

        if 'dashboard' in description and framework['id'] in ['streamlit', 'django']:
            framework['score'] += 5

        if 'datos' in description and framework['id'] in ['streamlit']:
            framework['score'] += 8

        if 'microservicio' in description and framework['id'] in ['fastapi', 'flask', 'express']:
            framework['score'] += 5

        if 'admin' in description and framework['id'] in ['django']:
            framework['score'] += 8

        if ('simple' in description or 'sencillo' in description) and framework['id'] in ['flask', 'express', 'streamlit']:
            framework['score'] += 3

        if 'completo' in description and framework['id'] in ['django', 'nestjs']:
            framework['score'] += 3

    # Ordenar y seleccionar los mejores frameworks de backend
    backend_frameworks.sort(key=lambda x: x['score'], reverse=True)
    frameworks['backend'] = backend_frameworks[:3]  # Top 3 backends

    # Detectar frameworks de frontend
    frontend_frameworks = [
        {
            'id': 'react',
            'name': 'React',
            'description': 'Biblioteca para construir interfaces de usuario',
            'use_cases': 'SPAs, interfaces dinámicas, aplicaciones complejas',
            'score': 0
        },
        {
            'id': 'vue',
            'name': 'Vue.js',
            'description': 'Framework progresivo para construir interfaces de usuario',
            'use_cases': 'Aplicaciones web de cualquier tamaño, integraciones progresivas',
            'score': 0
        },
        {
            'id': 'angular',
            'name': 'Angular',
            'description': 'Framework completo para aplicaciones web',
            'use_cases': 'Aplicaciones empresariales, proyectos a gran escala',
            'score': 0
        },
        {
            'id': 'svelte',
            'name': 'Svelte',
            'description': 'Compilador en lugar de framework, con menor tamaño de bundle',
            'use_cases': 'Interfaces rápidas, aplicaciones con rendimiento optimizado',
            'score': 0
        },
        {
            'id': 'bootstrap',
            'name': 'Bootstrap',
            'description': 'Framework CSS para diseño responsivo',
            'use_cases': 'Prototipos rápidos, interfaces consistentes',
            'score': 0
        }
    ]

    # Puntuar frameworks de frontend según la descripción
    for framework in frontend_frameworks:
        if framework['id'] in description:
            framework['score'] += 10

        if 'móvil' in description and framework['id'] in ['react', 'vue']:
            framework['score'] += 3

        if 'responsive' in description and framework['id'] in ['bootstrap']:
            framework['score'] += 5

        if 'componentes' in description and framework['id'] in ['react', 'vue', 'angular', 'svelte']:
            framework['score'] += 3

        if 'empresarial' in description and framework['id'] in ['angular']:
            framework['score'] += 5

        if 'rendimiento' in description and framework['id'] in ['svelte']:
            framework['score'] += 5

    # Ordenar y seleccionar los mejores frameworks de frontend
    frontend_frameworks.sort(key=lambda x: x['score'], reverse=True)
    frameworks['frontend'] = frontend_frameworks[:3]  # Top 3 frontends

    # Detectar bases de datos
    database_options = [
        {
            'id': 'sqlite',
            'name': 'SQLite',
            'description': 'Base de datos relacional ligera sin servidor',
            'use_cases': 'Aplicaciones pequeñas, prototipos, almacenamiento local',
            'score': 0
        },
        {
            'id': 'mysql',
            'name': 'MySQL',
            'description': 'Sistema de gestión de bases de datos relacional',
            'use_cases': 'Aplicaciones web tradicionales, CMS, comercio electrónico',
            'score': 0
        },
        {
            'id': 'postgresql',
            'name': 'PostgreSQL',
            'description': 'Sistema de base de datos relacional avanzado',
            'use_cases': 'Aplicaciones complejas, datos geoespaciales, escalabilidad',
            'score': 0
        },
        {
            'id': 'mongodb',
            'name': 'MongoDB',
            'description': 'Base de datos NoSQL orientada a documentos',
            'use_cases': 'Aplicaciones con datos variables, APIs, microservicios',
            'score': 0
        },
        {
            'id': 'redis',
            'name': 'Redis',
            'description': 'Almacén de estructura de datos en memoria',
            'use_cases': 'Caché, tiempo real, colas de mensajes, leaderboards',
            'score': 0
        }
    ]

    # Puntuar bases de datos según la descripción
    for db in database_options:
        if db['id'] in description:
            db['score'] += 10

        if 'sql' in description and db['id'] in ['mysql', 'postgresql', 'sqlite']:
            db['score'] += 5

        if 'nosql' in description and db['id'] in ['mongodb']:
            db['score'] += 8

        if 'simple' in description and db['id'] in ['sqlite']:
            db['score'] += 5

        if 'escalable' in description and db['id'] in ['postgresql', 'mongodb']:
            db['score'] += 5

        if 'tiempo real' in description and db['id'] in ['redis', 'mongodb']:
            db['score'] += 5

    # Ordenar y seleccionar las mejores bases de datos
    database_options.sort(key=lambda x: x['score'], reverse=True)
    frameworks['database'] = database_options[:3]  # Top 3 databases

    # Recomendar una combinación de tecnologías basada en los puntajes
    if len(frameworks['backend']) > 0 and len(frameworks['frontend']) > 0:
        backend_choice = frameworks['backend'][0]['name']
        frontend_choice = frameworks['frontend'][0]['name']
        database_choice = frameworks['database'][0]['name'] if len(frameworks['database']) > 0 else "SQLite"

        frameworks['recommended'] = {
            'name': f"{backend_choice} + {frontend_choice} + {database_choice}",
            'description': f"Stack recomendado basado en tu descripción",
            'backend': frameworks['backend'][0],
            'frontend': frameworks['frontend'][0],
            'database': frameworks['database'][0] if len(frameworks['database']) > 0 else None
        }

    return frameworks

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
        tech_data = data.get('tech_data', {})  # Nuevos datos de tecnología

        if not description:
            return jsonify({
                'success': False,
                'error': 'Se requiere una descripción del proyecto'
            }), 400
            
        # Procesar datos de tecnología si existen
        if tech_data:
            # Añadir información de tecnología al estado del proyecto
            if isinstance(tech_data, str):
                try:
                    tech_data = json.loads(tech_data)
                except:
                    tech_data = {}
                    
            # Añadir características basadas en tecnologías seleccionadas
            if isinstance(tech_data, dict):
                # Añadir framework backend como característica
                if tech_data.get('backend'):
                    backend_feature = f"Backend: {tech_data.get('backend')}"
                    if backend_feature not in features:
                        features.append(backend_feature)
                
                # Añadir framework frontend como característica
                if tech_data.get('frontend'):
                    frontend_feature = f"Frontend: {tech_data.get('frontend')}"
                    if frontend_feature not in features:
                        features.append(frontend_feature)
                
                # Añadir base de datos como característica
                if tech_data.get('database'):
                    db_feature = f"Base de datos: {tech_data.get('database')}"
                    if db_feature not in features:
                        features.append(db_feature)
                
                # Añadir características adicionales
                if tech_data.get('features') and isinstance(tech_data.get('features'), list):
                    for feature in tech_data.get('features'):
                        if feature and feature not in features:
                            features.append(feature)

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
        # Si el proyecto no existe, verificar si es un error de formato o si debemos crear un proyecto temporal
        if project_id not in project_status:
            # Si parece tener un formato válido, crear un estado temporal
            if project_id.startswith('app_') and '_' in project_id:
                logging.warning(f"Project {project_id} not found, creating temporary status")

                # Crear estado temporal para resolver los errores 404
                project_status[project_id] = {
                    'status': 'in_progress',
                    'progress': 60,
                    'current_stage': 'Procesando solicitud...',
                    'console_messages': [
                        {
                            'time': time.time(),
                            'message': "Recuperando estado del proyecto..."
                        }
                    ],
                    'start_time': time.time(),
                    'completion_time': None,
                    'framework': 'Flask + Bootstrap + SQLite',
                    'techstack': {
                        'backend': 'flask',
                        'frontend': 'bootstrap',
                        'database': 'sqlite'
                    }
                }

                # Crear directorio del proyecto si no existe
                project_dir = os.path.join(PROJECTS_DIR, project_id)
                os.makedirs(project_dir, exist_ok=True)

                # Iniciar un nuevo proceso de generación en segundo plano
                thread = Thread(
                    target=generate_application,
                    args=(
                        project_id,
                        "Proyecto recuperado automáticamente",
                        "developer",
                        "openai",
                        {"includeTests": False, "includeDocs": True},
                        ["Funcionalidad básica", "Interfaz de usuario", "Documentación"]
                    )
                )
                thread.daemon = True
                thread.start()
            else:
                return jsonify({
                    'success': False,
                    'error': 'Proyecto no encontrado'
                }), 404

        status_data = project_status[project_id]

        # Get the most recent console message if any
        console_message = None
        if status_data.get('console_messages'):
            console_message = status_data['console_messages'][-1]['message']

        # Si no tiene framework, añadir uno predeterminado
        if 'framework' not in status_data:
            status_data['framework'] = 'Flask + Bootstrap + SQLite'
            status_data['techstack'] = {
                'backend': 'flask',
                'frontend': 'bootstrap',
                'database': 'sqlite'
            }

        return jsonify({
            'success': True,
            'project_id': project_id,
            'status': status_data.get('status', 'in_progress'),
            'progress': status_data.get('progress', 60),
            'current_stage': status_data.get('current_stage', 'Procesando...'),
            'console_message': console_message,
            'error': status_data.get('error'),
            'framework': status_data.get('framework'),
            'techstack': status_data.get('techstack', {})
        })
    except Exception as e:
        logging.error(f"Error checking project status: {str(e)}")
        # Devolver una respuesta con algo de información en lugar de error
        return jsonify({
            'success': True,
            'project_id': project_id,
            'status': 'in_progress',
            'progress': 60,
            'current_stage': f'Recuperando estado... ({str(e)[:50]})',
            'console_message': f"Intentando recuperar el estado del proyecto: {str(e)[:100]}",
            'error': None
        })

# Route to download a generated project
@constructor_bp.route('/api/constructor/download/<project_id>', methods=['GET'])
def download_project(project_id):
    try:
        # Check if the project exists and is completed
        if project_id not in project_status:
            # Si no existe en memoria, verificar si existe el archivo zip directamente
            zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
            if os.path.exists(zip_path):
                # Si existe el archivo, permitir la descarga aunque no esté en memoria
                return send_file(
                    zip_path,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=f"{project_id}.zip"
                )
            else:
                # Verificar si existe el directorio del proyecto
                project_dir = os.path.join(PROJECTS_DIR, project_id)
                if os.path.exists(project_dir):
                    # Crear un archivo zip para este proyecto
                    zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(project_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, project_dir)
                                zipf.write(file_path, arcname)
                    
                    # Retornar el archivo zip recién creado
                    return send_file(
                        zip_path,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=f"{project_id}.zip"
                    )
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Proyecto no encontrado'
                    }), 404

        if project_status[project_id]['status'] != 'completed' and project_status[project_id].get('status') != 'failed':
            # Si el proyecto falló, igual intentamos crear un ZIP con lo que tengamos
            if project_status[project_id].get('status') == 'failed':
                project_dir = os.path.join(PROJECTS_DIR, project_id)
                if os.path.exists(project_dir):
                    # Crear zip del directorio existente
                    zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(project_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, project_dir)
                                zipf.write(file_path, arcname)
                    
                    # Retornar el archivo zip
                    return send_file(
                        zip_path,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=f"{project_id}.zip"
                    )
            
            # Si no está completado ni falló, mostrar mensaje de error
            return jsonify({
                'success': False,
                'error': f"El proyecto aún no está listo. Estado actual: {project_status[project_id].get('status', 'desconocido')}"
            }), 400

        # Project zip file path
        zip_path = os.path.join(PROJECTS_DIR, f"{project_id}.zip")
        if not os.path.exists(zip_path):
            # Si no existe el zip pero el proyecto está marcado como completado, recrearlo
            project_dir = os.path.join(PROJECTS_DIR, project_id)
            if os.path.exists(project_dir):
                # Crear zip del directorio existente
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, project_dir)
                            zipf.write(file_path, arcname)
            else:
                # Crear un proyecto mínimo para evitar errores
                project_dir = os.path.join(PROJECTS_DIR, project_id)
                os.makedirs(project_dir, exist_ok=True)
                
                # Crear un archivo README con información del error
                with open(os.path.join(project_dir, 'README.md'), 'w') as f:
                    f.write(f"# Proyecto: {project_id}\n\n")
                    f.write("Este proyecto tuvo un error durante la generación.\n")
                    if project_id in project_status and 'error' in project_status[project_id]:
                        f.write(f"\nError: {project_status[project_id]['error']}\n")
                
                # Crear un archivo index.html simple
                os.makedirs(os.path.join(project_dir, 'templates'), exist_ok=True)
                with open(os.path.join(project_dir, 'templates', 'index.html'), 'w') as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Proyecto con Error</title>
</head>
<body>
    <h1>Error en la generación del proyecto</h1>
    <p>Se produjo un error durante la generación de este proyecto.</p>
</body>
</html>""")
                
                # Crear app.py simple
                with open(os.path.join(project_dir, 'app.py'), 'w') as f:
                    f.write("""from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
                
                # Crear el zip con estos archivos mínimos
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, project_dir)
                            zipf.write(file_path, arcname)

        # Return the zip file
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{project_id}.zip"
        )
    except Exception as e:
        logging.error(f"Error downloading project: {str(e)}")
        # En caso de error crítico, crear un ZIP mínimo con información del error
        try:
            project_dir = os.path.join(PROJECTS_DIR, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            with open(os.path.join(project_dir, 'ERROR.txt'), 'w') as f:
                f.write(f"Error al descargar el proyecto: {str(e)}\n")
            
            zip_path = os.path.join(PROJECTS_DIR, f"{project_id}_error.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(os.path.join(project_dir, 'ERROR.txt'), 'ERROR.txt')
            
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{project_id}_error.zip"
            )
        except Exception as inner_e:
            logging.error(f"Error crítico al intentar generar ZIP de error: {str(inner_e)}")
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

@constructor_bp.route('/start_construction', methods=['POST'])
def start_construction():
    """Start the construction process based on the plan"""
    data = request.json
    plan_id = data.get('plan_id')

    if not plan_id:
        return jsonify({'error': 'No plan ID provided'}), 400

    # Get the plan from the database or session
    # For now, we'll just return a mock response

    # Here you would start the actual construction process
    # This would involve generating files, installing dependencies, etc.

    return jsonify({
        'success': True,
        'message': 'Construction started',
        'plan_id': plan_id,
        'status': 'in_progress',
    })

@constructor_bp.route('/pause_construction', methods=['POST'])
def pause_construction():
    """Pause the ongoing construction process"""
    data = request.json
    plan_id = data.get('plan_id')
    reason = data.get('reason', 'User requested pause')

    if not plan_id:
        return jsonify({'error': 'No plan ID provided'}), 400

    # Logic to pause the construction process
    # This could involve setting a flag in the database

    return jsonify({
        'success': True,
        'message': f'Construction paused: {reason}',
        'plan_id': plan_id,
        'status': 'paused',
    })

@constructor_bp.route('/resume_construction', methods=['POST'])
def resume_construction():
    """Resume a paused construction process"""
    data = request.json
    plan_id = data.get('plan_id')

    if not plan_id:
        return jsonify({'error': 'No plan ID provided'}), 400

    # Logic to resume the construction process

    return jsonify({
        'success': True,
        'message': 'Construction resumed',
        'plan_id': plan_id,
        'status': 'in_progress',
    })

@constructor_bp.route('/construction_status', methods=['GET'])
def construction_status():
    """Get the current status of a construction process"""
    plan_id = request.args.get('plan_id')

    if not plan_id:
        return jsonify({'error': 'No plan ID provided'}), 400

    # Logic to get the construction status

    # Mock response for demonstration
    return jsonify({
        'plan_id': plan_id,
        'status': 'in_progress',  # or 'paused', 'completed', 'failed'
        'progress': 60,
        'current_step': 'Generating application files',
        'is_paused': False,
        'time_elapsed': '00:02:45',
        'estimated_time_remaining': '00:01:30'
    })