# Codestorm Assistant

![Codestorm Assistant](generated-icon.png)

Un asistente avanzado para desarrollo de código impulsado por inteligencia artificial, creado para facilitar la programación mediante instrucciones en lenguaje natural.

## 🌟 Características Principales

- **Múltiples agentes especializados**: Desarrollador, Arquitecto y Experto Avanzado
- **Soporte para múltiples modelos de IA**: OpenAI (GPT-4o), Anthropic (Claude) y Google Gemini
- **Interfaz web intuitiva**: Panel de control completo con editor, terminal y chat integrados
- **Generación de archivos complejos**: HTML, CSS, JavaScript, Python y más
- **Ejecución de comandos**: Controla tu terminal mediante lenguaje natural
- **APIs completas**: Endpoints para todas las funcionalidades
- **WebSockets**: Actualizaciones en tiempo real para archivos y comandos
- **Workspaces aislados**: Entornos de trabajo separados para diferentes usuarios/proyectos

## 💼 Componentes del Sistema

### Principales Dependencias
- **Framework Web**:
  - Flask y sus extensiones (Flask-Cors, Flask-SocketIO, Flask-SQLAlchemy)
  - Gunicorn (para servir la aplicación)
- **Integraciones de IA**:
  - OpenAI API (GPT-4o)
  - Anthropic API (Claude)
  - Google Generative AI (Gemini)
- **Base de datos**:
  - SQLAlchemy
  - PostgreSQL (psycopg2-binary)
- **Utilidades**:
  - Python-dotenv (para variables de entorno)
  - Requests (para llamadas HTTP)
  - Eventlet (para manejo asíncrono)
  - GitPython y PyGitHub (para integración con Git)

### Configuración del Servidor
- El servidor está configurado para ejecutarse con Gunicorn en el puerto 5000
- Workflows configurados:
  - "Run CODESTORM" (principal)
  - "Start application"
  - "Run Application"
  - "Check API Keys"

### Sistema Multiagente Implementado
- **Agente General**: Asistente versátil para tareas diversas
- **Agente Desarrollador**: Especializado en escribir y depurar código
- **Agente Arquitecto**: Enfocado en diseño de sistemas y estructuras
- **Agente Avanzado**: Para soluciones técnicas complejas y optimizaciones

## 🚀 Inicio Rápido

### Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/josedcape/CODESTORM.git
   cd CODESTORM
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura las claves API en un archivo `.env`:
   ```
   OPENAI_API_KEY=tu_clave_aquí
   ANTHROPIC_API_KEY=tu_clave_aquí
   GEMINI_API_KEY=tu_clave_aquí
   SECRET_KEY=una_clave_secreta_para_flask
   ```

### Uso

#### Aplicación Web Completa

```bash
python main_completo.py
```

La aplicación estará disponible en `http://localhost:5000`

#### CLI Interactivo

```bash
python asistente_completo.py interact
```

#### Comandos Específicos

Generar un archivo con IA:
```bash
python asistente_completo.py generate "Crear una página web de portafolio personal con secciones para habilidades y proyectos" --type html --filename portfolio.html
```

Ejecutar un comando:
```bash
python asistente_completo.py exec "ls -la"
```

Procesar instrucción en lenguaje natural:
```bash
python asistente_completo.py process "genera un programa en Python que calcule los números primos"
```

## 🧠 Agentes Especializados

### Desarrollador
Especializado en escribir código de alta calidad, bien documentado y eficiente. Ideal para implementaciones técnicas detalladas.

### Arquitecto
Especializado en diseño de sistemas y componentes, patrones de diseño y estructura general. Perfecto para planificar aplicaciones.

### Experto Avanzado
Especializado en soluciones complejas con optimizaciones avanzadas. Ideal para problemas técnicos desafiantes y rendimiento.

## 📄 API Endpoints

La aplicación ofrece un conjunto completo de APIs:

- `GET /api/files`: Listar archivos del workspace
- `POST /api/files/create`: Crear o actualizar un archivo
- `GET /api/files/read`: Leer el contenido de un archivo
- `DELETE /api/files/delete`: Eliminar un archivo
- `POST /api/execute`: Ejecutar un comando
- `POST /api/chat`: Interactuar con un agente especializado
- `POST /api/process-code`: Procesar y mejorar código
- `POST /api/generate-file`: Generar archivos complejos
- `POST /api/process-instruction`: Procesar instrucciones en lenguaje natural

## 📋 Ejemplos de Uso

### Crear un archivo HTML
```
ejecutar: crear un archivo HTML con una página web personal
```

### Ejecutar comandos
```
ejecutar: ls -la
```

### Preguntar al asistente
```
¿Cuáles son los mejores patrones de diseño para una API REST?
```

## 📊 Estructura del Proyecto

```
CODESTORM/
├── main_completo.py           # Aplicación web principal
├── asistente_completo.py      # CLI interactivo
├── agents_utils.py            # Utilidades para agentes IA
├── agents_generators.py       # Generadores de contenido
├── static/                    # Archivos estáticos
│   ├── css/                   # Estilos CSS
│   └── js/                    # Scripts JavaScript
├── templates/                 # Plantillas HTML
├── user_workspaces/           # Workspaces de usuario
└── .env                       # Variables de entorno
```

## 🔧 Tecnologías Utilizadas

- **Backend**: Python, Flask, SocketIO
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **IA**: OpenAI API, Anthropic API, Google Gemini API
- **Otros**: WebSockets, SQLite (para almacenamiento)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add amazing feature'`)
4. Haz push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está licenciado bajo los términos de la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

José - [@josedcape](https://github.com/josedcape)

Link del proyecto: [https://github.com/josedcape/CODESTORM](https://github.com/josedcape/CODESTORM)
# Constructor de Aplicaciones

Este proyecto permite la creación rápida de aplicaciones web y APIs basadas en diversos stacks tecnológicos.

## Características Principales

- Selección de tecnologías backend y frontend
- Generación de código estructurado y funcional
- Creación de archivos estáticos (HTML, CSS, JavaScript)
- Configuración automática de dependencias
- Documentación integrada

## Archivos Generados

El constructor puede generar los siguientes tipos de archivos:

- **README.md**: Documentación del proyecto
- **app.js**: Archivo principal de JavaScript
- **index.html**: Estructura HTML del proyecto
- **style.css**: Estilos CSS
- **package.json**: Configuración de dependencias

## Uso

1. Seleccione el stack tecnológico
2. Configure las opciones adicionales
3. Seleccione los archivos a generar
4. Proporcione una descripción del proyecto
5. Haga clic en "Generar Aplicación"

## Ejemplo

```javascript
// Ejemplo de app.js generado
const app = {
  init: function() {
    console.log('Aplicación inicializada');
    this.setupEventListeners();
  },
  
  setupEventListeners: function() {
    document.addEventListener('DOMContentLoaded', this.onDocumentReady.bind(this));
  },
  
  onDocumentReady: function() {
    console.log('Documento listo');
  }
};

app.init();
```
