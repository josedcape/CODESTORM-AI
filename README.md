# CODESTORM - Asistente de Terminal con IA

CODESTORM es un asistente de terminal impulsado por inteligencia artificial que permite a los usuarios convertir instrucciones en lenguaje natural a comandos de terminal. La aplicación proporciona una interfaz interactiva con un explorador de archivos integrado y soporte para múltiples modelos de IA.

## Características

- 🤖 Utiliza modelos de IA como OpenAI GPT, Anthropic Claude y Google Gemini
- 💻 Convierte instrucciones en lenguaje natural a comandos de terminal
- 📁 Explorador de archivos integrado para navegar, crear, editar y eliminar archivos
- 🔄 Actualizaciones en tiempo real mediante WebSockets
- 💾 Historial de comandos para referencia y reutilización
- 🌐 Soporte para múltiples espacios de trabajo
- ⚡ Caché local para comandos comunes, mejorando el tiempo de respuesta
- 🔍 Resaltado de sintaxis para código

## Instalación

1. Clonar el repositorio:
```
git clone https://github.com/josedcape/CODESTORM.git
cd CODESTORM
```

2. Instalar dependencias:
```
pip install -r requirements.txt
```

3. Configurar las claves API (crea un archivo `.env` con el siguiente contenido):
```
OPENAI_API_KEY=tu_clave_de_openai
ANTHROPIC_API_KEY=tu_clave_de_anthropic
GEMINI_API_KEY=tu_clave_de_gemini
```

4. Iniciar la aplicación:
```
python main.py
```

## Uso

1. Abrir la aplicación en el navegador (http://localhost:5000)
2. Escribir instrucciones en lenguaje natural en el campo de entrada
3. Seleccionar el modelo de IA deseado (OpenAI, Anthropic, Gemini)
4. Hacer clic en "Ejecutar" para convertir la instrucción en un comando de terminal
5. Ver el resultado del comando en la salida de la terminal
6. Usar el explorador de archivos para gestionar tus archivos

### Ejemplos de comandos

- "Mostrar archivos en el directorio actual"
- "Crear una carpeta llamada proyectos"
- "Mostrar la fecha y hora actual"
- "Crear un archivo llamado hola.txt"
- "Mostrar el contenido de README.md"

## Estructura del proyecto

```
CODESTORM/
├── app.py              # Aplicación Flask principal
├── main.py             # Punto de entrada
├── models.py           # Modelos de base de datos
├── static/             # Archivos estáticos (CSS, JS)
│   ├── css/            # Hojas de estilo
│   └── js/             # Scripts JavaScript
├── templates/          # Plantillas HTML
├── user_workspaces/    # Espacios de trabajo de usuarios
└── .env                # Variables de entorno (no incluido en el repositorio)
```

## Tecnologías utilizadas

- Flask: Framework web
- Flask-SocketIO: Comunicación en tiempo real
- SQLAlchemy: ORM para base de datos
- OpenAI API: Modelo GPT-4o para procesamiento de lenguaje natural
- Anthropic API: Modelo Claude para procesamiento de lenguaje natural
- Google Gemini API: Modelo Gemini para procesamiento de lenguaje natural
- Bootstrap: Framework CSS para la interfaz de usuario

## Contribuir

Las contribuciones son bienvenidas. Por favor, siente libre de abrir un issue o enviar un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.