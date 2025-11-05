"""
Script para programar reuniones informativas (RIF) de maestrías
Toma datos de un sheet, selecciona los próximos 10 eventos y actualiza las descripciones
"""

import sys
from datetime import datetime, timedelta
from auth import GoogleSheetsAuth
from sheet_operations import SheetOperations
from config_rif import RIFConfig as Config
import pandas as pd
from zoneinfo import ZoneInfo


class RIFScheduler:
    def __init__(self):
        self.auth = GoogleSheetsAuth()
        self.sheet_ops = None
    
    def initialize(self):
        """Inicializa la aplicación"""
        try:
            print("Iniciando programador de RIF...")
            
            # Validar configuración
            errors = Config.validate()
            if errors:
                print("Errores de configuración:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # Autenticar
            service = self.auth.authenticate()
            self.sheet_ops = SheetOperations(service)
            
            print("Aplicación inicializada correctamente")
            return True
            
        except Exception as error:
            print(f"Error al inicializar: {error}")
            return False
    
    def read_rif_data(self):
        """Lee los datos de RIF del sheet origen"""
        try:
            print("Leyendo datos de RIF...")
            data = self.sheet_ops.read_sheet(
                range_name=Config.RIF_SOURCE_RANGE,
                sheet_name=Config.SOURCE_SHEET_NAME
            )
            
            if not data or len(data) < 2:
                print("No se encontraron datos suficientes")
                return None
            
            # Procesar datos (asumiendo que la primera fila son encabezados)
            headers = data[1]
            rows = data[2:]
            
            print(f"Datos leídos: {len(rows)} filas")
            return headers, rows
            
        except Exception as error:
            print(f"Error al leer datos: {error}")
            return None
    
    def parse_rif_events(self, headers, rows):
        """Parsea los datos de RIF y extrae eventos válidos"""
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
            print("No se encontraron las columnas necesarias (maestría, fecha RIF, hora RIF)")
            return []
        
        print(f"Columnas encontradas - Maestría: {maestria_idx}, Fecha: {fecha_idx}, Hora: {hora_idx}")
        
        # Procesar cada fila
        flag = True
        for row_idx, row in enumerate(rows):
            if len(row) <= max(maestria_idx, fecha_idx, hora_idx):
                continue
                
            maestria = row[maestria_idx].strip() if maestria_idx < len(row) else ""
            fecha_str = row[fecha_idx].strip() if fecha_idx < len(row) else ""
            hora_str = row[hora_idx].strip() if hora_idx < len(row) else ""
            
            if not maestria or not fecha_str:
                continue
            
            # Parsear fecha (formato DD/MM)
            try:
                fecha_parts = fecha_str.split('/')
                if len(fecha_parts) == 2:
                    dia, mes = int(fecha_parts[0]), int(fecha_parts[1])
                    # Asumir año actual
                    tz_ar = ZoneInfo("America/Argentina/Buenos_Aires")

                    año_actual = datetime.now().year
                    
                    if ":" in hora_str:
                        hora = int(hora_str.split(":")[0])
                    if "." in hora_str:
                        hora= int(float(hora_str))

                    fecha_evento = datetime(año_actual, mes, dia,hora, tzinfo=tz_ar)
                    
                    # Si la fecha ya pasó este año, usar el próximo año
                    if fecha_evento < datetime.now(tz=tz_ar) and flag:
                        continue
                    elif fecha_evento < datetime.now(tz=tz_ar) and not flag:
                        fecha_evento = datetime(año_actual + 1, mes, dia,tzinfo=tz_ar)
                    
                    # Parsear hora
                    flag=False
                    
                    events.append({
                            'maestria': maestria,
                            'fecha': fecha_str,
                            'hora': hora_str,
                            'fecha_hora': fecha_evento,
                            'row_idx': row_idx + 2  # +2 porque empezamos desde fila 2
                        })
                        
            except (ValueError, IndexError) as e:
                print(f"Error parseando fecha {fecha_str}: {e}")
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
        events_sorted = sorted(events, key=lambda x: x['fecha_hora'])
        
        # Filtrar eventos futuros
        now = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        future_events = [e for e in events_sorted if e['fecha_hora'] > now]
        rifs_programs={
            'EMBARIF': False,
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
        }

        mapped_programs = self.get_maestria_id_mapping()
        
        
        for future_event in future_events:
            if rifs_programs[mapped_programs[future_event['maestria']]]==False:
                rifs_programs[mapped_programs[future_event['maestria']]] = future_event['fecha']

        print(rifs_programs)
        
        return rifs_programs
    
    def get_maestria_id_mapping(self):
        """Obtiene el mapeo de maestrías a IDs"""
        # Mapeo de maestrías a IDs (puedes ajustar según tus datos)
        maestria_mapping = {
                "MBT": "MBTRIF",
                "FyL": "FLRIF",
                "EMBA Regional": "REMBARIF",
                "MBA Salud": "MBASRIF",
                "MIM": "MIMRIF",
                "MRHH": "RRHHRIF",
                "MKT": "MKTRIF",
                "MND": "MNDRIF",
                "MBA Online": "MBAORIF",
                "EMBA": "EMBARIF",
                "MOSFL": "OSFLRIF",
                "MFIN": "FINRIF",
                "MOSFL 2026 Egresados": "OSFLRIF",
                "Fin&Law": "FLRIF",
            }

        
        return maestria_mapping
    
    def update_descriptions(self, next_10_events):
        """Actualiza las descripciones en el sheet destino"""
        try:
            print("Actualizando descripciones...")
            
            # Leer datos del sheet destino
            dest_data = self.sheet_ops.read_sheet(
                Config.DESTINATION_SHEET_ID,
                Config.RIF_DEST_RANGE,
                Config.DESTINATION_SHEET_NAME,
                False
            )
            
            if not dest_data:
                print("No se pudieron leer los datos del sheet destino")
                return False
            
            # Buscar columnas
            headers = dest_data[0]
            rows = dest_data[1:]

            # normalizar cada fila al largo del header
            normalized_rows = []
            num_cols = len(headers)

            for r in rows:
                # si la fila viene vacía o más corta, la completo
                if len(r) < num_cols:
                    r = r + [""] * (num_cols - len(r))
                # si viene más larga, la corto
                elif len(r) > num_cols:
                    r = r[:num_cols]
                normalized_rows.append(r)

            # ahora sí se puede crear el DF
            df = pd.DataFrame(normalized_rows, columns=headers)

            col_id = headers[0]       # primera columna
            col_desc = headers[2] 
            
            def build_desc(row):
                id_actual = (row[col_id] or "").strip()
                if id_actual in next_10_events:
                    if not next_10_events[id_actual]:
                        return ''
                    evento = next_10_events[id_actual]
                    return f"Próxima reunión informativa: {evento}"
                return row[col_desc]

            df[col_desc] = df.apply(build_desc, axis=1)

            # Volver a lista de listas para escribir al sheet
            updated_data = [headers] + df.values.tolist()
            # Escribir datos actualizados
            self.sheet_ops.write_sheet(
                Config.DESTINATION_SHEET_ID,
                updated_data,
                Config.RIF_DEST_RANGE,
                Config.DESTINATION_SHEET_NAME
            )
            
            print("Descripciones actualizadas exitosamente")
            return True
            
        except Exception as error:
            print(f"Error al actualizar descripciones: {error}")
            return False
    
    def run(self):
        """Ejecuta el proceso completo"""
        try:
            print("=== PROGRAMADOR DE RIF ===")
            print(f"Fecha y hora actual: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print()
            
            # Leer datos de RIF
            rif_data = self.read_rif_data()
            if not rif_data:
                return False
            
            headers, rows = rif_data
            
            # Parsear eventos
            events = self.parse_rif_events(headers, rows)
            if not events:
                print("No se encontraron eventos válidos")
                return False
            
            # Seleccionar próximos 10
            next_10 = self.select_next_10_events(events)
            if not next_10:
                print("No hay eventos futuros")
                return False

            
            # Actualizar descripciones
            success = self.update_descriptions(next_10)
            
            if success:
                print("\nProceso completado exitosamente")
            else:
                print("\nError en el proceso")
            
            return success
            
        except Exception as error:
            print(f"Error en el proceso: {error}")
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
