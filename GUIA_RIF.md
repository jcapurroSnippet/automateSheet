# 🎯 Guía del RIF Scheduler

## ¿Qué hace el RIF Scheduler?

El RIF Scheduler es un script especializado que:

1. **Lee datos de RIF** desde un Google Sheet con columnas de:
   - Maestrías (ej: MKT, EMBA, MBA Online)
   - Fecha del RIF (formato DD/MM)
   - Hora del RIF (formato HH.MM o HH)

2. **Selecciona los próximos 10 eventos** basándose en la fecha y hora actual

3. **Matchea las maestrías con sus IDs** usando un mapeo predefinido

4. **Actualiza las descripciones** en el sheet destino con la próxima reunión informativa

## 🚀 Uso Rápido

### 1. Configurar
```bash
# Configurar proyecto
python setup.py

# Editar config.env con tus IDs de sheets
```

### 2. Ejecutar
```bash
# Ejecutar RIF Scheduler
python rif_scheduler.py

# O usar el script de prueba
python test_rif.py
```

## ⚙️ Configuración

### Archivo config.env
```env
# IDs de los spreadsheets
SOURCE_SHEET_ID=tu_sheet_id_origen
DESTINATION_SHEET_ID=tu_sheet_id_destino

# Rangos de datos
SOURCE_RANGE=A:Z
DESTINATION_RANGE=A:Z

# Rangos específicos para RIF
RIF_SOURCE_RANGE=A:Z
RIF_DEST_RANGE=A:Z
```

### Estructura del Sheet Origen
El sheet debe tener columnas con:
- **Maestría**: Nombre de la maestría (MKT, EMBA, etc.)
- **Fecha RIF**: Fecha en formato DD/MM (ej: 03/09, 21/10)
- **Hora RIF**: Hora en formato HH.MM o HH (ej: 18.30, 19)

### Estructura del Sheet Destino
El sheet debe tener columnas con:
- **ID**: Código de la maestría (MKT, EMBA, etc.)
- **Description**: Descripción que se actualizará

## 🔧 Mapeo de Maestrías

El sistema incluye un mapeo predefinido en `config_rif.py`:

```python
MAESTRIA_MAPPING = {
    'MKT': 'MKT',
    'MRHH': 'RRHH', 
    'MOSFL': 'OSFL',
    'EMBA': 'EMBA',
    'MND': 'MND',
    'MIM': 'MIM',
    'MBA Online': 'MBAO',
    'MFIN': 'FIN',
    'MBT': 'MBT',
    'Fin&Law': 'FL',
    'MBA Salud': 'MBAS',
    'EDN': 'EDN',
    'REMBA': 'REMBA'
}
```

## 📊 Ejemplo de Funcionamiento

### Datos de Entrada (Sheet Origen):
| Maestría | Fecha RIF | Hora RIF |
|----------|-----------|----------|
| MKT      | 03/09     | 18.30    |
| EMBA     | 21/10     | 19       |
| MBA Online | 23/10   | 19       |

### Resultado (Sheet Destino):
| ID | Description |
|----|-------------|
| MKT | Próxima reunión informativa: 03/09 a las 18.30 |
| EMBA | Próxima reunión informativa: 21/10 a las 19 |
| MBAO | Próxima reunión informativa: 23/10 a las 19 |

## 🐛 Solución de Problemas

### Error: "No se encontraron las columnas necesarias"
- Verifica que el sheet tenga columnas con "maestría", "fecha" y "hora"
- Los nombres pueden variar (maestría, maestría, fecha rif, hora rif)

### Error: "No se encontraron eventos válidos"
- Verifica que las fechas estén en formato DD/MM
- Verifica que las horas estén en formato HH.MM o HH
- Verifica que no haya celdas vacías en las columnas necesarias

### Error: "No hay eventos futuros"
- Verifica que las fechas sean futuras
- El sistema asume año actual si no se especifica

## 📝 Logs del Sistema

El sistema muestra logs detallados:
- Eventos encontrados
- Eventos futuros
- Próximos 10 seleccionados
- Actualizaciones realizadas

## 🔄 Flujo Completo

1. **Inicialización**: Autenticación con Google Sheets
2. **Lectura**: Lee datos del sheet origen
3. **Parsing**: Extrae maestrías, fechas y horas
4. **Filtrado**: Selecciona eventos futuros
5. **Ordenamiento**: Ordena por fecha y hora
6. **Selección**: Toma los próximos 10
7. **Mapeo**: Convierte maestrías a IDs
8. **Actualización**: Actualiza descripciones en sheet destino
