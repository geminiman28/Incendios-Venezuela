#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuracion centralizada con deteccion automatica de rutas."""

import os
import sys
import argparse
from pathlib import Path

import pandas as pd

# ============================================================
# CONFIGURACION EDITABLE — Modifica aqui para Spyder o defaults
# ============================================================
MODO_POLITICO = False          # True = mapa politico, False = satelital
MOSTRAR_ESEQUIBO = True   # True = incluir Esequibo
MOSTRAR_RAYAS = False       # True = rayas grises en area disputada
SENSOR_DEFAULT = "MODIS (Aqua + Terra)"
MESES_DEFAULT = ["2024-01","2024-02"]
DPI_DEFAULT = 150
GUARDAR_DEFAULT = None        # None = no guardar, o string con ruta
COBERTURA_DEFAULT = False     # True = escaneo mes a mes de CSVs en informe (lento)
# ============================================================

from fuente.utils import get_logger

logger = get_logger(__name__)


def _detectar_raiz():
    """Detecta la raiz del proyecto."""
    fuente_dir = Path(__file__).resolve().parent
    raiz = fuente_dir.parent
    if (raiz / "datos").exists() or (raiz / "fuente").exists():
        return raiz

    cwd = Path.cwd()
    for ruta in (cwd, cwd.parent):
        if (ruta / "datos").exists() and (ruta / "fuente").exists():
            return ruta

    env = os.getenv("INCENDIOS_BASE")
    if env:
        return Path(env).resolve()

    return raiz


def _cargar_env(raiz):
    """Lee archivo .env simple (KEY=VALUE)."""
    env_path = raiz / ".env"
    if not env_path.exists():
        return {}
    config = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip().strip('"').strip("'")
    return config


def _resolver_ruta(raiz, env, clave, default):
    """Resuelve ruta: env_var > .env > default relativo."""
    valor = os.getenv(clave) or env.get(clave)
    if valor:
        p = Path(valor)
        return p.resolve() if p.is_absolute() else (raiz / p).resolve()
    return (raiz / default).resolve()


RAIZ = _detectar_raiz()
_ENV = _cargar_env(RAIZ)

BASE = _resolver_ruta(RAIZ, _ENV, "INCENDIOS_BASE", ".")
DATA = _resolver_ruta(RAIZ, _ENV, "INCENDIOS_DATA", "datos")
SHP = _resolver_ruta(RAIZ, _ENV, "INCENDIOS_SHP", "datos/shapefiles")

SHPVG = SHP / "Venezuela y Guayana Esequiba (nuevos)"
SHP_VEN = SHPVG / "ne_10m_admin_0_countries_modificacion_esequibo"
SHP_RAYAS = SHPVG / "ne_10m_admin_0_countries_con_areas_en_disputa_suramerica"
SHP_NORMAL = SHPVG / "ne_10m_admin_0_countries"
SHP_ESQ = SHPVG / "guayana_esequiba/guayana_esequiba.shp"

SHP_WORLD = {
    "esequibo": SHP_VEN / "ne_10m_admin_0_countries.shp",
    "rayas": SHP_RAYAS / "world_con_areas_en_disputa_suramerica.shp",
    "normal": SHP_NORMAL / "ne_10m_admin_0_countries.shp",
}

MAPAS_GENERADOS = BASE / "output" / "mapas"


def asegurar_directorio_salida():
    """Crea la carpeta de salida si no existe (llamar al generar mapas)."""
    MAPAS_GENERADOS.mkdir(parents=True, exist_ok=True)

LOGO_IVIC = _resolver_ruta(
    RAIZ, _ENV, "INCENDIOS_LOGO", "IVICvertical.png"
)

LOGO_POSICION = (
    os.getenv("INCENDIOS_LOGO_POSICION")
    or _ENV.get("INCENDIOS_LOGO_POSICION", "superior_derecha")
).strip().lower()

SENSORES_VALIDOS = [
    "VIIRS (SNPP)",
    "VIIRS (JPSS1)",
    "MODIS (Aqua + Terra)",
]

