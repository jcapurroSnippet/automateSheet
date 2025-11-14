"""
Módulo de operaciones con Google Sheets
Usa OAuth 2.0 (token.json) para acceso a Drive y Sheets
"""

import pandas as pd
from config_rif import RIFConfig as Config
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class SheetOperations:
    def __init__(self, service, credentials=None):
        self.service = service
        self.credentials = credentials  # OAuth credentials (de auth.py)
        self.drive_service = None
        
        # Inicializar Drive API si tenemos credenciales
        if self.credentials:
            self.drive_service = build("drive", "v3", credentials=self.credentials, cache_discovery=False)
    
    def read_sheet(self, sheet_id=None, range_name=None, sheet_name=None, source=True):
        """
        Lee datos del sheet
        
        Args:
            sheet_id (str): ID del sheet
            range_name (str): Rango a leer (ej: 'A1:Z100')
            sheet_name (str): Nombre de la hoja
            source (bool): Si True, intenta copiar XLSX de Drive
            
        Returns:
            list: Lista de filas con los datos
        """
        try:
            if source and sheet_id is None:
                # Copiar archivo XLSX de Drive a Google Sheets
                if not self.drive_service:
                    raise RuntimeError("Drive API no disponible. Verifica que token.json esté presente.")
                
                print(f"📋 Copiando archivo de Drive: {Config.SOURCE_SHEET_ID}")
                xlsx_id = Config.SOURCE_SHEET_ID
                
                copy = self.drive_service.files().copy(
                    fileId=xlsx_id,
                    body={
                        "name": "Copia como Sheets",
                        "mimeType": "application/vnd.google-apps.spreadsheet"
                    },
                    supportsAllDrives=True
                ).execute()

                sheet_id = copy["id"]
                print(f"✅ Copia creada: {sheet_id}")
            
            # Construir rango
            full_range = self._build_range(
                sheet_name or Config.SOURCE_SHEET_NAME,
                range_name or Config.RIF_SOURCE_RANGE
            )
            
            print(f"📖 Leyendo datos de: {sheet_id} - {full_range}")
            
            # Leer desde Sheets API
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=full_range
            ).execute()

            values = result.get('values', [])
            print(f"✅ Se leyeron {len(values)} filas del sheet")
            
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
