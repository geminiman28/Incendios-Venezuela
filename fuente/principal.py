"""Generador de mapas de incendios Venezuela.

Uso terminal:
    python -m fuente.principal --meses 2018-05 2018-06 --guardar
    python -m fuente.principal --no-satelital --no-esequibo --rayas --guardar
    python -m fuente.principal --diagnostico
"""

import sys
from pathlib import Path

from fuente import configuracion as cfg
from fuente.diagnostico import diagnostico
from fuente.datos import (
    archivos_csv_venezuela,
    cobertura_mensual,
    procesar_datos,
    reportar_disponibilidad,
)
from fuente.utils import configurar_logging, fmt_annos, get_logger

logger = get_logger(__name__)

OUTPUT_DIR = cfg.MAPAS_GENERADOS


def _en_spyder():
    """Detecta si estamos en Spyder/IPython."""
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


# Backend Agg en terminal con --guardar: fijar ANTES de importar pyplot
if "--guardar" in sys.argv and not _en_spyder():
    import matplotlib
    matplotlib.use("Agg")

from fuente.mapa import generar_mapa  # noqa: E402 (import tras fijar backend)


def main():
    configurar_logging()
    parser = cfg.crear_parser()
    args = parser.parse_args()

    producto = cfg.resolver_producto(args)
    ficha_actual = cfg.ficha(producto)

    if args.diagnostico:
        meses_diag = cfg.parsear_meses(args.meses)
        diagnostico(producto=producto, meses=meses_diag)
        return

    if args.disponibilidad:
        reportar_disponibilidad()
        return

    if not cfg.verificar_rutas_criticas():
        logger.warning("\n[!] Usa --diagnostico para detalles.")
        return

    cfg.asegurar_directorio_salida()

    meses = cfg.parsear_meses(args.meses)

    logger.info("Procesando datos...")
    gdf, world, gdf_e, ven, guy, stats, gdf_ese = procesar_datos(
        producto=producto,
        meses=meses,
        esequibo=args.esequibo,
        rayas=args.rayas,
    )

    if gdf is None or gdf.empty:
        logger.warning("[!] Sin píxeles tras filtrar -> mapa omitido.")
        return

    res_texto = ficha_actual["res_texto"]
    total_píxeles = len(gdf)

    guardar_como = args.guardar
    if guardar_como is not None and not Path(guardar_como).is_absolute():
        guardar_como = str(OUTPUT_DIR / guardar_como)

    if not guardar_como and not _en_spyder():
        logger.info(
            "Sin --guardar y fuera de Spyder: no se mostrara ni guardara mapa."
        )


    logger.info("Generando mapa...")
    fig = generar_mapa(
        gdf=gdf,
        world=world,
        meses=meses,
        satelital=args.satelital,
        esequibo=args.esequibo,
        rayas=args.rayas,
        res_texto=res_texto,
        total_píxeles=total_píxeles,
        sensor_nombre=ficha_actual["nombre"],
        gdf_ese=gdf_ese,
        guardar_como=guardar_como,
        dpi=args.dpi,
    )

    if guardar_como:
        logger.info("Mapa guardado: %s", guardar_como)

    if _en_spyder():
        try:
            import matplotlib.pyplot as plt
            plt.show()
            logger.info("Mapa mostrado en ventana de Spyder.")
        except Exception:
            logger.warning("No se pudo mostrar el mapa en Spyder.")
    elif guardar_como:
        import matplotlib.pyplot as plt
        plt.close(fig)
        logger.info("Mapa cerrado (terminal sin visualizacion).")

    periodo = cfg.formatear_periodo(meses)

    # ============================================================
    # INFORME
    # ============================================================
    print("\n" + "=" * 60)
    print("  Informe")
    print("=" * 60)

    # --- PARTE A: ANÁLISIS DE DATOS DISPONIBLES EN CARPETAS ---
    print("\n  [A] DATOS DISPONIBLES EN CARPETAS CSV")
    print("      " + "-" * 46)

    for prod_id, ficha_i in cfg.PRODUCTOS.items():
        v_files = archivos_csv_venezuela(prod_id)
        annos = sorted(
            {
                int(f.stem.split("_")[1])
                for f in v_files
                if f.stem.split("_")[1].isdigit()
            }
        )

        print(f"\n      📡 {ficha_i['nombre']}")
        print(f"          Años: {fmt_annos(annos)} ({len(v_files)} archivos)")

        if not args.cobertura:
            if v_files:
                print("          (--cobertura para detalle mes a mes)")
            continue

        for csv_file in v_files:
            resultado = cobertura_mensual(csv_file)
            if resultado is None:
                continue
            anno, meses_disp = resultado
            meses_faltan = [
                cfg.MESES_ES[m - 1].capitalize()
                for m in range(1, 13)
                if m not in meses_disp
            ]
            if meses_faltan:
                print(f"          {anno}: ❌ Faltan {', '.join(meses_faltan)} ({len(meses_disp)}/12)")
            else:
                print(f"          {anno}: ✅ Completo (12/12)")

    # --- PARTE B: CONFIGURACIÓN DE ESTA EJECUCIÓN ---
    print("\n  [B] CONFIGURACIÓN DE ESTA EJECUCIÓN")
    print("      " + "-" * 46)
    print(f"      Sensor:      {ficha_actual['nombre']}")
    print(f"      Año:         {meses[0].year}")
    print(f"      Periodo:     {periodo}")
    print(f"      Meses:       {', '.join(cfg.MESES_ES[m.month - 1].capitalize() for m in meses[:-1])}")
    print(f"      Modo:        {'Satelital' if args.satelital else 'Politico'}")
    esq_str = "Incluido (unidad)" if args.esequibo and not args.rayas else "Excluido" if not args.esequibo else "Area en disputa (rayas)"
    print(f"      Esequibo:    {esq_str}")
    print(f"      Resolución:  {res_texto}")

    # --- PARTE C: DATOS EMPLEADOS ---
    print("\n  [C] DATOS EMPLEADOS")
    print("      " + "-" * 46)
    print(f"      Venezuela:        {stats['venezuela']:>6} píxeles")
    print(f"      Guyana:           {stats['guyana']:>6} píxeles")
    print(f"      Esequibo:         {stats['esequibo']:>6} píxeles")
    print("      " + "-" * 46)
    if args.esequibo and not args.rayas:
        print(f"      Venezuela Total:  {stats['venezuela_total']:>6} píxeles")
        print("        (Venezuela + Esequibo como unidad)")
    else:
        print(f"      Venezuela Total:  {stats['venezuela']:>6} píxeles")
        print("        (Esequibo excluido)")
    print(f"      Total en mapa:    {total_píxeles:>6} píxeles")

    # --- PARTE D: RESULTADOS POR MES ---
    print("\n  [D] RESULTADOS POR MES")
    print("      " + "-" * 46)
    for i in range(len(meses) - 1):
        sub = gdf[(gdf["acq_datetime"] >= meses[i]) & (gdf["acq_datetime"] < meses[i + 1])]
        print(f"      {cfg.MESES_ES[meses[i].month - 1].capitalize():<12} {len(sub):>8} píxeles")
    print(f"      {'TOTAL':<12} {total_píxeles:>8} píxeles")

    # --- PARTE E: ARCHIVO GENERADO ---
    if guardar_como:
        print(f"\n  [E] ARCHIVO GENERADO")
        print("      " + "-" * 46)
        print(f"      {guardar_como}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
