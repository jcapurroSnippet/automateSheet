"""
Módulo de autenticación con Google Sheets API
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config_rif import RIFConfig as Config

class GoogleSheetsAuth:
    def __init__(self):
        self.credentials = None
        self.service = None
    
    def authenticate(self):
        """
        Autentica con Google Sheets API
        """
        try:
            print("🔐 Iniciando autenticación con Google Sheets API...")
            
            # Cargar credenciales existentes
            if os.path.exists(Config.TOKEN_PATH):
                self.credentials = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)
                print("✅ Token de autenticación cargado")
            
            # Si no hay credenciales válidas, obtener nuevas
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print("🔄 Refrescando token de autenticación...")
                    self.credentials.refresh(Request())
                else:
                    print("🔑 Obteniendo nuevas credenciales...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        Config.CREDENTIALS_PATH, Config.SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Guardar credenciales para uso futuro
                with open(Config.TOKEN_PATH, 'w') as token:
                    token.write(self.credentials.to_json())
                print("💾 Credenciales guardadas para uso futuro")
            
            # Construir el servicio de Google Sheets
            self.service = build('sheets', 'v4', credentials=self.credentials)
            print("✅ Autenticación exitosa con Google Sheets API")
            
            return self.service
            
        except FileNotFoundError:
            print("❌ Error: No se encontró el archivo de credenciales")
            print(f"📁 Asegúrate de que {Config.CREDENTIALS_PATH} existe")
            raise
        except Exception as error:
            print(f"❌ Error en la autenticación: {error}")
            raise
    
    def get_service(self):
        """
        Obtiene el servicio de Google Sheets
        """
        if not self.service:
            raise Exception("No se ha autenticado. Llama a authenticate() primero.")
        return self.service
    
    def is_authenticated(self):
        """
        Verifica si está autenticado
        """
        return self.service is not None
