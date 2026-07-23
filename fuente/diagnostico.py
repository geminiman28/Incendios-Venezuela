#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico completo de rutas, datos y dependencias."""

import sys
from pathlib import Path

from fuente import configuracion as cfg
from fuente.utils import get_logger

logger = get_logger(__name__)

_MODULOS = [
    "pandas",
    "geopandas",
    "matplotlib",
    "contextily",
    "pyproj",
    "numpy",
]

_RESULTADOS = []


def _check(label, ruta, es_archivo=False):
    """Imprime estado de ruta o módulo y registra el resultado."""
    if isinstance(ruta, str):
        try:
            __import__(ruta)
            print(f"  ✅ {ruta:<25} OK")
            _RESULTADOS.append(True)
            return True
        except ImportError as e:
            print(f"  ❌ {ruta:<25} {e}")
            _RESULTADOS.append(False)
            return False

    ok = ruta.exists()
    tipo = "archivo" if es_archivo else "carpeta"
    print(f"  {'✅' if ok else '❌'} {label:<25} {tipo:<8} {ruta}")
    _RESULTADOS.append(ok)
    return ok


def diagnostico(sensor=None, meses=None):
    """Ejecuta diagnóstico completo."""
    import pandas as pd

    print("=" * 60)
    print("  DIAGNÓSTICO: Incendios Venezuela")
    print("=" * 60)
    _RESULTADOS.clear()

    print("\n1. SISTEMA")
    print(f"   Python: {sys.version.split()[0]} | {sys.platform}")

    print("\n2. DEPENDENCIAS")
    deps_ok = all(_check(m, m) for m in _MODULOS)

    print("\n3. RUTAS")
    print(f"   Raíz: {cfg.RAIZ}")
    _check("RAIZ", cfg.BASE)
    _check("datos", cfg.DATA)
    _check("shapefiles", cfg.SHP)

    print("\n4. SHAPEFILES")
    for nombre, ruta in [
        ("Mundo (Eseq)", cfg.SHP_WORLD["esequibo"]),
        ("Mundo (normal)", cfg.SHP_WORLD["normal"]),
        ("Mundo (rayas)", cfg.SHP_WORLD["rayas"]),
        ("Esequibo", cfg.SHP_ESQ),
    ]:
        _check(nombre, ruta, True)

    print("\n5. CSVs")
    sensor = sensor or cfg.SENSOR_DEFAULT
    if meses is None:
        meses = pd.date_range(
            cfg.DEFAULT_MESES_INICIO, cfg.DEFAULT_MESES_FIN, freq="MS"
        )
    rutas = cfg._rutas_csv(meses)
    if sensor in rutas:
        print(f"   Sensor: {sensor} | {meses[0].date()} → {meses[-1].date()}")
        for zona, key in [("Venezuela", "ven"), ("Guyana", "guy")]:
            print(f"   {zona}:")
            for r in rutas[sensor][key]:
                _check(f"     {r.name}", r, True)
    else:
        print(f"   ❌ Sensor '{sensor}' no reconocido.")

    print("\n6. RESUMEN")
    todo_ok = deps_ok and all(_RESULTADOS)
    if not deps_ok:
        print(
            "   ❌ Instala: pip install pandas geopandas"
            " matplotlib contextily pyproj numpy"
        )
    elif not todo_ok:
        print("   ❌ Faltan rutas, shapefiles o CSVs. Revisa secciones 3-5.")
    else:
        print("   ✅ Todo listo.")
    print("=" * 60)


if __name__ == "__main__":
    diagnostico()
