# Especificaciones del programa de mapas de incendios

Documento de contexto para futuras modificaciones. Preparado para ser proporcionado a Kimi cuando se retome el proyecto.

- Proyecto: `Incendios_Venezuela`
- Ruta local: `/home/ccab/Documents/IVIC/Mapas/Python/Incendios y Puntos de Calor/Incendios_Venezuela`
- Fecha de esta especificación: 2026-07-21
- Estado deseado del repo: historia limpia de 1 commit, tag `v2.0-funcional-consolidada`
- Archivos que NO deben versionarse: `.env`, `__pycache__/`, `*.pyc`, `output/mapas/*` salvo `output/mapas/.gitkeep`

## 1. Modos de mapa

Hay dos modos principales, controlados por `--satelital` / `--no-satelital`.

| Aspecto | Modo satelital | Modo político |
|---|---|---|
| Activación | `--satelital` | `--no-satelital` |
| CRS | `EPSG:3857` Web Mercator | `EPSG:4326` lat/lon |
| Fondo | Basemap `Esri.WorldImagery` vía `contextily`; si falla, fondo blanco | Mar `skyblue`; figura blanca |
| Venezuela | Sin relleno; borde negro `linewidth=1.5` | Relleno `forestgreen`; borde negro `1.5` |
| Otros países | Relleno gris con `alpha=0.30`; borde negro atenuado | Relleno `#84b6ca`; borde gris |
| Área disputada/Esequibo | Sin relleno si se dibuja; borde negro; rayas si `--rayas` | Relleno `forestgreen`; rayas grises/negras si `--rayas` |
| Atribución Esri | Manual: `(C) Esri`, gris `#C0C0C0`, `alpha=0.65`, abajo a la derecha | No aplica |
| Texto EPSG | `EPSG:3857`, gris claro atenuado | `EPSG:4326`, negro |
| Brújula | Plateada `#C0C0C0`, `alpha=0.65` | Negra |
| Barra de escala | 500 km o 250 km si el ancho es corto; 10 segmentos negro/blanco; inicia en `-64°`; etiqueta blanca con borde negro | Igual |
| Ticks | Se transforman a `EPSG:3857`, pero se etiquetan en grados | Directos en grados |

## 2. Extensión, ticks y figura

- Extensión geográfica: `EXTENT_DEG = [-74, 0, -58, 15.71]`
  - Oeste: `-74°`
  - Sur: `0°`
  - Este: `-58°`
  - Norte: `15.71°`
- Ticks X: `[-74, -72, -70, -68, -66, -64, -62, -60, -58]`
- Ticks Y: `[0, 2, 4, 6, 8, 10, 12, 14]`
- Figura: `FIG_HEIGHT = 10`; ancho proporcional a la extensión.
- Relación de aspecto: `ax.set_aspect("equal")`.

## 3. Píxeles de calor

- Marcador: cuadrado, `marker="s"`.
- Tamaño: `MARKERSIZE = 1`.
- Orden de dibujo: `zorder=5`.
- Paleta por mes: `["yellow", "darkorange", "red", "darkred", "maroon"]`.
- Transparencias por mes: `[1.0, 0.5, 0.2, 0.1]`.
- CLI permite máximo 3 meses por `parsear_meses`.
- Leyenda: esquina inferior izquierda, título `"Pixeles por mes"`, meses en español.

## 4. Título, pie y fuente

Estado actual reciente:

- El título ya NO incluye resolución.
- Formato del título:
  ```text
  Deteccion de Pixeles de Incendios y Puntos de Calor, <Mes o Meses> <Año>
  Sensor <nombre del sensor>
  ```
- Pie izquierdo: total de píxeles y resolución del sensor.
- Pie derecho: `Fuente: NASA FIRMS`, negro, misma altura que el pie izquierdo.
- Sensores y resolución:
  - `VIIRS (SNPP)`: `0.375 Km x 0.375 Km`
  - `VIIRS (JPSS1)`: `0.375 Km x 0.375 Km`
  - `MODIS (Aqua + Terra)`: `1.0 Km x 1.0 Km`

## 5. Logo IVIC

Estado actual de prueba:

- Ubicación por defecto: esquina superior derecha del mapa.
- Posición configurable: `INCENDIOS_LOGO_POSICION=superior_derecha` o `superior_izquierda`.
- Tamaño: altura equivalente al 76% de la distancia entre las marcas `0°` y `2°`.
- Se mantiene la proporción original del PNG.
- Margen interno: 12 px, centralizado en `ESTILO["logo"]`.
- Ruta configurable: `LOGO_IVIC = _resolver_ruta(RAIZ, _ENV, "INCENDIOS_LOGO", "IVICvertical.png")`.
- Archivo actual: `IVICvertical.png` en la raíz del proyecto.
- Implementación actual: `ax.imshow(...)` en coordenadas de datos, no `OffsetImage`, para evitar escalado por DPI.

