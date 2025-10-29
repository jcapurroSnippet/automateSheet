# RIF Scheduler - Programador de Reuniones Informativas

Sistema automatizado para programar reuniones informativas de maestrías usando Google Sheets.

## 🎯 ¿Qué hace?

El RIF Scheduler:
1. **Lee datos de RIF** desde un Google Sheet con columnas de maestrías, fechas y horas
2. **Selecciona los próximos 10 eventos** basándose en la fecha y hora actual
3. **Matchea las maestrías con sus IDs** usando un mapeo configurable
4. **Actualiza las descripciones** en el sheet destino con la próxima reunión

## 🚀 Instalación Rápida

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar automáticamente:**
```bash
python setup.py
```

3. **Configurar credenciales:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita Google Sheets API
   - Crea credenciales OAuth 2.0
   - Descarga el archivo JSON como `credentials.json`

4. **Configurar sheets:**
   - Edita `config.env` con tus IDs de sheets
   - Configura los rangos de datos

## ⚙️ Configuración

Edita el archivo `config.env`:

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

# Nombres de las hojas
SOURCE_SHEET_NAME=Hoja1
DESTINATION_SHEET_NAME=Hoja1
```

## 🚀 Uso

```bash
# Ejecutar RIF Scheduler
python rif_scheduler.py
```

## 📊 Estructura de Datos

### Sheet Origen (Datos de RIF):
Debe tener columnas con:
- **Maestría**: Nombre de la maestría (MKT, EMBA, etc.)
- **Fecha RIF**: Fecha en formato DD/MM (ej: 03/09, 21/10)
- **Hora RIF**: Hora en formato HH.MM o HH (ej: 18.30, 19)

### Sheet Destino (Resultado):
Debe tener columnas con:
- **ID**: Código de la maestría (MKT, EMBA, etc.)
- **Description**: Descripción que se actualizará

## 🔧 Mapeo de Maestrías

El sistema incluye un mapeo predefinido en `config_rif.py`:

- MKT → MKT
- MRHH → RRHH  
- MOSFL → OSFL
- EMBA → EMBA
- MND → MND
- MIM → MIM
- MBA Online → MBAO
- MFIN → FIN
- MBT → MBT
- Fin&Law → FL
- MBA Salud → MBAS
- EDN → EDN
- REMBA → REMBA

## 📁 Estructura del Proyecto

```
automateSheet/
├── rif_scheduler.py          # Script principal
├── config_rif.py            # Configuración RIF
├── auth.py                   # Autenticación
├── sheet_operations.py       # Operaciones con sheets
├── config.env               # Variables de entorno
├── config.env.example       # Plantilla
├── setup.py                 # Configuración automática
├── requirements.txt         # Dependencias
├── GUIA_RIF.md             # Guía detallada
└── README.md               # Este archivo
```

## 🔐 Autenticación

En la primera ejecución se abrirá el navegador para autorizar la aplicación.

## 📝 Logs

El sistema muestra logs detallados:
- Eventos encontrados
- Eventos futuros
- Próximos 10 seleccionados
- Actualizaciones realizadas

## 🐛 Solución de Problemas

- **Error de autenticación**: Verifica que `credentials.json` exista
- **Error de permisos**: Verifica que los IDs de sheets sean correctos
- **Error de rango**: Verifica que los rangos especificados existan
- **Error de mapeo**: Verifica que las maestrías estén en el mapeo de `config_rif.py`

## 📚 Documentación Adicional

- **GUIA_RIF.md**: Guía completa con ejemplos y solución de problemas