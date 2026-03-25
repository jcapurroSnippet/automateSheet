"""
Script para programar reuniones informativas (RIF) de maestrías
Toma datos de un sheet, selecciona los próximos 10 eventos y actualiza las descripciones
"""

import csv
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from auth import GoogleSheetsAuth
from sheet_operations import SheetOperations
from config_rif import RIFConfig as Config
from zoneinfo import ZoneInfo


class RIFScheduler:
    TIKTOK_CATALOG_HEADERS = (
        'sku_id',
        'title',
        'description',
        'availability',
        'condition',
        'price',
        'link',
        'image_link',
        'brand',
        'gender',
        'age_group',
        'gtin',
        'additional_image_link',
    )

    def __init__(self):
        self.auth = GoogleSheetsAuth()
        self.sheet_ops = None
        self.logs = []

    def _log(self, message):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.logs.append(formatted_message)

    def get_logs(self):
        return self.logs

    @staticmethod
    def normalize_catalog_id(catalog_id):
        """Normaliza IDs de catálogo para compararlos contra los IDs RIF."""
        return (catalog_id or "").strip().replace('V2', '')

    def build_rif_description(self, catalog_id, current_description, next_10_events):
        """Construye la descripción según el próximo evento disponible."""
        normalized_id = self.normalize_catalog_id(catalog_id)

        if normalized_id in next_10_events:
            if not next_10_events[normalized_id]:
                return ''

            return f"Próxima reunión informativa: {next_10_events[normalized_id]}"

        return current_description or ""

    def get_platform_events(self, next_10_events, platform):
        """Devuelve el mapping de eventos adaptado a cada plataforma."""
        platform_events = dict(next_10_events)

        if platform == 'GGL':
            for prog, posibles_claves in Config.map_rif.items():
                for clave in posibles_claves:
                    if clave in platform_events and platform_events[clave]:
                        platform_events[prog] = platform_events[clave]
                        self._log(f"Mapeando {clave} -> {prog} con fecha {platform_events[clave]}")
                        break

        return platform_events

    @staticmethod
    def normalize_rows(headers, rows):
        """Normaliza filas tabulares al largo del header."""
        normalized_rows = []
        num_cols = len(headers)

        for row in rows:
            if len(row) < num_cols:
                row = row + [""] * (num_cols - len(row))
            elif len(row) > num_cols:
                row = row[:num_cols]

            normalized_rows.append(row)

        return normalized_rows

    @staticmethod
    def normalize_additional_image_link(raw_value):
        """Convierte separadores del sheet de Meta al formato esperado por TikTok."""
        if not raw_value:
            return ""

        parts = [part.strip() for part in str(raw_value).split('|')]
        return ",".join(part for part in parts if part)

    def build_tiktok_catalog_rows(self, meta_data):
        """Construye filas de TikTok usando el sheet de Meta como fuente."""
        if not meta_data:
            raise ValueError("No se pudieron leer los datos del sheet de Meta para TikTok")

        meta_headers = meta_data[0]
        meta_rows = self.normalize_rows(meta_headers, meta_data[1:])
        header_positions = {header.strip().lower(): idx for idx, header in enumerate(meta_headers)}

        required_columns = {
            'id',
            'title',
            'description',
            'availability',
            'condition',
            'price',
            'link',
            'image_link',
            'brand',
            'gender',
            'age_group',
            'gtin',
            'additional_image_link',
        }
        missing_columns = required_columns - set(header_positions)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Faltan columnas obligatorias en el sheet de Meta para TikTok: {missing}")

        tiktok_rows = []
        for row in meta_rows:
            tiktok_rows.append({
                'sku_id': row[header_positions['id']],
                'title': row[header_positions['title']],
                'description': row[header_positions['description']],
                'availability': row[header_positions['availability']],
                'condition': row[header_positions['condition']],
                'price': row[header_positions['price']],
                'link': row[header_positions['link']],
                'image_link': row[header_positions['image_link']],
                'brand': row[header_positions['brand']],
                'gender': row[header_positions['gender']],
                'age_group': row[header_positions['age_group']],
                'gtin': row[header_positions['gtin']],
                'additional_image_link': self.normalize_additional_image_link(
                    row[header_positions['additional_image_link']]
                ),
            })

        return tiktok_rows
    
    def initialize(self):
        """Inicializa la aplicación"""
        try:
            self._log("Iniciando programador de RIF...")
            
            
            # Autenticar
            self._log("Autenticando con Google Sheets...")
            service = self.auth.authenticate()
            self._log("Autenticación completada")
            # Pasar las credenciales (Service Account) a SheetOperations para operaciones Drive
            creds = self.auth.get_credentials()
            self.sheet_ops = SheetOperations(service, credentials=creds)
            self._log("Instancia de SheetOperations creada")
            
            self._log("Aplicación inicializada correctamente")
            return True
            
        except Exception as error:
            self._log(f"Error al inicializar: {error}")
            return False
    
    def read_rif_data(self):
        """Lee los datos de RIF del sheet origen"""
        try:
            self._log("Leyendo datos de RIF...")
            self._log(f"Leyendo rango {Config.RIF_SOURCE_RANGE} del sheet {Config.SOURCE_SHEET_NAME}")
            data = self.sheet_ops.read_sheet(
                range_name=Config.RIF_SOURCE_RANGE,
                sheet_name=Config.SOURCE_SHEET_NAME
            )
            
            if not data or len(data) < 2:
                self._log("No se encontraron datos suficientes")
                return None
            
            # Procesar datos (asumiendo que la primera fila son encabezados)
            headers = data[1]
            rows = data[2:]
            
            self._log(f"Datos leídos: {len(rows)} filas")
            return headers, rows
            
        except Exception as error:
            self._log(f"Error al leer datos: {error}")
            return None
    
    def parse_rif_events(self, headers, rows):
        """Parsea los datos de RIF y extrae eventos válidos"""
        self._log("Parseando eventos de RIF...")
        events = []
        
        # Buscar índices de columnas
        maestria_idx = None
        fecha_idx = None
        hora_idx = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'maestria' in header_lower or 'maestría' in header_lower:
                maestria_idx = i
            elif 'fecha' in header_lower and 'rif' in header_lower:
                fecha_idx = i
            elif 'hora' in header_lower and 'rif' in header_lower:
                hora_idx = i
        
        if maestria_idx is None or fecha_idx is None or hora_idx is None:
            self._log("No se encontraron las columnas necesarias (maestría, fecha RIF, hora RIF)")
            return []
        
        self._log(f"Columnas encontradas - Maestría: {maestria_idx}, Fecha: {fecha_idx}, Hora: {hora_idx}")
        
        # Procesar cada fila

        for row_idx, row in enumerate(rows):
            self._log(f"Procesando fila {row_idx + 2}: {row}")
            if len(row) <= max(maestria_idx, fecha_idx, hora_idx):
                continue
                
            maestria = row[maestria_idx].strip() if maestria_idx < len(row) else ""
            fecha_str = row[fecha_idx].strip() if fecha_idx < len(row) else ""
            hora_str = row[hora_idx].strip() if hora_idx < len(row) else ""
            
            if not maestria or not fecha_str:
                self._log(f"Fila {row_idx + 2} sin maestría o fecha válida. Maestría: '{maestria}', Fecha: '{fecha_str}'")
                continue
            
            # Parsear fecha (formato DD/MM)
            try:
                fecha_parts = fecha_str.split('/')
                
                dia, mes, año = int(fecha_parts[0]), int(fecha_parts[1]), int(fecha_parts[2])+2000 if len(fecha_parts) > 2 else (datetime.now().year)
                
                tz_ar = ZoneInfo("America/Argentina/Buenos_Aires")
                
                if ":" in hora_str:
                    hora = int(hora_str.split(":")[0])
                elif "." in hora_str:
                    hora= int(float(hora_str))
                else:
                    hora = int(hora_str)
                fecha_evento = datetime(año, mes, dia,hora, tzinfo=tz_ar)
                
                # Si la fecha ya pasó este año, usar el próximo año
                if fecha_evento < datetime.now(tz=tz_ar) :
                    self._log(f"Evento pasado para {maestria} en fila {row_idx + 2}")
                    continue

                
                self._log(f"Evento válido encontrado: {maestria} - {fecha_evento}")
                events.append({
                        'maestria': maestria,
                        'fecha': fecha_str,
                        'hora': hora_str,
                        'fecha_hora': fecha_evento,
                        'row_idx': row_idx + 2  # +2 porque empezamos desde fila 2
                    })
                        
            except (ValueError, IndexError) as e:
                self._log(f"Error parseando fecha {fecha_str}: {e}")
                continue
        
        return events
    
    def parse_hora(self, hora_str):
        """Parsea la hora en diferentes formatos"""
        if not hora_str:
            return None
            
        try:
            # Limpiar la hora
            hora_clean = hora_str.replace(':', '.').replace('h', '').strip()
            
            # Si es solo un número, asumir que son horas
            if hora_clean.isdigit():
                hora_int = int(hora_clean)
                if 0 <= hora_int <= 23:
                    return datetime.now().replace(hour=hora_int, minute=0)
            
            # Si tiene punto o dos puntos, parsear como HH.MM o HH:MM
            if '.' in hora_clean or ':' in hora_clean:
                separador = '.' if '.' in hora_clean else ':'
                partes = hora_clean.split(separador)
                if len(partes) == 2:
                    hora_int = int(partes[0])
                    minuto_int = int(partes[1])
                    if 0 <= hora_int <= 23 and 0 <= minuto_int <= 59:
                        return datetime.now().replace(hour=hora_int, minute=minuto_int)
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def select_next_10_events(self, events):
        """Selecciona los próximos 10 eventos ordenados por fecha"""
        if not events:
            return []
        
        # Ordenar por fecha y hora
        self._log(f"Seleccionando próximos eventos de {len(events)} encontrados")
        events_sorted = sorted(events, key=lambda x: x['fecha_hora'])
        
        # Filtrar eventos futuros
        now = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        future_events = [e for e in events_sorted if e['fecha_hora'] > now]
        self._log(f"Eventos futuros encontrados: {len(future_events)}")
        rifs_programs={
            'EMBARIF': False,
            'EMBAR': False,
            'REMBARIF': False,
            'MBAORIF': False,
            'MBASRIF': False,
            'MIMRIF': False,
            'MKTRIF': False,
            'MNDRIF': False,
            'RRHHRIF': False,
            'FLRIF': False,
            'FINRIF': False,
            'MBTRIF': False,
            'OSFLRIF': False,
            'FINORIF': False,
        }

        mapped_programs = self.get_maestria_id_mapping()
        
        
        for future_event in future_events:
            maestria = future_event['maestria']
            if maestria not in mapped_programs:
                self._log(f"Maestría sin mapeo encontrado: {maestria}")
                continue

            mapped_key = mapped_programs[maestria]
            self._log(f"Evaluando evento {maestria} -> {mapped_key} el {future_event['fecha_hora']}")

            if rifs_programs[mapped_key] == False:
                fecha = future_event['fecha'][:5]
                if fecha[-1] == '/':
                    fecha = fecha[:-1]
                    fecha = '0' + fecha
                rifs_programs[mapped_key] = fecha
                self._log(f"Asignado {future_event['fecha']} a {mapped_key}")
            
            # Si es EMBA, también asignar a EMBAR
                if maestria == "EMBA" and rifs_programs['REMBARIF'] == False:
                    rifs_programs['REMBARIF'] = fecha
                    self._log(f"Asignado {future_event['fecha']} a EMBAR")
        self._log(f"Asignaciones resultantes: {rifs_programs}")
        
        return rifs_programs
    
    def get_maestria_id_mapping(self):
        """Obtiene el mapeo de maestrías a IDs"""
        # Mapeo de maestrías a IDs (puedes ajustar según tus datos)
        maestria_mapping = {
                "MBT": "MBTRIF",
                "FyL": "FLRIF",
                "MBA Salud": "MBASRIF",
                "MIM": "MIMRIF",
                "MRHH": "RRHHRIF",
                "MKT": "MKTRIF",
                "MND": "MNDRIF",
                "MBA's": "MBAORIF",
                "EMBA": "EMBARIF",
                "MOSFL": "OSFLRIF",
                "MFIN": "FINRIF",
                "MOSFL 2026 Egresados": "OSFLRIF",
                "Fin&Law": "FLRIF",
                "MF Online": "FINORIF",
            }

        
        return maestria_mapping
    
    def update_descriptions(self, next_10_events,dest_sheet_id,rif_dest_range,dest_sheet_name,platform):
        """Actualiza las descripciones en el sheet destino"""
        try:
            self._log("Actualizando descripciones...")
            
            # Leer datos del sheet destino
            self._log(f"Leyendo sheet destino {dest_sheet_name} ({dest_sheet_id}) rango {rif_dest_range}")
            dest_data = self.sheet_ops.read_sheet(
                dest_sheet_id,
                rif_dest_range,
                dest_sheet_name,
                False
            )

            
            if not dest_data:
                self._log("No se pudieron leer los datos del sheet destino")
                return False
            
            # Buscar columnas
            headers = dest_data[0]
            rows = dest_data[1:]

            # ahora sí se puede crear el DF
            import pandas as pd
            df = pd.DataFrame(self.normalize_rows(headers, rows), columns=headers)
            platform_events = self.get_platform_events(next_10_events, platform)

            self._log(f"Construyendo descripciones para plataforma {platform}")
            if platform == 'META':
                col_id = headers[0]       # primera columna
                col_desc = headers[2]
            else:
                col_id = headers[0]
                col_desc = headers[7]


            def build_desc(row):
                return self.build_rif_description(
                    row[col_id],
                    row[col_desc],
                    platform_events
                )

            df[col_desc] = df.apply(build_desc, axis=1)

            # Volver a lista de listas para escribir al sheet
            updated_data = [headers] + df.values.tolist()
            # Escribir datos actualizados
            self._log(f"Escribiendo datos actualizados en {dest_sheet_name}")
            self.sheet_ops.write_sheet(
                dest_sheet_id,
                updated_data,
                rif_dest_range,
                dest_sheet_name
            )
            
            self._log("Descripciones actualizadas exitosamente")
            return True
            
        except Exception as error:
            self._log(f"Error al actualizar descripciones: {error}")
            return False

    def export_tiktok_catalog(self, bucket_name=None, object_name=None, storage_client=None, meta_data=None):
        """Construye el catálogo de TikTok desde el sheet de Meta y lo publica en GCS."""
        temp_path = None

        try:
            bucket_name = bucket_name or Config.TIKTOK_CATALOG_BUCKET
            object_name = object_name or Config.TIKTOK_CATALOG_OBJECT

            if not bucket_name:
                raise ValueError("Falta configurar TIKTOK_CATALOG_BUCKET")

            if meta_data is None:
                if not self.sheet_ops:
                    raise ValueError("SheetOperations no está inicializado para construir el catálogo de TikTok")

                self._log(
                    f"Leyendo sheet de Meta para TikTok {Config.DESTINATION_SHEET_NAME_META} "
                    f"({Config.DESTINATION_SHEET_ID_META}) rango {Config.RIF_DEST_RANGE_META}"
                )
                meta_data = self.sheet_ops.read_sheet(
                    Config.DESTINATION_SHEET_ID_META,
                    Config.RIF_DEST_RANGE_META,
                    Config.DESTINATION_SHEET_NAME_META,
                    False
                )

            rows = self.build_tiktok_catalog_rows(meta_data)
            self._log(f"Construyendo CSV de TikTok desde Meta con {len(rows)} filas")

            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8-sig',
                newline='',
                suffix='.csv',
                delete=False,
                dir=tempfile.gettempdir()
            ) as temp_file:
                writer = csv.DictWriter(temp_file, fieldnames=self.TIKTOK_CATALOG_HEADERS)
                writer.writeheader()
                writer.writerows(rows)
                temp_path = Path(temp_file.name)

            self._log(f"Subiendo catálogo TikTok a gs://{bucket_name}/{object_name}")
            client = storage_client
            if client is None:
                from google.cloud import storage
                client = storage.Client()

            blob = client.bucket(bucket_name).blob(object_name)
            blob.upload_from_filename(str(temp_path), content_type='text/csv')

            self._log("Catálogo TikTok actualizado y subido exitosamente")
            return True

        except Exception as error:
            self._log(f"Error al exportar catálogo TikTok: {error}")
            return False
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    def run(self):
        """Ejecuta el proceso completo"""
        try:
            if not self.sheet_ops and not self.initialize():
                return False

            self._log("=== PROGRAMADOR DE RIF ===")
            self._log(f"Fecha y hora actual: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            self._log("")
            
            # Leer datos de RIF
            self._log("Leyendo información de origen...")
            rif_data = self.read_rif_data()
            if not rif_data:
                return False

            headers, rows = rif_data

            # Parsear eventos
            self._log("Parseando eventos obtenidos...")
            events = self.parse_rif_events(headers, rows)
            if not events:
                self._log("No se encontraron eventos válidos")
                return False

            # Seleccionar próximos 10
            self._log("Seleccionando próximos eventos...")
            next_10 = self.select_next_10_events(events)
            if not next_10:
                self._log("No hay eventos futuros")
                return False


            # Actualizar descripciones
            self._log("Actualizando plataforma META...")
            success_meta = self.update_descriptions(next_10,Config.DESTINATION_SHEET_ID_META,Config.RIF_DEST_RANGE_META,Config.DESTINATION_SHEET_NAME_META,'META')
            self._log("Actualizando plataforma GGL...")
            success_ggl = self.update_descriptions(next_10,Config.DESTINATION_SHEET_ID_GGL,Config.RIF_DEST_RANGE_GGL,Config.DESTINATION_SHEET_NAME_GGL,'GGL')
            self._log("Actualizando catálogo TikTok...")
            success_tiktok = self.export_tiktok_catalog()

            if success_ggl and success_meta and success_tiktok:
                self._log("Proceso completado exitosamente")
            else:
                self._log("Error en el proceso")

            return success_meta and success_ggl and success_tiktok
            
        except Exception as error:
            self._log(f"Error en el proceso: {error}")
            return False

def main():
    """Función principal"""
    scheduler = RIFScheduler()
    
    if not scheduler.initialize():
        sys.exit(1)
    
    success = scheduler.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