## 6. Esequibo / área disputada

Flags:

- `--esequibo` / `--no-esequibo`
- `--rayas`

Comportamiento vigente tras Prioridad 2:

- Política central: `cfg.modo_esequibo(esequibo, rayas)`.
- `--no-esequibo`, con o sin `--rayas`: `excluido`; no se muestra Esequibo ni rayas, y los puntos del Esequibo se excluyen.
- `--esequibo --no-rayas`: `unidad`; Esequibo tratado como unidad con Venezuela y se suman puntos de Guyana dentro del shapefile del Esequibo.
- `--esequibo --rayas`: `disputa`; se excluyen puntos del Esequibo y el área se marca con rayas.
- Las capas shapefile pasan por `_asegurar_crs`; si falta CRS se asume `EPSG:4326` con advertencia.

## 7. Rutas y configuración

- Configuración central: `fuente/configuracion.py`.
- `.env` es local y no debe versionarse.
- Variables soportadas:
  - `INCENDIOS_BASE`
  - `INCENDIOS_DATA`
  - `INCENDIOS_SHP`
  - `INCENDIOS_LOGO`
- Defaults editables actuales en `configuracion.py`:
  - `MODO_POLITICO = False`
  - `MOSTRAR_ESEQUIBO = True`
  - `MOSTRAR_RAYAS = False`
  - `SENSOR_DEFAULT = "MODIS (Aqua + Terra)"`
  - `MESES_DEFAULT = ["2024-01", "2024-02"]`
  - `DPI_DEFAULT = 150`

## 8. Elementos gráficos fijos

- Barra de escala:
  - `TOTAL=500_000`, `SEG=50_000`, 10 segmentos.
  - Si el ancho es corto: `TOTAL=250_000`, `SEG=25_000`.
  - Posición horizontal: extremo izquierdo en `-64°`.
  - Posición vertical: `y_min + 3%` del alto.
  - Alto de barra: `1.8%` del alto del mapa.
- Brújula:
  - Posición geográfica base: `bx_deg=-73.5`, `by_deg=15.0`.
  - En satelital se transforma a `EPSG:3857`.
  - Tras Prioridad 3.2, `_guardar()` se ejecuta al final de `generar_mapa`, por lo que la brújula también queda incluida en los archivos guardados.
  - Revisar separación vertical entre `▲` y `N` en satelital; históricamente hubo riesgo de solape por unidades.
- Texto EPSG: esquina inferior derecha dentro del axes.
- Texto Esri: esquina inferior derecha, ligeramente por encima del borde, gris atenuado.

## 9. Entrada/salida

- Entrada: CSVs MODIS/VIIRS para Venezuela y Guyana, más shapefiles.
- Salida por defecto: `output/mapas`.
- `--guardar` relativo se resuelve dentro de `output/mapas`.
- Formatos: PNG/PDF/SVG.
- En terminal con `--guardar` y fuera de Spyder se usa backend `Agg` y se cierra la figura.
- En Spyder se muestra con `plt.show()`.

## 10. Comandos de prueba rápidos

Político con rayas:

```bash
cd "/home/ccab/Documents/IVIC/Mapas/Python/Incendios y Puntos de Calor/Incendios_Venezuela"
python -m fuente.principal --no-satelital --no-esequibo --rayas --meses 2024-01 2024-02 --guardar test_politico.png
```

Satelital con Esequibo:

```bash
cd "/home/ccab/Documents/IVIC/Mapas/Python/Incendios y Puntos de Calor/Incendios_Venezuela"
python -m fuente.principal --satelital --esequibo --meses 2024-01 2024-02 --guardar test_satelital.png
```

Compilación rápida:

```bash
python -m py_compile fuente/configuracion.py fuente/datos.py fuente/mapa.py fuente/principal.py fuente/utils.py
```

## 11. Checklist antes de modificar

1. Confirmar rama y limpieza:
   ```bash
   git branch --show-current
   git status --short
   git rev-list --count HEAD
   ```
2. No versionar `.env`, `__pycache__`, `*.pyc` ni `output/mapas/*`.
3. Si se cambia tamaño/posición del logo, probar ambos modos: satelital y político.
4. Si se cambia CRS, probar barra de escala, ticks, brújula, logo y atribuciones.
5. Si se cambia Esequibo/rayas, revisar tanto `datos.py` como `mapa.py`.
6. Si se cambia título/pie, mantener fuente `NASA FIRMS` al pie derecho salvo instrucción contraria.
7. Antes de commit, compilar módulos y generar al menos un mapa de cada modo.
