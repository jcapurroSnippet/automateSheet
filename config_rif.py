"""
Configuración específica para el RIF Scheduler
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('config.env')

class RIFConfig:
    # IDs de los sheets
    SOURCE_SHEET_ID = os.getenv('SOURCE_SHEET_ID', 'tu_sheet_id_origen_aqui')
    DESTINATION_SHEET_ID = os.getenv('DESTINATION_SHEET_ID', 'tu_sheet_id_destino_aqui')
    
    # Rangos específicos para RIF
    RIF_SOURCE_RANGE = os.getenv('RIF_SOURCE_RANGE', 'A:Z')  # Rango del sheet con datos de RIF
    RIF_DEST_RANGE = os.getenv('RIF_DEST_RANGE', 'A:Z')      # Rango del sheet destino
    
    # Nombres de las hojas
    SOURCE_SHEET_NAME = os.getenv('SOURCE_SHEET_NAME', 'Hoja1')
    DESTINATION_SHEET_NAME = os.getenv('DESTINATION_SHEET_NAME', 'Hoja1')
    
    # Configuración de autenticación
    CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', './credentials.json')
    TOKEN_PATH = os.getenv('TOKEN_PATH', './token.json')
    
    # Configuración de la API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Mapeo de maestrías a IDs (ajusta según tus datos)
    MAESTRIA_MAPPING = {
        'MKT': 'MKT',
        'MRHH': 'RRHH', 
        'MOSFL': 'OSFL',
        'EMBA': 'EMBA',
        'MND': 'MND',
        'MIM': 'MIM',
        'MIB': 'MIM',
        'MBA Online': 'MBAO',
        'MFIN': 'FIN',
        'MBT': 'MBT',
        'Fin&Law': 'FL',
        'MBA Salud': 'MBAS',
        'EDN': 'EDN',
        'REMBA': 'REMBA'
    }
    
    @classmethod
    def validate(cls):
        """Valida la configuración"""
        errors = []
        
        if not os.path.exists('config.env'):
            errors.append("Archivo config.env no encontrado")
        
        if cls.SOURCE_SHEET_ID == 'tu_sheet_id_origen_aqui':
            errors.append("SOURCE_SHEET_ID no está configurado")
        
        if cls.DESTINATION_SHEET_ID == 'tu_sheet_id_destino_aqui':
            errors.append("DESTINATION_SHEET_ID no está configurado")
        
        if not os.path.exists(cls.CREDENTIALS_PATH):
            errors.append(f"Archivo de credenciales no encontrado: {cls.CREDENTIALS_PATH}")
        
        return errors
