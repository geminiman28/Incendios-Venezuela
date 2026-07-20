#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generacion del mapa con matplotlib y contextily."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import contextily as cx
from pyproj import Transformer
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon

from fuente import configuracion as cfg
from fuente.utils import get_logger

logger = get_logger(__name__)
# ------------------------------------------------------------------
# Constantes de estilo visual (tema centralizado)
# ------------------------------------------------------------------
ESTILO = {
    "logo": {
        "margen": 12,
        "factor_altura": 0.76,
        "posiciones": {"superior_derecha", "superior_izquierda"},
    },
    "satelital": {
        "otros": {"facecolor": "gray", "edgecolor": "black", "alpha": 0.30},
        "ven": {"facecolor": "none", "edgecolor": "black"},
        "disputa": {"facecolor": "none", "edgecolor": "black"},
        "bg": None,
    },
    "politico": {
        "otros": {"facecolor": "#84b6ca", "edgecolor": "gray", "alpha": 1.0},
        "ven": {"facecolor": "forestgreen", "edgecolor": "black"},
        "disputa": {"facecolor": "forestgreen", "edgecolor": "black"},
        "bg": "skyblue",
    },
    "grosor": {
        "venezuela": 1.5,
        "esequibo": 1.5,
        "disputa": 1.5,
        "otros": 0.8,
    },
}

def _escala(ax, crs, extent):
    """Dibuja barra de escala 250/500 km con segmentos B/N."""
    TOTAL, SEG = 500_000, 50_000
    N_SEGS, COLORES = 10, ["black", "white"] * 5

    x_min, x_max, y_min, y_max = extent[0], extent[2], extent[1], extent[3]
    ancho = x_max - x_min

    if crs == "4326":
        m_por_deg = 111_320 * np.cos(np.radians((y_min + y_max) / 2))
        ancho_m = ancho * m_por_deg
    else:
        m_por_deg = 1.0
        ancho_m = ancho

    if TOTAL > ancho_m * 0.5:
        TOTAL, SEG = 250_000, 25_000

    seg = SEG / m_por_deg if crs == "4326" else SEG
    total_len = TOTAL / m_por_deg if crs == "4326" else TOTAL
    # Posición: extremo izquierdo en -64° (unidades del CRS)
    x0 = -64.0 if crs == "4326" else -64.0 * 111_320
    y0 = y_min + (y_max - y_min) * 0.03
    alto = (y_max - y_min) * 0.018

    for i in range(N_SEGS):
        x1 = x0 + seg * i
        x2 = x0 + seg * (i + 1)
        ax.fill(
            [x1, x2, x2, x1],
            [y0, y0, y0 + alto, y0 + alto],
            color=COLORES[i],
            edgecolor="black",
            linewidth=0.5,
            zorder=8,
        )

    ax.plot(
        [x0, x0 + total_len, x0 + total_len, x0, x0],
        [y0, y0, y0 + alto, y0 + alto, y0],
        color="black",
        linewidth=1.2,
        zorder=8,
    )
    for i in range(1, N_SEGS):
        ax.plot(
            [x0 + seg * i, x0 + seg * i],
            [y0, y0 + alto],
            color="black",
            linewidth=0.8,
            zorder=8,
        )

    ax.text(
        x0 + total_len / 2,
        y0 - alto * 0.5,
        f"{TOTAL // 1000:.0f} km",
        ha="center",
        va="top",
        fontsize=9,
        color="white",
        weight="bold",
        zorder=8,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="black")],
    )

def _ticks_grados(ax, xticks, yticks, crs, extent, transformer):
    """Establece ticks en grados."""
    if crs == "4326":
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
    elif crs == "3857":
        lc = (extent[0] + extent[2]) / 2
        ax.set_xticks([transformer.transform(x, lc)[0] for x in xticks])
        ax.set_yticks([transformer.transform(lc, y)[1] for y in yticks])
    ax.set_xticklabels([f"{x}°" for x in xticks])
    ax.set_yticklabels([f"{y}°" for y in yticks])

