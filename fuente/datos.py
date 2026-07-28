#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga, filtrado y geoprocesamiento de datos de incendios."""

import pandas as pd
import geopandas as gpd

from fuente import configuracion as cfg
from fuente.utils import fmt_annos, get_logger

logger = get_logger(__name__)


def _asegurar_crs(gdf, nombre):
    """Garantiza CRS sin romper capas ya referenciadas."""
    if gdf.crs is None:
        logger.warning("%s sin CRS; se asume EPSG:4326", nombre)
        return gdf.set_crs(epsg=4326, allow_override=True)
    return gdf


def _annos_en_directorio(directorio, patron):
    """Extrae años (4 dígitos) de nombres de archivo."""
    if not directorio.exists():
        return []
    return sorted(
        {
            int(p)
            for f in directorio.glob(patron)
            for p in f.stem.split("_")
            if p.isdigit() and len(p) == 4
        }
    )


def reportar_disponibilidad():
    """Imprime tabla de años disponibles por sensor."""
    roots = [
        ("VIIRS (SNPP)", "viirs-snpp", "VIIRS"),
        ("VIIRS (JPSS1)", "viirs-jpss1", "VIIRS"),
        ("MODIS (Aqua + Terra)", "modis", "MODIS"),
    ]
    print("\nBIBLIOTECA     Venezuela        Guyana")
    print("─" * 50)
    for sensor, pref, folder in roots:
        if folder == "MODIS":
            v, g = (
                cfg.DATA / "MODIS" / "Datos Venezuela MODIS",
                cfg.DATA / "MODIS" / "Datos Guyana MODIS",
            )
            pat = "modis_*.csv"
        else:
            v = (
                cfg.DATA
                / "VIIRS"
                / "Datos Venezuela viirs"
                / f"Datos Venezuela {pref}"
            )
            g = (
                cfg.DATA
                / "VIIRS"
                / "Datos Guyana viirs"
                / f"Datos Guyana {pref}"
            )
            pat = f"{pref}_*.csv"
        annos_v = fmt_annos(_annos_en_directorio(v, pat))
        annos_g = fmt_annos(_annos_en_directorio(g, pat))
        print(f"{sensor:<15} {annos_v:<16} {annos_g:<16}")


def archivos_csv_venezuela(sensor):
    """Devuelve lista ordenada de CSVs de Venezuela para un sensor."""
    if sensor == "MODIS (Aqua + Terra)":
        directorio = cfg.DATA / "MODIS" / "Datos Venezuela MODIS"
        patron = "modis_*.csv"
    elif sensor in ("VIIRS (SNPP)", "VIIRS (JPSS1)"):
        pref = "viirs-snpp" if sensor == "VIIRS (SNPP)" else "viirs-jpss1"
        directorio = (
            cfg.DATA
            / "VIIRS"
            / "Datos Venezuela viirs"
            / f"Datos Venezuela {pref}"
        )
        patron = f"{pref}_*.csv"
    else:
        return []
    if not directorio.exists():
        return []
    return sorted(directorio.glob(patron))


def cobertura_mensual(csv_path):
    """Meses presentes en un CSV: (anno, {meses}) o None si falla."""
    try:
        df = pd.read_csv(csv_path, usecols=["acq_date"])
        fechas = pd.to_datetime(df["acq_date"], errors="coerce").dropna()
    except Exception as e:
        logger.warning("No se pudo leer %s para cobertura: %s", csv_path, e)
        return None
    if fechas.empty:
        logger.warning("%s sin fechas validas.", csv_path.name)
        return None
    return fechas.iloc[0].year, set(fechas.dt.month.unique())


def _cargar_csvs(rutas):
    """Concatena CSVs existentes; devuelve DataFrame vacío si ninguno."""
    fragmentos = []
    for ruta in rutas:
        if not ruta.exists():
            continue
        try:
            df = pd.read_csv(ruta, encoding="utf-8", low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(ruta, encoding="latin-1", low_memory=False)
        except Exception as e:
            logger.warning(f"{ruta.name}: {e}")
            continue

        if df.empty:
            logger.warning(f"{ruta.name}: vacío, omitido.")
            continue

        REQUIRED = {"latitude", "longitude", "acq_date"}
        if not REQUIRED.issubset(df.columns):
            faltan = REQUIRED - set(df.columns)
            logger.warning(f"{ruta.name}: faltan columnas {faltan}, omitido.")
            continue

        fragmentos.append(df)

    if not fragmentos:
        return pd.DataFrame()

    cols = set.intersection(*(set(df.columns) for df in fragmentos))
    if len(cols) < 3:
        logger.warning("CSVs con columnas muy diferentes.")
        return pd.DataFrame()

    return pd.concat([df[list(cols)] for df in fragmentos], ignore_index=True)


def _parse_datetime(df):
    """Añade columna acq_datetime desde acq_date + acq_time."""
    if df.empty or "acq_date" not in df.columns:
        return df

    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"] + " " + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        errors="coerce",
    )
    n = df.acq_datetime.isna().sum()
    if n:
        logger.warning(f"{n} filas con fecha inválida omitidas.")
        df = df.dropna(subset=["acq_datetime"])
    return df


