# Main entry point for the Flask application
from app import app, socketio

# Configurar un manejador para verificar la salud de la aplicación
@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