def _plot_mundo(ax, world, satelital, rayas=False):
    """Plotea Venezuela, disputa y otros paises desde el mismo world."""
    if world.empty or "ADMIN" not in world.columns:
        return

    mask_ven = world.ADMIN.str.contains("Venezuela", case=False, na=False)
    ven = world[mask_ven]

    mask_disputa = pd.Series([False] * len(world))
    if "TYPE" in world.columns:
        mask_disputa = world["TYPE"].str.contains(
            "Disputed", case=False, na=False
        )
    if not mask_disputa.any():
        mask_disputa = world["ADMIN"].str.contains(
            "Disputed", case=False, na=False
        )

    disputa = world[mask_disputa]
    otros = world[~(mask_ven | mask_disputa)]

    tema = ESTILO["satelital" if satelital else "politico"]

    if satelital:
        otros.plot(
            ax=ax,
            facecolor=tema["otros"]["facecolor"],
            edgecolor="none",
            linewidth=0,
            alpha=tema["otros"]["alpha"],
            zorder=3,
        )
        # Frontera otros países (solo línea, encima de puntos)
        otros.plot(
            ax=ax,
            facecolor="none",
            edgecolor=tema["otros"]["edgecolor"],
            linewidth=0.8,
            alpha=tema["otros"]["alpha"],
            zorder=9,
        )
        if not ven.empty:
            ven.plot(
                ax=ax,
                facecolor="none",
                edgecolor="none",
                linewidth=0,
                zorder=3,
            )
        # Frontera Venezuela (solo línea, encima de puntos)
        if not ven.empty:
            ven.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=1.5,
                zorder=10,
            )
        if not disputa.empty:
            disputa.plot(
                ax=ax,
                facecolor="none",
                edgecolor="none",
                linewidth=0,
                zorder=3,
            )
        # Frontera disputa (solo línea, encima de puntos)
        if not disputa.empty:
            disputa.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=1.5,
                zorder=10,
            )
    else:
        otros.plot(
            ax=ax,
            facecolor=tema["otros"]["facecolor"],
            edgecolor="none",
            linewidth=0,
            alpha=tema["otros"]["alpha"],
            zorder=3,
        )
        # Frontera otros países (solo línea, encima de puntos)
        otros.plot(
            ax=ax,
            facecolor="none",
            edgecolor=tema["otros"]["edgecolor"],
            linewidth=0.8,
            alpha=tema["otros"]["alpha"],
            zorder=9,
        )
        if not ven.empty:
            ven.plot(
                ax=ax,
                facecolor=tema["ven"]["facecolor"],
                edgecolor="none",
                linewidth=0,
                alpha=1.0,
                zorder=3,
            )
        # Frontera Venezuela (solo línea, encima de puntos)
        if not ven.empty:
            ven.plot(
                ax=ax,
                facecolor="none",
                edgecolor="none",
                linewidth=0,
                zorder=3,
            )
        # Frontera Venezuela (solo línea, encima de puntos)
        if not ven.empty:
            ven.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=1.5,
                zorder=10,
            )
        if not disputa.empty:
            disputa.plot(
                ax=ax,
                facecolor=tema["ven"]["facecolor"],
                edgecolor="none",
                linewidth=0,
                alpha=1.0,
                zorder=3,
            )
        # Frontera disputa (solo línea, encima de puntos)
        if not disputa.empty:
            disputa.plot(
                ax=ax,
                facecolor="none",
                edgecolor="none",
                linewidth=0,
                zorder=3,
            )
        # Frontera disputa (solo línea, encima de puntos)
        if not disputa.empty:
            disputa.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=1.5,
                zorder=10,
            )

