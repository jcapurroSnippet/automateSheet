"""
Módulo de autenticación con Google Sheets API
Usa OAuth 2.0 (credentials.json como OAuth client + token.json como autorización)
"""

import os
import json
import traceback
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

            # If secrets were provided via environment variables (Cloud Run Secret Manager
            # or local test), materialize them to the files the code expects. This is a
            # safe no-op if the files already exist.
            env_client = os.environ.get("CLIENT_SECRETS")
            env_token = os.environ.get("TOKEN_JSON")

            if env_client and not os.path.exists(credentials_path):
                print("Writing CLIENT_SECRETS from env to credentials.json")
                with open(credentials_path, "w", encoding="utf-8") as f:
                    f.write(env_client)
                try:
                    size = os.path.getsize(credentials_path)
                    print(f"Wrote credentials.json ({size} bytes)")
                except Exception:
                    print("Wrote credentials.json (size unknown)")

            if env_token and not os.path.exists(token_path):
                print("Writing TOKEN_JSON from env to token.json")
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(env_token)
                try:
                    size = os.path.getsize(token_path)
                    print(f"Wrote token.json ({size} bytes)")
                except Exception:
                    print("Wrote token.json (size unknown)")

            # Opción A: Usar token.json existente
            if os.path.exists(token_path):
                print("✓ Cargando autorización desde token.json")
                self.credentials = Credentials.from_authorized_user_file(
                    token_path,
                    scopes=Config.SCOPES
                )
                # Log basic metadata (do NOT print secrets)
                try:
                    print(f"token.json found. valid={getattr(self.credentials, 'valid', None)}, expired={getattr(self.credentials, 'expired', None)}, has_refresh_token={bool(getattr(self.credentials, 'refresh_token', None))}")
                except Exception:
                    print("Loaded token.json but couldn't read metadata")
                # Refrescar token si es necesario
                if self.credentials.expired and self.credentials.refresh_token:
                    print("✓ Refrescando token...")
                    request = Request()
                    self.credentials.refresh(request)
                    print("✓ Token refrescado")
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
            print("✅ Autenticación exitosa: servicio Sheets creado correctamente")
            try:
                # quick check: list spreadsheets scope presence (do not call APIs that modify data)
                print(f"Credenciales scopes: {getattr(self.credentials, 'scopes', None)}")
            except Exception:
                pass
            return self.service

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            try:
                cwd = os.getcwd()
                print(f"Current working directory: {cwd}")
                files = os.listdir(cwd)
                print(f"Files in cwd: {files}")
            except Exception:
                pass
            raise
        except Exception as error:
            print(f"❌ Error en autenticación: {error}")
            traceback.print_exc()
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