def leer_csv(sensor: str, meses: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (df_VEN, df_GUY) con datetime parseado."""
    rutas = cfg._rutas_csv(meses)
    if sensor not in rutas:
        logger.error(f"Sensor '{sensor}' no reconocido.")
        return pd.DataFrame(), pd.DataFrame()

    ven = _parse_datetime(_cargar_csvs(rutas[sensor]["ven"]))
    guy = _parse_datetime(_cargar_csvs(rutas[sensor]["guy"]))
    return ven, guy


def filtrar_por_meses(df: pd.DataFrame, meses: pd.DatetimeIndex) -> pd.DataFrame:
    """Filtra DataFrame dentro del rango de meses."""
    if df.empty or "acq_datetime" not in df.columns:
        return df
    return df[(df.acq_datetime >= meses[0]) & (df.acq_datetime < meses[-1])]


def a_geo(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Convierte DataFrame a GeoDataFrame (EPSG:4326)."""
    if df.empty or "longitude" not in df.columns:
        return gpd.GeoDataFrame(
            df, geometry=gpd.GeoSeries([], crs="EPSG:4326"), crs="EPSG:4326"
        )
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    )


def procesar_datos(sensor: str, meses: pd.DatetimeIndex, esequibo: bool, rayas: bool):
    """Carga, filtra y procesa datos. Retorna (gdf, world, gdf_e, ven, guy)."""
    ven, guy = leer_csv(sensor, meses)

    ven = filtrar_por_meses(ven, meses)   # CORREGIDO: filtrar Venezuela
    guy = filtrar_por_meses(guy, meses)
    gdf_ven = a_geo(ven)
    gdf_guy = a_geo(guy)

    # --- Seleccionar shapefile del mundo ---
    # Caso 1: esequibo=True, rayas=False -> mundo con Esequibo
    # Caso 2/3: esequibo=False o rayas=True -> mundo normal
    modo = cfg.modo_esequibo(esequibo, rayas)
    clave = "esequibo" if modo == "unidad" else "normal"
    shp_ruta = cfg.SHP_WORLD[clave]
    try:
        world = gpd.read_file(shp_ruta) if shp_ruta.exists() else gpd.GeoDataFrame()
        world = _asegurar_crs(world, "mundo")
    except Exception as e:
        logger.error(f"Error leyendo shapefile {shp_ruta}: {e}")
        world = gpd.GeoDataFrame()

    gdf_e = None

    # --- Caso 1: Venezuela incluye Esequibo como unidad ---
    # Se suman los puntos de Guyana que caen en el Esequibo
    if modo == "unidad":
        if cfg.SHP_ESQ.exists() and not gdf_guy.empty:
            ese = _asegurar_crs(gpd.read_file(cfg.SHP_ESQ), "esequibo").to_crs(gdf_guy.crs)
            joined = gdf_guy.sjoin(ese, predicate="within", how="inner")
            if not joined.empty:
                # Conservar solo columnas originales de gdf_guy
                cols = [c for c in gdf_guy.columns if c in joined.columns]
                gdf_e = joined[cols].copy()
                gdf = gpd.GeoDataFrame(
                    pd.concat([gdf_ven, gdf_e], ignore_index=True), crs="EPSG:4326"
                )
                print(f"  [INFO] +{len(gdf_e)} puntos Guyana en Esequibo (total: {len(gdf)})")
            else:
                print("  [INFO] 0 puntos Guyana en Esequibo")
                gdf = gdf_ven
        else:
            gdf = gdf_ven

    # --- Caso 2/3: Esequibo no es parte de Venezuela o es disputa ---
    # Se excluyen los puntos de Venezuela que caen en el Esequibo
    else:
        if cfg.SHP_ESQ.exists() and not gdf_ven.empty:
            ese = _asegurar_crs(gpd.read_file(cfg.SHP_ESQ), "esequibo").to_crs(gdf_ven.crs)
            joined = gdf_ven.sjoin(ese, predicate="within", how="left")
            fuera = joined.index_right.isna()
            n_dentro = (~fuera).sum()
            gdf_ven = gdf_ven[fuera].copy()
            if n_dentro > 0:
                print(f"  [INFO] -{n_dentro} puntos Venezuela en Esequibo excluidos")
        gdf = gdf_ven

    # Calcular estadísticas para el informe
    stats = {
        "venezuela": len(gdf_ven) if modo == "unidad" else len(gdf),
        "guyana": len(guy) if not guy.empty else 0,
        "esequibo": len(gdf_e) if gdf_e is not None else 0,
        "venezuela_total": len(gdf),
    }

    return gdf, world, gdf_e, ven, guy, stats
