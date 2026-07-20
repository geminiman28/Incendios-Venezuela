#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades compartidas del proyecto."""

import logging
import sys
import time
import functools
import shutil
from pathlib import Path


def configurar_logging(nivel=logging.INFO, archivo=None):
    """Configura logging a consola y archivo opcional.

    Args:
        nivel: Nivel de logging (default: INFO).
        archivo: Ruta opcional para log a archivo.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    if archivo:
        handlers.append(logging.FileHandler(archivo, encoding="utf-8"))

    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def get_logger(nombre):
    """Obtiene un logger con el nombre del módulo.

    Args:
        nombre: Nombre del módulo (__name__).

    Returns:
        Logger configurado.
    """
    return logging.getLogger(nombre)


def timed(func):
    """Decorador que mide y loggea el tiempo de ejecución de una función."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        elapsed = time.perf_counter() - inicio
        logger.info("%s completado en %.3fs", func.__name__, elapsed)
        return resultado
    return wrapper


def verificar_espacio(ruta: Path, mb_minimos: int = 500) -> bool:
    """Verifica que haya al menos mb_minimos MB libres en la partición."""
    try:
        _, _, libre_b = shutil.disk_usage(ruta.parent if ruta.is_file() else ruta)
        return (libre_b / (1024 * 1024)) >= mb_minimos
    except Exception:
        return True  # Si no podemos verificar, asumimos que sí hay espacio
