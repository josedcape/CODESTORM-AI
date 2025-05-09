
#!/usr/bin/env python3
"""
Utilidad para recargar las variables de entorno desde .env
Esto puede ser útil cuando se actualizan las claves API y se quiere
recargar sin reiniciar completamente la aplicación.
"""
import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def reload_env():
    """Recarga las variables de entorno desde el archivo .env"""
    try:
        # Comprobar si el archivo .env existe
        if not os.path.exists('.env'):
            print("❌ Error: Archivo .env no encontrado.")
            print("Por favor, crea un archivo .env con las siguientes variables:")
            print("  OPENAI_API_KEY=tu_clave_openai_aqui")
            print("  ANTHROPIC_API_KEY=tu_clave_anthropic_aqui")
            print("  GEMINI_API_KEY=tu_clave_gemini_aqui")
            return False
            
        # Cargar las variables de entorno
        load_dotenv(dotenv_path='.env', override=True)
        
        # Verificar si se cargaron las claves API
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        print("\n" + "="*50)
        print("ESTADO DE LAS VARIABLES DE ENTORNO")
        print("="*50)
        
        if openai_key:
            masked_key = f"{openai_key[:5]}...{openai_key[-5:]}" if len(openai_key) > 10 else "***configurada***"
            print(f"✅ OPENAI_API_KEY: {masked_key}")
        else:
            print("❌ OPENAI_API_KEY: No configurada")
            
        if anthropic_key:
            masked_key = f"{anthropic_key[:5]}...{anthropic_key[-5:]}" if len(anthropic_key) > 10 else "***configurada***"
            print(f"✅ ANTHROPIC_API_KEY: {masked_key}")
        else:
            print("❌ ANTHROPIC_API_KEY: No configurada")
            
        if gemini_key:
            masked_key = f"{gemini_key[:5]}...{gemini_key[-5:]}" if len(gemini_key) > 10 else "***configurada***"
            print(f"✅ GEMINI_API_KEY: {masked_key}")
        else:
            print("❌ GEMINI_API_KEY: No configurada")
            
        print("\nNota: Debes reiniciar la aplicación para que los cambios surtan efecto.")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error al recargar variables de entorno: {str(e)}")
        logging.error(f"Error al recargar variables de entorno: {str(e)}")
        return False

if __name__ == "__main__":
    print("Recargando variables de entorno desde .env...")
    success = reload_env()
    if success:
        print("\n✅ Variables de entorno recargadas exitosamente.")
    else:
        print("\n❌ Error al recargar variables de entorno.")
        sys.exit(1)
