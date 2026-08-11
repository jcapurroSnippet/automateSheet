"""
Configuración específica para el RIF Scheduler
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('config.env')

class RIFConfig:
    # IDs de los sheets
    SOURCE_SHEET_ID = os.getenv('SOURCE_SHEET_ID', '1dlj12O27VqxGLfTpTG4u4c8C45DFMEthju2dyHb7HZQ')
    DESTINATION_SHEET_ID_META = os.getenv('DESTINATION_SHEET_ID_META')
    DESTINATION_SHEET_ID_GGL = os.getenv('DESTINATION_SHEET_ID_GGL')
    
    # Rangos específicos para RIF
    # SOURCE_RANGE se conserva como fallback para instalaciones anteriores.
    RIF_SOURCE_RANGE = os.getenv('RIF_SOURCE_RANGE', os.getenv('SOURCE_RANGE', 'A:H'))
    RIF_DEST_RANGE_META = os.getenv('RIF_DEST_RANGE_META')      # Rango del sheet destino
    RIF_DEST_RANGE_GGL = os.getenv('RIF_DEST_RANGE_GGL')
    
    # Nombres de las hojas
    SOURCE_SHEET_NAME = os.getenv('SOURCE_SHEET_NAME', 'Consolidado')
    DESTINATION_SHEET_NAME_META = os.getenv('DESTINATION_SHEET_NAME_META', 'Worksheet')
    DESTINATION_SHEET_NAME_GGL = os.getenv('DESTINATION_SHEET_NAME_GGL')

    # Catálogo TikTok
    TIKTOK_CATALOG_BUCKET = os.getenv('TIKTOK_CATALOG_BUCKET', 'catalogo_tiktok')
    TIKTOK_CATALOG_OBJECT = os.getenv('TIKTOK_CATALOG_OBJECT', 'Catalog_TikTok_from_Meta.csv')

    # Bucket para imágenes de programas RIF
    IMAGE_BUCKET = os.getenv('IMAGE_BUCKET', 'piezas_programas_udesa')
    
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
            "MBAS": ["MBASRIF"],
            "EMBAR": ["REMBARIF"],
        }
    