def _plot_esequibo(ax, crs, rayas=False, satelital=False):
    """Dibuja Esequibo con matplotlib.patches.Polygon (sin descartes)."""
    if not cfg.SHP_ESQ.exists():
        logger.warning(f"Shapefile Esequibo no encontrado: {cfg.SHP_ESQ}")
        return

    try:
        ese = gpd.read_file(cfg.SHP_ESQ)
        if ese.empty:
            return

        if (
            crs == "3857"
            and ese.crs is not None
            and "3857" not in str(ese.crs)
        ):
            ese = ese.to_crs(epsg=3857)

        geom = unary_union(ese.geometry)
        g = ESTILO["grosor"]

        def _add_patches(geometry, **kwargs):
            polys = geometry.geoms if isinstance(geometry, MultiPolygon) else [geometry]
            for p in polys:
                coords = np.array(p.exterior.coords)
                patch = mpatches.Polygon(coords, closed=True, **kwargs)
                ax.add_patch(patch)

        # Fondo base del Esequibo
        _add_patches(geom, facecolor="none" if satelital else "forestgreen", edgecolor="none", alpha=1.0, zorder=100)
        if rayas:
            # Rayas grises 35% atenuación (solo cuando se solicita)
            _add_patches(geom, facecolor="none", edgecolor="black", linewidth=1.5, hatch="/////", alpha=0.5, zorder=101)
        # Borde negro
        _add_patches(geom, facecolor="none", edgecolor="black", linewidth=g["esequibo"], alpha=1.0, zorder=102)

    except Exception as e:
        logger.warning(f"Error dibujando Esequibo: {e}")
        # Fallback simple sin recursión
        try:
            if cfg.SHP_ESQ.exists():
                ese = gpd.read_file(cfg.SHP_ESQ)
                if not ese.empty:
                    if crs == "3857" and ese.crs is not None and "3857" not in str(ese.crs):
                        ese = ese.to_crs(epsg=3857)
                    g = ESTILO["grosor"]
                    fc = "none" if satelital else "forestgreen"
                    # Fondo base
                    ese.plot(ax=ax, facecolor=fc, edgecolor="none", linewidth=0, alpha=1.0)
                    if rayas:
                        # Rayas grises 35%
                        ese.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.5, hatch="/////", alpha=0.5)
                    # Borde negro
                    ese.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=g["esequibo"], alpha=1.0)
        except Exception as e2:
            logger.warning(f"Fallback Esequibo también falló: {e2}")




def _logo_ivic(fig, ax, logo_path, satelital=False, transformer=None):
    """Logo en la esquina superior derecha del mapa.

    Mantiene el tamaño actual: 76% de la distancia entre 0° y 2°.
    """
    try:
        logo_path = Path(logo_path)
        if not logo_path.exists():
            logger.warning("Logo IVIC no encontrado: %s", logo_path)
            return

        img = plt.imread(logo_path)
        if img.size == 0:
            return

        fig.canvas.draw()
        axbb = ax.get_window_extent()
        inv_data = ax.transData.inverted()

        h_img, w_img = img.shape[0], img.shape[1]
        x_ref = ax.get_xlim()[0]
        lon_ref = (cfg.EXTENT_DEG[0] + cfg.EXTENT_DEG[2]) / 2

        if satelital and transformer is not None:
            _, y0 = transformer.transform(lon_ref, 0.0)
            _, y2 = transformer.transform(lon_ref, 2.0)
        else:
            y0, y2 = 0.0, 2.0

        p0 = ax.transData.transform((x_ref, y0))
        p2 = ax.transData.transform((x_ref, y2))

        alto_px = abs(p2[1] - p0[1]) * ESTILO["logo"]["factor_altura"]
        if alto_px <= 0:
            return

        ancho_px = alto_px * (w_img / h_img)

        margen = ESTILO["logo"]["margen"]
        max_ancho = axbb.width - 2 * margen
        max_alto = axbb.height - 2 * margen
        if max_ancho <= 0 or max_alto <= 0:
            return

        escala = min(
            (max_ancho * 0.98) / ancho_px,
            (max_alto * 0.98) / alto_px,
            1.0,
        )
        ancho_px *= escala
        alto_px *= escala

        pos = getattr(cfg, "LOGO_POSICION", "superior_derecha")
        if pos not in ESTILO["logo"]["posiciones"]:
            logger.warning("Posición de logo inválida: %s", pos)
            pos = "superior_derecha"

        y_top_px = axbb.y1 - margen
        y_bottom_px = y_top_px - alto_px
        if pos == "superior_izquierda":
            x_left_px = axbb.x0 + margen
            x_right_px = x_left_px + ancho_px
        else:
            x_right_px = axbb.x1 - margen
            x_left_px = x_right_px - ancho_px

        inf_izq = inv_data.transform([(x_left_px, y_bottom_px)])[0]
        sup_der = inv_data.transform([(x_right_px, y_top_px)])[0]

        ax.imshow(
            img,
            extent=[
                inf_izq[0],
                sup_der[0],
                inf_izq[1],
                sup_der[1],
            ],
            transform=ax.transData,
            aspect="auto",
            interpolation="antialiased",
            zorder=20,
        )
    except Exception as e:
        logger.warning("No se pudo insertar el logo IVIC: %s", e)


