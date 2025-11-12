"""
Módulo de operaciones con Google Sheets
"""

import os
import json
import pandas as pd
from config_rif import RIFConfig as Config
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

class SheetOperations:
    def __init__(self, service, credentials=None):
        """
        service: cliente de Sheets (googleapiclient.discovery.Resource)
        credentials: objeto de credenciales (opcional). Si se provee,
                     se usará para construir clientes adicionales como Drive.
        """
        self.service = service
        self.credentials = credentials
    
    def read_sheet(self,  sheet_id=None, range_name=None, sheet_name=None, source=True, source_type='auto'):
        """
        Lee datos del sheet
        
        Args:
            sheet_id (str): ID del sheet
            range_name (str): Rango a leer (ej: 'A1:Z100')
            sheet_name (str): Nombre de la hoja
            
        Returns:
            list: Lista de filas con los datos
        """
        try:
            # Decide comportamiento según el tipo de fuente
            # source_type: 'sheet' -> leer directamente como Google Sheet usando las credenciales principales (SA/ADC)
            # source_type: 'drive' -> copiar vía Drive API (usa token/secret específico para Drive)
            # source_type: 'auto' (default) -> intentar 'sheet' por defecto
            effective_source = source_type or 'auto'

            if source and effective_source != 'drive':
                # Leer directamente como Google Sheet usando Sheets API
                sheet_id = sheet_id or Config.SOURCE_SHEET_ID
                full_range = self._build_range(
                    sheet_name or Config.SOURCE_SHEET_NAME,
                    range_name or Config.RIF_SOURCE_RANGE
                )
                print(f"📖 Leyendo datos de (Sheets): {sheet_id} - {full_range}")
                try:
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=sheet_id,
                        range=full_range
                    ).execute()
                    values = result.get('values', [])
                    print(f"✅ Se leyeron {len(values)} filas del sheet origen (Sheets)")
                    return values
                except HttpError as e:
                    # Si se pidió auto y obtuvimos notFound, intentamos fallback a Drive
                    if effective_source == 'auto' and e.status_code == 404:
                        print("⚠️ Sheet no encontrado vía Sheets API, intentando fallback a Drive para copiar el archivo...")
                        # caerá a la lógica drive más abajo
                    else:
                        raise

            # Si llegamos aquí, queremos usar Drive to copy (source_type == 'drive' o fallback)
            # Para Drive, preferimos credenciales específicas para Drive (secret o archivo)
            drive_creds = None
            # El token/secret puede venir en varias vars. Prioridad:
            # 1) GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON (service account JSON para Drive)
            # 2) GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE (path montado)
            # 3) GOOGLE_TOKEN_JSON (secret con token/sa para Drive)
            # 4) Config.TOKEN_PATH (token.json local)
            drive_json = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
            drive_file = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE')
            google_token_json = os.environ.get('GOOGLE_TOKEN_JSON')
            if drive_json:
                try:
                    info = json.loads(drive_json)
                    drive_creds = service_account.Credentials.from_service_account_info(info, scopes=[
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/spreadsheets",
                    ])
                except Exception as e:
                    raise RuntimeError(f"Error cargando GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON: {e}")
            elif drive_file:
                try:
                    drive_creds = service_account.Credentials.from_service_account_file(drive_file, scopes=[
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/spreadsheets",
                    ])
                except Exception as e:
                    raise RuntimeError(f"Error cargando GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE: {e}")

            # secret token JSON fallback (puede ser service account o credenciales de usuario)
            if not drive_creds and google_token_json:
                try:
                    info = json.loads(google_token_json)
                    if info.get('type') == 'service_account':
                        drive_creds = service_account.Credentials.from_service_account_info(info, scopes=[
                            "https://www.googleapis.com/auth/drive",
                            "https://www.googleapis.com/auth/spreadsheets",
                        ])
                    else:
                        # credenciales de usuario (token) en memoria
                        from google.oauth2.credentials import Credentials as UserCreds
                        drive_creds = UserCreds.from_authorized_user_info(info, scopes=[
                            "https://www.googleapis.com/auth/drive",
                            "https://www.googleapis.com/auth/spreadsheets",
                        ])
                except Exception:
                    drive_creds = None

            # token local fallback
            if not drive_creds and os.path.exists(Config.TOKEN_PATH):
                try:
                    from google.oauth2.credentials import Credentials as UserCreds
                    drive_creds = UserCreds.from_authorized_user_file(Config.TOKEN_PATH, [
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/spreadsheets",
                    ])
                except Exception:
                    drive_creds = None

            # last resort: use general credentials passed in
            if not drive_creds:
                if getattr(self, 'credentials', None):
                    drive_creds = self.credentials
                else:
                    try:
                        http = getattr(self.service, '_http', None)
                        if http and getattr(http, 'credentials', None):
                            drive_creds = http.credentials
                    except Exception:
                        drive_creds = None

            if not drive_creds:
                raise RuntimeError("No se pudieron obtener credenciales para Drive. Define GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON/FILE o coloca un token en Config.TOKEN_PATH")

            drive = build("drive", "v3", credentials=drive_creds, cache_discovery=False)

            xlsx_id = sheet_id or Config.SOURCE_SHEET_ID
            print(f"📦 Copiando archivo Drive {xlsx_id} -> Sheets usando credenciales de Drive")
            copy = drive.files().copy(
                fileId=xlsx_id,
                body={"name": "Copia como Sheets", "mimeType": "application/vnd.google-apps.spreadsheet"},
                supportsAllDrives=True
            ).execute()

            sheet_id = copy["id"]  # usalo con la Sheets API
            # Construir el rango completo (para lectura posterior)
            
            full_range = self._build_range(
                sheet_name or Config.SOURCE_SHEET_NAME,
                range_name or Config.RIF_SOURCE_RANGE
                )
            
            print(f"📖 Leyendo datos de: {sheet_id} - {full_range}")

            # Llamar a la API
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=full_range
            ).execute()

            values = result.get('values', [])
            print(f"✅ Se leyeron {len(values)} filas del sheet origen")
            
            return values
            
        except Exception as error:
            print(f"❌ Error al leer el sheet: {error}")
            raise
    
    def write_sheet(self, sheet_id, data, range_name=None, sheet_name=None):
        """
        Escribe datos al sheet
        
        Args:
            sheet_id (str): ID del sheet
            data (list): Datos a escribir
            range_name (str): Rango donde escribir
            sheet_name (str): Nombre de la hoja
        """
        try:
            # Construir el rango completo
            full_range = self._build_range(
                sheet_name or Config.DESTINATION_SHEET_NAME,
                range_name or Config.RIF_DEST_RANGE
            )
            
            print(f"📝 Escribiendo {len(data)} filas en: {sheet_id} - {full_range}")
            
            # Llamar a la API
            body = {'values': data}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=full_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Se escribieron {len(data)} filas en el sheet destino")
            return result
            
        except Exception as error:
            print(f"❌ Error al escribir en el sheet: {error}")
            raise
    
    def clear_sheet(self, sheet_id, range_name=None, sheet_name=None):
        """
        Limpia el contenido del sheet
        
        Args:
            sheet_id (str): ID del sheet
            range_name (str): Rango a limpiar
            sheet_name (str): Nombre de la hoja
        """
        try:
            # Construir el rango completo
            full_range = self._build_range(
                sheet_name or Config.DESTINATION_SHEET_NAME,
                range_name or Config.RIF_DEST_RANGE
            )
            
            print(f"🧹 Limpiando contenido de: {sheet_id} - {full_range}")
            
            # Llamar a la API
            self.service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=full_range
            ).execute()
            
            print("✅ Sheet destino limpiado exitosamente")
            
        except Exception as error:
            print(f"❌ Error al limpiar el sheet: {error}")
            raise
    
    def get_sheet_info(self, sheet_id):
        """
        Obtiene información del sheet
        
        Args:
            sheet_id (str): ID del sheet
            
        Returns:
            dict: Información del sheet
        """
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()
            
            sheet_info = {
                'title': result['properties']['title'],
                'sheets': []
            }
            
            for sheet in result['sheets']:
                sheet_info['sheets'].append({
                    'title': sheet['properties']['title'],
                    'sheetId': sheet['properties']['sheetId'],
                    'gridProperties': sheet['properties'].get('gridProperties', {})
                })
            
            print(f"📊 Información del sheet \"{sheet_info['title']}\":")
            for sheet in sheet_info['sheets']:
                print(f"  - {sheet['title']} (ID: {sheet['sheetId']})")
            
            return sheet_info
            
        except Exception as error:
            print(f"❌ Error al obtener información del sheet: {error}")
            raise
    
    def _build_range(self, sheet_name, range_name):
        """
        Construye el rango completo con el nombre de la hoja
        
        Args:
            sheet_name (str): Nombre de la hoja
            range_name (str): Rango
            
        Returns:
            str: Rango completo
        """
        return f"{sheet_name}!{range_name}"
    
    def read_sheet_as_dataframe(self, sheet_id, range_name=None, sheet_name=None):
        """
        Lee datos del sheet como DataFrame de pandas
        
        Args:
            sheet_id (str): ID del sheet
            range_name (str): Rango a leer
            sheet_name (str): Nombre de la hoja
            
        Returns:
            pd.DataFrame: DataFrame con los datos
        """
        try:
            data = self.read_sheet(sheet_id, range_name, sheet_name)
            
            if not data:
                return pd.DataFrame()
            
            # Usar la primera fila como encabezados si es posible
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data)
            
            return df
            
        except Exception as error:
            print(f"❌ Error al leer sheet como DataFrame: {error}")
            raise
    
    def write_dataframe_to_sheet(self, df, sheet_id, range_name=None, sheet_name=None, include_headers=True):
        """
        Escribe un DataFrame al sheet
        
        Args:
            df (pd.DataFrame): DataFrame a escribir
            sheet_id (str): ID del sheet
            range_name (str): Rango donde escribir
            sheet_name (str): Nombre de la hoja
            include_headers (bool): Incluir encabezados
        """
        try:
            # Convertir DataFrame a lista
            if include_headers:
                data = [df.columns.tolist()] + df.values.tolist()
            else:
                data = df.values.tolist()
            
            # Escribir al sheet
            self.write_sheet(sheet_id, data, range_name, sheet_name)
            
        except Exception as error:
            print(f"❌ Error al escribir DataFrame al sheet: {error}")
            raise
