# Incendios Venezuela

Mapas de puntos de calor e incendios en Venezuela y la Guayana Esequiba.

## Sensores soportados
- **MODIS** (2000-2024)
- **VIIRS-SNPP** (2012-2024)
- **VIIRS-JPSS1** (2018-2024)

## Instalacion

```bash
pip install -r requirements.txt
```

## Uso

### Desde terminal
```bash
# Mapa satelital con Esequibo (default)
python -m fuente.principal --meses 2018-05 2018-06 --guardar mapa.png

# Mapa politico sin Esequibo, con area disputada rayada
python -m fuente.principal --no-satelital --no-esequibo --rayas --guardar mapa.png

# Diagnostico de rutas y dependencias
python -m fuente.principal --diagnostico
```

### Desde Spyder
Ejecutar `run.py` con **F5**.

### Opciones disponibles
| Argumento | Descripcion | Default |
|-----------|-------------|---------|
| `--sensor` | Sensor a utilizar | `MODIS (Aqua + Terra)` |
| `--meses` | Meses en formato AAAA-MM (max. 3) | `2018-05 2018-06` |
| `--satelital` / `--no-satelital` | Fondo satelital o politico | `satelital` |
| `--esequibo` / `--no-esequibo` | Incluir Guayana Esequiba | `esequibo` |
| `--rayas` | Mostrar area disputada con rayas | `False` |
| `--guardar` | Ruta de salida (PNG/PDF/SVG) | None |
| `--dpi` | Resolucion de exportacion | `150` |
| `--diagnostico` | Verificar rutas y dependencias | False |

## Estructura del proyecto
```
Incendios_Venezuela/
├── datos/              # CSVs de MODIS/VIIRS y shapefiles
│   ├── MODIS/
│   ├── VIIRS/
│   └── shapefiles/
├── fuente/             # Codigo fuente Python
│   ├── configuracion.py
│   ├── datos.py
│   ├── diagnostico.py
│   ├── mapa.py
│   ├── principal.py
│   └── utils.py
├── output/mapas/       # Mapas generados
├── tests/              # Pruebas unitarias
├── run.py              # Launcher para Spyder
├── requirements.txt
└── .env                # Configuracion local de rutas (opcional)
```

## Configuracion de rutas externas
Si los datos estan en otra ubicacion, crea un archivo `.env` en la raiz:
```bash
INCENDIOS_DATA=/ruta/a/datos
INCENDIOS_SHP=/ruta/a/shapefiles
```

## Diagnostico
```bash
python -m fuente.principal --diagnostico
```

## Pruebas
```bash
python -m unittest discover tests/
```


## Datos grandes y Git LFS

Este proyecto utiliza **Git LFS** para shapefiles y CSVs grandes.
Si clonas el repositorio, asegúrate de tener instalado Git LFS:

```bash
git lfs install
git lfs pull
```

## Autor
Carlos Perez

## Notas de comportamiento actuales

- Esequibo: la política es `cfg.modo_esequibo(esequibo, rayas)`.
  - `--no-esequibo`, con o sin `--rayas`: no se muestra Esequibo ni rayas.
  - `--esequibo --no-rayas`: Esequibo como unidad con Venezuela.
  - `--esequibo --rayas`: Esequibo como área disputada rayada.
- El título no incluye resolución; la resolución va en el pie izquierdo.
- El pie derecho muestra `Fuente: NASA FIRMS`.
- El logo IVIC se guarda por defecto en la esquina superior derecha y puede
  cambiarse con `INCENDIOS_LOGO_POSICION=superior_derecha` o
  `superior_izquierda` en `.env`.
- Desde P3.2 la brújula también queda incluida en los archivos guardados.
- `run.py` es un lanzador legacy para Spyder/F5; el flujo configurable es
  `python -m fuente.ejecutar_spyder`.