def _titulo_leyenda(meses, sensor_nombre, res_texto):
    """Genera titulo y leyenda del mapa."""
    n = len(meses) - 1
    colores = cfg.PALETA[:n]
    if n > len(cfg.PALETA):
        raise ValueError(f"Maximo {len(cfg.PALETA)} meses. Recibidos: {n}")

    leyenda = [
        mpatches.Patch(
            color=colores[i],
            alpha=1.0,
            label=cfg.MESES_ES[meses[i].month - 1].capitalize(),
        )
        for i in range(n)
    ]

    mi = cfg.MESES_ES[meses[0].month - 1].capitalize()
    mf = cfg.MESES_ES[meses[n - 1].month - 1].capitalize() if n > 1 else mi
    titulo_meses = mi if n == 1 else f"{mi}-{mf}"

    titulo = (
        f"Deteccion de Pixeles de Incendios y Puntos de Calor, "
        f"{titulo_meses} {meses[0].year}"
        + chr(10)
        + f"Sensor {sensor_nombre}"
    )

    return titulo, leyenda, colores

def generar_mapa(
    gdf: gpd.GeoDataFrame,
    world: gpd.GeoDataFrame,
    meses: pd.DatetimeIndex,
    satelital: bool,
    esequibo: bool,
    rayas: bool,
    res_texto: str,
    total_píxeles: int,
    sensor_nombre: str,
    guardar_como: str | None = None,
    dpi: int = 300,
) -> plt.Figure:
    """Genera y muestra/guarda el mapa. Siempre retorna la figura."""
    w = cfg.EXTENT_DEG[2] - cfg.EXTENT_DEG[0]
    h = cfg.EXTENT_DEG[3] - cfg.EXTENT_DEG[1]
    fig = plt.figure(figsize=(cfg.FIG_HEIGHT * w / h, cfg.FIG_HEIGHT), facecolor="white")
    ax = fig.add_subplot(111)

    tr = None
    x0 = y0 = x1 = y1 = None

    if satelital:
        tr = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x0, y0 = tr.transform(cfg.EXTENT_DEG[0], cfg.EXTENT_DEG[1])
        x1, y1 = tr.transform(cfg.EXTENT_DEG[2], cfg.EXTENT_DEG[3])
        gdf = gdf.to_crs(epsg=3857)
        world = world.to_crs(epsg=3857)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        try:
            cx.add_basemap(
                ax,
                source=cx.providers.Esri.WorldImagery,
                attribution="",
                zorder=0,
            )
        except Exception as e:
            logger.warning(f"Fondo satelital no disponible (sin conexion?): {e}")
            ax.set_facecolor("white")
        ax.text(
            0.995,
            0.03,
            "(C) Esri",
            transform=ax.transAxes,
            va="center",
            ha="right",
            fontsize=9,
            color="#C0C0C0",
            alpha=0.65,
        )
    else:
        ax.set_xlim(cfg.EXTENT_DEG[0], cfg.EXTENT_DEG[2])
        ax.set_ylim(cfg.EXTENT_DEG[1], cfg.EXTENT_DEG[3])
        ax.set_facecolor("skyblue")
        fig.set_facecolor("white")
        x0, y0, x1, y1 = cfg.EXTENT_DEG

    _plot_mundo(ax, world, satelital, rayas=rayas)

    crs_code = "3857" if satelital else "4326"
    if cfg.modo_esequibo(esequibo, rayas) == "disputa":
        crs_code = "3857" if satelital else "4326"
        _plot_esequibo(ax, crs_code, rayas=rayas, satelital=satelital)

    _ticks_grados(
        ax, cfg.XTICKS_DEG, cfg.YTICKS_DEG, crs_code, cfg.EXTENT_DEG, tr
    )
    _escala(ax, crs_code, [x0, y0, x1, y1] if satelital else cfg.EXTENT_DEG)

    titulo, leyenda, colores = _titulo_leyenda(meses, sensor_nombre, res_texto)

    for i in range(len(meses) - 1):
        sub = gdf[
            (gdf["acq_datetime"] >= meses[i])
            & (gdf["acq_datetime"] < meses[i + 1])
        ]
        if not sub.empty:
            alpha = cfg.ALPHAS[i] if i < len(cfg.ALPHAS) else 0.3
            sub.plot(
                ax=ax,
                color=colores[i],
                markersize=cfg.MARKERSIZE,
                marker="s",
                alpha=alpha,
                zorder=5,
            )

    ax.legend(
        handles=leyenda,
        loc="lower left",
        title="Pixeles por mes",
        frameon=True,
        fancybox=True,
    )
    ax.set_title(titulo, weight="bold")

    crs_num = 3857 if satelital else 4326
    estilo_epsg = (
        {"color": "#C0C0C0", "alpha": 0.65} if satelital else {}
    )
    ax.text(
        1.0,
        0.0,
        f"EPSG:{crs_num}",
        transform=ax.transAxes,
        fontsize=9,
        va="bottom",
        ha="right",
        **estilo_epsg,
    )
    ax.text(
        0,
        -0.05,
        f"{total_píxeles} píxeles de incendios y puntos de calor de resolución {res_texto}",
        transform=ax.transAxes,
        ha="left",
        fontsize=9,
        style="italic",
        color="gray",
    )
    ax.text(
        1.0,
        -0.05,
        "Fuente: NASA FIRMS",
        transform=ax.transAxes,
        ha="right",
        fontsize=9,
        style="italic",
        color="black",
    )

    ax.set_aspect("equal")
    _logo_ivic(fig, ax, cfg.LOGO_IVIC, satelital, tr)

    if guardar_como:
        ext = Path(guardar_como).suffix.lower()
        kwargs = {"dpi": dpi, "bbox_inches": "tight"}
        if ext in (".png", ".jpg", ".jpeg"):
            kwargs["pad_inches"] = 0.05
        elif ext == ".pdf":
            kwargs["format"] = "pdf"
        elif ext == ".svg":
            kwargs["format"] = "svg"

        fig.savefig(guardar_como, **kwargs)
        logger.info(f"Mapa guardado: {guardar_como}")

    # ============================================
    # BRÚJULA DE NORTE - Unicode ▲ + N
    # ============================================
    # Posición en coordenadas geográficas (EPSG:4326)
    bx_deg = -73.5    # longitud oeste
    by_deg = 15.0     # latitud norte
    
    # Convertir a coordenadas del mapa si es satelital (EPSG:3857)
    if satelital and tr is not None:
        bx, by = tr.transform(bx_deg, by_deg)
    else:
        bx, by = bx_deg, by_deg
    
    # Color: plateado para satelital, negro para político
    color_brujula = '#C0C0C0' if satelital else 'black'
    alpha_brujula = 0.65 if satelital else 1.0

    # Triángulo Unicode + letra N (compactos y juntos)
    ax.text(bx, by + 0.08, '▲', ha='center', va='bottom',
            fontsize=14, color=color_brujula, alpha=alpha_brujula,
            zorder=15)
    ax.text(bx, by, 'N', ha='center', va='top',
            fontsize=9, fontweight='bold', color=color_brujula,
            alpha=alpha_brujula, zorder=16)

    return fig
