"""
Módulo de autenticación con Google Sheets API (adaptado para Cloud Run)
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SACredentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth
from config_rif import RIFConfig as Config

class GoogleSheetsAuth:
    def __init__(self):
        self.credentials = None
        self.service = None

    def authenticate(self):
        """
        Autentica con Google Sheets API.
        Prioridad:
        1. Service Account (para Cloud Run)
        2. Token OAuth existente (local)
        3. Flujo OAuth (solo local)
        """
        try:
            print("🔐 Iniciando autenticación con Google Sheets API...")

            # 1) INTENTAR SERVICE ACCOUNT (Cloud Run / servidor)
            # Opción A: el JSON viene en una env var
            sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            # Opción B: viene un path a un json montado
            sa_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", None)

            if sa_json or sa_path:
                print("🟣 Usando Service Account")
                if sa_json:
                    info = json.loads(sa_json)
                    self.credentials = SACredentials.from_service_account_info(
                        info,
                        scopes=Config.SCOPES
                    )
                else:
                    self.credentials = SACredentials.from_service_account_file(
                        sa_path,
                        scopes=Config.SCOPES
                    )

            # 1b) Intentar Application Default Credentials (útil en Cloud Run / GCE)
            if not self.credentials:
                try:
                    creds, project = google.auth.default(scopes=Config.SCOPES)
                    if creds:
                        print("🟢 Usando Application Default Credentials")
                        self.credentials = creds
                except Exception:
                    # no hay ADC disponible, continuar con flujo local
                    pass

            # Si aún no hay credenciales, intentar flujo local con token/oauth
            if not self.credentials:
                # 2) LOCAL: usar token guardado
                if os.path.exists(Config.TOKEN_PATH):
                    print("📄 Cargando token local existente...")
                    self.credentials = Credentials.from_authorized_user_file(
                        Config.TOKEN_PATH,
                        Config.SCOPES
                    )

                # 3) Si no hay token o no es válido, hacer flujo OAuth (solo local)
                if not self.credentials or not self.credentials.valid:
                    if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                        print("🔄 Refrescando token...")
                        self.credentials.refresh(Request())
                    else:
                        print("🔑 Obteniendo nuevas credenciales vía OAuth (esto es para correr en local)...")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            Config.CREDENTIALS_PATH,
                            Config.SCOPES
                        )
                        # esto abre el browser; no usar en Cloud Run
                        self.credentials = flow.run_local_server(port=0)

                    # guardar token para próximas corridas locales
                    with open(Config.TOKEN_PATH, 'w') as token:
                        token.write(self.credentials.to_json())
                    print("💾 Credenciales OAuth guardadas")

            # construir servicio
            self.service = build('sheets', 'v4', credentials=self.credentials)
            print("✅ Autenticación exitosa con Google Sheets API")
            return self.service

        except FileNotFoundError:
            print("❌ Error: No se encontró el archivo de credenciales")
            print(f"📁 Asegúrate de que {Config.CREDENTIALS_PATH} existe (solo para OAuth local)")
            raise
        except Exception as error:
            print(f"❌ Error en la autenticación: {error}")
            raise

    def get_service(self):
        if not self.service:
            raise Exception("No se ha autenticado. Llama a authenticate() primero.")
        return self.service

    def is_authenticated(self):
        return self.service is not None