DEFAULT_MESES_INICIO = MESES_DEFAULT[0] if MESES_DEFAULT else "2018-05-01"
DEFAULT_MESES_FIN = (
    MESES_DEFAULT[-1] if len(MESES_DEFAULT) > 1 else MESES_DEFAULT[0]
) if MESES_DEFAULT else "2018-08-01"

EXTENT_DEG = [-74, 0, -58, 15.71]
XTICKS_DEG = [-74, -72, -70, -68, -66, -64, -62, -60, -58]
YTICKS_DEG = [0, 2, 4, 6, 8, 10, 12, 14]

MESES_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

PALETA = ["yellow", "darkorange", "red", "darkred", "maroon"]
ALPHAS = [1.0, 0.5, 0.2, 0.1]
MARKERSIZE = 1
FIG_HEIGHT = 10

RESOLUCION = {
    "VIIRS (SNPP)": "0.375 Km x 0.375 Km",
    "VIIRS (JPSS1)": "0.375 Km x 0.375 Km",
    "MODIS (Aqua + Terra)": "1.0 Km x 1.0 Km",
}


def _rutas_csv(meses):
    """Genera rutas CSV segun los meses solicitados."""
    annos = sorted({m.year for m in meses})
    res = {}

    for sensor, pref in [
        ("VIIRS (SNPP)", "viirs-snpp"),
        ("VIIRS (JPSS1)", "viirs-jpss1"),
    ]:
        v = (
            DATA
            / "VIIRS"
            / "Datos Venezuela viirs"
            / f"Datos Venezuela {pref}"
        )
        g = DATA / "VIIRS" / "Datos Guyana viirs" / f"Datos Guyana {pref}"
        res[sensor] = {
            "ven": [v / f"{pref}_{a}_Venezuela.csv" for a in annos],
            "guy": [g / f"{pref}_{a}_Guyana.csv" for a in annos],
        }

    v = DATA / "MODIS" / "Datos Venezuela MODIS"
    g = DATA / "MODIS" / "Datos Guyana MODIS"
    res["MODIS (Aqua + Terra)"] = {
        "ven": [v / f"modis_{a}_Venezuela.csv" for a in annos],
        "guy": [g / f"modis_{a}_Guyana.csv" for a in annos],
    }
    return res


try:
    from argparse import BooleanOptionalAction
except ImportError:  # pragma: no cover
    BooleanOptionalAction = None


