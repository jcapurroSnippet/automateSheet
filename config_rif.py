"""
Configuración específica para el RIF Scheduler
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('config.env')

class RIFConfig:
    # IDs de los sheets
    SOURCE_SHEET_ID = os.getenv('SOURCE_SHEET_ID', '1RkbgAXnR9bQQSRMUxvXbm_r3m1bnzqIN')
    DESTINATION_SHEET_ID_META = os.getenv('DESTINATION_SHEET_ID_META')
    DESTINATION_SHEET_ID_GGL = os.getenv('DESTINATION_SHEET_ID_GGL')
    
    # Rangos específicos para RIF
    RIF_SOURCE_RANGE = os.getenv('RIF_SOURCE_RANGE', 'D:F')  # Rango del sheet con datos de RIF
    RIF_DEST_RANGE_META = os.getenv('RIF_DEST_RANGE_META')      # Rango del sheet destino
    RIF_DEST_RANGE_GGL = os.getenv('RIF_DEST_RANGE_GGL')
    
    # Nombres de las hojas
    SOURCE_SHEET_NAME = os.getenv('SOURCE_SHEET_NAME', 'Status y Solicitud RIFs')
    DESTINATION_SHEET_NAME_META = os.getenv('DESTINATION_SHEET_NAME_META', 'Worksheet')
    DESTINATION_SHEET_NAME_GGL = os.getenv('DESTINATION_SHEET_NAME_GGL')

    # Catálogo TikTok
    TIKTOK_CATALOG_SOURCE_FILE = os.getenv('TIKTOK_CATALOG_SOURCE_FILE', 'Catalog_TikTok_from_Meta.csv')
    TIKTOK_CATALOG_BUCKET = os.getenv('TIKTOK_CATALOG_BUCKET', 'catalogo_tiktok')
    TIKTOK_CATALOG_OBJECT = os.getenv('TIKTOK_CATALOG_OBJECT', 'Catalog_TikTok_from_Meta.csv')
    
    # Configuración de autenticación
    CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', './credentials.json')
    
    # Configuración de la API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    
    
    map_rif = {
            "EMBA": ["EMBARIF"],  
            "MBAO": ["MBAORIF"],
            "MIM": ["MIMRIF"],
            "MKT": ["MKTRIF"],
            "MND": ["MNDRIF"],
            "RRHH": ["RRHHRIF"],
            "FIN": ["FINRIF"],
            "MBT": ["MBTRIF"],
            "OSFL": ["OSFLRIF"],
        }
    
