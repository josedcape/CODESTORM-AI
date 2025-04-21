import os
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'codestorm-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB máximo para uploads

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Codestorm Assistant funcionando correctamente'})

    @app.route('/')
    def root():
        from flask import redirect
        return redirect('/codestorm')

    # Importar el blueprint de Codestorm después de asegurar que la app está definida
    from codestorm_app import app as codestorm_blueprint
    
    # Registrar el blueprint de Codestorm bajo la URL /codestorm
    app.register_blueprint(codestorm_blueprint, url_prefix='/codestorm')
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)