def crear_parser():
    """Devuelve parser argparse configurado."""
    parser = argparse.ArgumentParser(
        prog="incendios_venezuela",
        description="Genera mapas de incendios para Venezuela.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python -m fuente.principal\n"
            "  python -m fuente.principal --meses 2018-05"
            " 2018-06 --guardar m.png\n"
            "  python -m fuente.principal --no-satelital"
            " --no-esequibo --rayas\n"
            "  python -m fuente.principal --diagnostico"
        ),
    )
    parser.add_argument(
        "--sensor",
        choices=SENSORES_VALIDOS,
        default=SENSOR_DEFAULT,
        help=f"Sensor (default: {SENSOR_DEFAULT})",
    )
    parser.add_argument(
        "--meses",
        nargs="+",
        metavar="YYYY-MM",
        default=MESES_DEFAULT,
        help="Meses AAAA-MM (max 3).",
    )
    if BooleanOptionalAction:
        parser.add_argument(
            "--satelital",
            action=BooleanOptionalAction,
            default=not MODO_POLITICO,
            help="Fondo satelital (default: True)",
        )
    else:
        parser.add_argument(
            "--satelital",
            action="store_true",
            default=not MODO_POLITICO,
            help="Fondo satelital (default)",
        )
        parser.add_argument(
            "--no-satelital",
            dest="satelital",
            action="store_false",
            help="Fondo politico simple",
        )
    if BooleanOptionalAction:
        parser.add_argument(
            "--esequibo",
            action=BooleanOptionalAction,
            default=MOSTRAR_ESEQUIBO,
            help="Incluir Esequibo (default: True)",
        )
    else:
        parser.add_argument(
            "--esequibo",
            action="store_true",
            default=MOSTRAR_ESEQUIBO,
            help="Incluir Esequibo (default)",
        )
        parser.add_argument(
            "--no-esequibo",
            dest="esequibo",
            action="store_false",
            help="Mostrar Esequibo como disputa",
        )
    if BooleanOptionalAction:
        parser.add_argument(
            "--rayas",
            action=BooleanOptionalAction,
            default=MOSTRAR_RAYAS,
            help="Area disputada con rayas (default: False)",
        )
    else:
        parser.add_argument(
            "--rayas",
            action="store_true",
            default=MOSTRAR_RAYAS,
            help="Area disputada con rayas (solo sin --esequibo)",
        )
    parser.add_argument(
        "--guardar",
        metavar="RUTA",
        default=GUARDAR_DEFAULT,
        help="Guardar mapa en archivo (PNG/PDF/SVG).",
    )
    parser.add_argument(
        "--diagnostico",
        action="store_true",
        help="Verificar rutas y dependencias.",
    )
    parser.add_argument(
        "--disponibilidad",
        action="store_true",
        help="Mostrar annos disponibles por sensor y salir.",
    )
    if BooleanOptionalAction:
        parser.add_argument(
            "--cobertura",
            action=BooleanOptionalAction,
            default=COBERTURA_DEFAULT,
            help="Informe: escaneo mes a mes de todos los CSV (lento)",
        )
    else:
        parser.add_argument(
            "--cobertura",
            action="store_true",
            default=COBERTURA_DEFAULT,
            help="Informe: escaneo mes a mes de todos los CSV (lento)",
        )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DPI_DEFAULT,
        help="DPI exportacion (default: 150)",
    )
    return parser


def parsear_meses(lista):
    """Convierte ['2018-05'] a pd.date_range."""
    if not lista:
        return pd.date_range(
            DEFAULT_MESES_INICIO, DEFAULT_MESES_FIN, freq="MS"
        )

    fechas = sorted({pd.to_datetime(m, format="%Y-%m") for m in lista})
    if len(fechas) > 3:
        raise ValueError(f"Maximo 3 meses permitidos. Recibidos: {len(fechas)}")

    fin = fechas[-1] + pd.DateOffset(months=1)
    return pd.date_range(fechas[0], fin, freq="MS")


def verificar_rutas_criticas():
    """Verifica que existan carpetas esenciales."""
    faltantes = [
        f"  • {n}: {r}"
        for n, r in [("RAIZ", BASE), ("datos", DATA), ("shp", SHP)]
        if not r.exists()
    ]
    if faltantes:
        msg = (
            "Rutas no encontradas:\n"
            + "\n".join(faltantes)
            + f"\n   Raiz: {RAIZ}\n"
            + "   Crear .env en la raiz si moviste el proyecto."
        )
        logger.warning(msg)
        return False
    return True


def modo_esequibo(esequibo, rayas):
    """Devuelve la política cartográfica del Esequibo.

    unidad: Esequibo se integra a Venezuela y suma puntos de Guyana.
    disputa: solo si esequibo=True y rayas=True; se excluyen puntos
             y el área se marca con rayas.
    excluido: sin esequibo no se muestra el área ni rayas, aunque
              rayas esté activo; los puntos del Esequibo se excluyen.
    """
    if not esequibo:
        return "excluido"
    if rayas:
        return "disputa"
    return "unidad"


def formatear_periodo(meses):
    """Devuelve string 'Mes' o 'Mes1-Mes2' a partir de un DatetimeIndex."""
    if len(meses) < 2:
        return MESES_ES[meses[0].month - 1].capitalize()
    m0 = meses[0].month - 1
    m1 = meses[-2].month - 1
    mi = MESES_ES[m0].capitalize()
    mf = MESES_ES[m1].capitalize()
    return mi if m0 == m1 else f"{mi}-{mf}"
