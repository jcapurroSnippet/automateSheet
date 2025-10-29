"""
Script para programar reuniones informativas (RIF) de maestrías
Toma datos de un sheet, selecciona los próximos 10 eventos y actualiza las descripciones
"""

import sys
from datetime import datetime, timedelta
from auth import GoogleSheetsAuth
from sheet_operations import SheetOperations
from config import Config as Config


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
                Config.SOURCE_SHEET_ID,
                Config.SOURCE_RANGE,
                Config.SOURCE_SHEET_NAME
            )
            
            if not data or len(data) < 2:
                print("No se encontraron datos suficientes")
                return None
            
            # Procesar datos (asumiendo que la primera fila son encabezados)
            headers = data[0]
            rows = data[1:]
            
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
                    año_actual = datetime.now().year
                    fecha_evento = datetime(año_actual, mes, dia)
                    
                    # Si la fecha ya pasó este año, usar el próximo año
                    if fecha_evento < datetime.now():
                        fecha_evento = datetime(año_actual + 1, mes, dia)
                    
                    # Parsear hora
                    hora_evento = self.parse_hora(hora_str)
                    
                    if hora_evento:
                        # Combinar fecha y hora
                        fecha_hora_evento = fecha_evento.replace(
                            hour=hora_evento.hour,
                            minute=hora_evento.minute
                        )
                        
                        events.append({
                            'maestria': maestria,
                            'fecha': fecha_str,
                            'hora': hora_str,
                            'fecha_hora': fecha_hora_evento,
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
        now = datetime.now()
        future_events = [e for e in events_sorted if e['fecha_hora'] > now]
        
        # Tomar los próximos 10
        next_10 = future_events[:10]
        
        print(f"Eventos encontrados: {len(events)}")
        print(f"Eventos futuros: {len(future_events)}")
        print(f"Próximos 10 seleccionados: {len(next_10)}")
        
        return next_10
    
    def get_maestria_id_mapping(self):
        """Obtiene el mapeo de maestrías a IDs"""
        # Mapeo de maestrías a IDs (puedes ajustar según tus datos)
        maestria_mapping = {
            'MKT': 'MKTRIF',
            'MRHH': 'RRHHRIF', 
            'MOSFL': 'OSFLRIF',
            'EMBA': 'EMBARIF',
            'MND': 'MNDRIF',
            'MIM': 'MIMRIF',
            'MBA Online': 'MBAORIF',
            'MFIN': 'FINRIF',
            'MBT': 'MBTRIF',
            'Fin&Law': 'FLRIF',
            'MBA Salud': 'MBASRIF',
            'EDN': 'EDNRIF',
            'REMBA': 'REMBARIF'
        }
        
        return maestria_mapping
    
    def update_descriptions(self, next_10_events):
        """Actualiza las descripciones en el sheet destino"""
        try:
            print("Actualizando descripciones...")
            
            # Leer datos del sheet destino
            dest_data = self.sheet_ops.read_sheet(
                Config.DESTINATION_SHEET_ID,
                Config.DESTINATION_RANGE,
                Config.DESTINATION_SHEET_NAME
            )
            
            if not dest_data:
                print("No se pudieron leer los datos del sheet destino")
                return False
            
            # Buscar columnas
            headers = dest_data[0]
            id_idx = None
            desc_idx = None
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'id' in header_lower and ('codigo' in header_lower or 'código' in header_lower):
                    id_idx = i
                elif 'description' in header_lower or 'descripcion' in header_lower or 'descripción' in header_lower:
                    desc_idx = i
            
            if id_idx is None or desc_idx is None:
                print("No se encontraron las columnas ID y Description en el sheet destino")
                return False
            
            print(f"Columnas encontradas - ID: {id_idx}, Description: {desc_idx}")
            
            # Obtener mapeo de maestrías
            maestria_mapping = self.get_maestria_id_mapping()
            
            # Crear mapeo de eventos por maestría
            eventos_por_maestria = {}
            for evento in next_10_events:
                maestria = evento['maestria']
                if maestria in maestria_mapping:
                    id_maestria = maestria_mapping[maestria]
                    eventos_por_maestria[id_maestria] = evento
            
            # Actualizar descripciones
            updated_rows = []
            for row in dest_data:
                new_row = row[:]
                if len(new_row) > id_idx and len(new_row) > desc_idx:
                    id_actual = new_row[id_idx].strip()
                    
                    if id_actual in eventos_por_maestria:
                        evento = eventos_por_maestria[id_actual]
                        nueva_descripcion = f"Próxima reunión informativa: {evento['fecha']} a las {evento['hora']}"
                        new_row[desc_idx] = nueva_descripcion
                        print(f"Actualizando {id_actual}: {nueva_descripcion}")
                
                updated_rows.append(new_row)
            
            # Escribir datos actualizados
            self.sheet_ops.write_sheet(
                Config.DESTINATION_SHEET_ID,
                updated_rows,
                Config.DESTINATION_RANGE,
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
            
            # Mostrar eventos seleccionados
            print("\nPróximos 10 eventos seleccionados:")
            for i, evento in enumerate(next_10, 1):
                print(f"{i}. {evento['maestria']} - {evento['fecha']} {evento['hora']} ({evento['fecha_hora'].strftime('%d/%m/%Y %H:%M')})")
            
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
