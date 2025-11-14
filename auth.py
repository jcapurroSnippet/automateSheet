"""
Módulo de autenticación con Google Sheets API
Usa OAuth 2.0 (credentials.json como OAuth client + token.json como autorización)
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config_rif import RIFConfig as Config

class GoogleSheetsAuth:
    def __init__(self):
        self.credentials = None
        self.service = None

    def authenticate(self):
        """
        Autentica con Google Sheets API usando OAuth 2.0.
        Prioridad:
        1. token.json (archivo local con autorización guardada)
        2. credentials.json (OAuth client) → flujo interactivo si token.json no existe
        """
        try:
            print("🔐 Iniciando autenticación con OAuth...")

            token_path = "token.json"
            credentials_path = "credentials.json"

            # Opción A: Usar token.json existente
            if os.path.exists(token_path):
                print("✓ Cargando autorización desde token.json")
                self.credentials = Credentials.from_authorized_user_file(
                    token_path,
                    scopes=Config.SCOPES
                )
                # Refrescar token si es necesario
                if self.credentials.expired and self.credentials.refresh_token:
                    print("✓ Refrescando token...")
                    request = Request()
                    self.credentials.refresh(request)
            else:
                # Opción B: Crear nuevo token desde credentials.json (flujo interactivo)
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"No se encontró {credentials_path}.\n"
                        f"Descarga el OAuth client JSON desde Google Cloud Console.\n"
                        f"Colócalo como 'credentials.json' en este directorio."
                    )
                
                print(f"✓ Cargando OAuth client desde {credentials_path}")
                print("✓ Iniciando flujo de autorización (se abrirá el navegador)...")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path,
                    scopes=Config.SCOPES
                )
                self.credentials = flow.run_local_server(port=0)
                
                # Guardar token para futuras ejecuciones
                with open(token_path, 'w') as token_file:
                    token_file.write(self.credentials.to_json())
                print(f"✓ Token guardado en {token_path}")

            if not self.credentials:
                raise RuntimeError("No se pudieron cargar las credenciales")

            # Construir servicio Sheets
            self.service = build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)
            print("✅ Autenticación exitosa")
            return self.service

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            raise
        except Exception as error:
            print(f"❌ Error en autenticación: {error}")
            raise

    def get_service(self):
        if not self.service:
            raise Exception("No autenticado. Llama a authenticate() primero.")
        return self.service

    def get_credentials(self):
        """Retorna las credenciales (útil para Drive API)"""
        if not self.credentials:
            raise Exception("No autenticado. Llama a authenticate() primero.")
        return self.credentials

    def is_authenticated(self):
        return self.service is not None
