"""
Script de configuración inicial para RIF Scheduler
"""

import os
import sys
import subprocess

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 7):
        print("ERROR: Se requiere Python 3.7 o superior")
        return False
    print(f"Python {sys.version.split()[0]} detectado")
    return True

def install_requirements():
    """Instala las dependencias"""
    try:
        print("Instalando dependencias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR al instalar dependencias: {e}")
        return False

def create_env_file():
    """Crea el archivo config.env si no existe"""
    env_path = "config.env"
    env_example_path = "config.env.example"
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            print("Creando archivo config.env...")
            with open(env_example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Archivo config.env creado")
        else:
            print("ERROR: No se encontró config.env.example")
            return False
    else:
        print("Archivo config.env ya existe")
    return True

def check_credentials():
    """Verifica si existen las credenciales"""
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print("\nIMPORTANTE: No se encontró credentials.json")
        print("Para continuar, necesitas:")
        print("   1. Ir a Google Cloud Console")
        print("   2. Habilitar Google Sheets API")
        print("   3. Crear credenciales OAuth 2.0")
        print("   4. Descargar el archivo JSON como credentials.json")
        return False
    else:
        print("Archivo credentials.json encontrado")
        return True

def main():
    """Función principal de configuración"""
    print("Configuración inicial de RIF Scheduler\n")
    
    # Verificar versión de Python
    if not check_python_version():
        return False
    
    # Crear archivo config.env
    if not create_env_file():
        return False
    
    # Instalar dependencias
    if not install_requirements():
        return False
    
    # Verificar credenciales
    credentials_ok = check_credentials()
    
    print("\nProximos pasos:")
    print("   1. Configura los IDs de tus sheets en config.env")
    print("   2. Configura los rangos de datos en config.env")
    if not credentials_ok:
        print("   3. Configura las credenciales de Google (credentials.json)")
    print("   4. Ejecuta: python rif_scheduler.py")
    print("\nPara más información, consulta GUIA_RIF.md")
    
    return True

if __name__ == "__main__":
    main()