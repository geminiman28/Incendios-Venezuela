#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de humo y carga de datos reales."""

import unittest
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent

from fuente import configuracion as cfg
from fuente.datos import leer_csv, filtrar_por_meses, a_geo


class TestConfiguracion(unittest.TestCase):
    """Tests de configuración y rutas."""

    def test_raiz_detectada(self):
        self.assertTrue(cfg.RAIZ.exists())

    def test_carpetas_criticas(self):
        self.assertTrue(cfg.RAIZ.exists())
        self.assertTrue((cfg.RAIZ / "fuente").exists())
        if not cfg.DATA.exists():
            self.skipTest(f"Datos no disponibles: {cfg.DATA}")


    def test_sensores_validos(self):
        self.assertIn("VIIRS (JPSS1)", cfg.SENSORES_VALIDOS)
        self.assertIn("VIIRS (SNPP)", cfg.SENSORES_VALIDOS)
        self.assertIn("MODIS (Aqua + Terra)", cfg.SENSORES_VALIDOS)

    def test_parser_defaults(self):
        parser = cfg.crear_parser()
        args = parser.parse_args([])
        self.assertEqual(args.sensor, cfg.SENSOR_DEFAULT)
        self.assertEqual(args.satelital, not cfg.MODO_POLITICO)
        self.assertEqual(args.esequibo, cfg.MOSTRAR_ESEQUIBO)
        self.assertEqual(args.rayas, cfg.MOSTRAR_RAYAS)
        self.assertEqual(args.cobertura, cfg.COBERTURA_DEFAULT)
        self.assertIsNone(args.producto)


    def test_parsear_meses(self):
        meses = cfg.parsear_meses(["2018-05", "2018-06"])
        self.assertEqual(len(meses), 3)
        self.assertIsInstance(meses, pd.DatetimeIndex)

    def test_parsear_meses_error_mas_de_3(self):
        with self.assertRaises(ValueError):
            cfg.parsear_meses(["2018-01", "2018-02", "2018-03", "2018-04"])

    def test_formatear_periodo(self):
        meses = cfg.parsear_meses(["2018-05"])
        self.assertEqual(cfg.formatear_periodo(meses), "Mayo")
        meses2 = cfg.parsear_meses(["2018-05", "2018-06"])
        self.assertEqual(cfg.formatear_periodo(meses2), "Mayo-Junio")


    def test_modo_esequibo(self):
        self.assertEqual(cfg.modo_esequibo(True, False), "unidad")
        self.assertEqual(cfg.modo_esequibo(True, True), "disputa")
        self.assertEqual(cfg.modo_esequibo(False, True), "excluido")
        self.assertEqual(cfg.modo_esequibo(False, False), "excluido")


    def test_logo_posicion_valida(self):
        self.assertIn(
            cfg.LOGO_POSICION,
            {"superior_derecha", "superior_izquierda"},
        )

    def test_logo_posicion_desde_entorno(self):
        import importlib
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"INCENDIOS_LOGO_POSICION": "superior_izquierda"}):
            importlib.reload(cfg)
            self.assertEqual(cfg.LOGO_POSICION, "superior_izquierda")
        importlib.reload(cfg)


    def test_verificar_espacio_usa_libre(self):
        from unittest.mock import patch
        from fuente import utils

        mb = 1024 * 1024
        with patch(
            "fuente.utils.shutil.disk_usage",
            return_value=(100 * mb, 90 * mb, 10 * mb),
        ):
            self.assertFalse(utils.verificar_espacio(cfg.RAIZ, 11))
            self.assertTrue(utils.verificar_espacio(cfg.RAIZ, 10))

    def test_verificar_espacio_ruta_nueva(self):
        from fuente import utils
        self.assertTrue(
            utils.verificar_espacio(cfg.RAIZ / "output" / "mapa_nuevo_xyz.png")
        )

    def test_registro_productos(self):
        self.assertEqual(
            set(cfg.PRODUCTOS),
            {
                "firms_viirs_snpp_presencia",
                "firms_viirs_jpss1_presencia",
                "firms_modis_presencia",
                "firms_modis_frp",
                "firms_viirs_jpss1_frp",
            },
        )
        for sensor in cfg.SENSORES_VALIDOS:
            self.assertIn(sensor, cfg.SENSOR_A_PRODUCTO)

    def test_fichas_campos_obligatorios(self):
        campos = {
            "nombre", "familia", "variable", "unidad", "fuente",
            "carpeta_ven", "carpeta_guy", "plantilla", "patron_glob",
            "formato", "columnas_requeridas", "columna_valor",
            "renderer", "coloracion", "leyenda", "res_texto", "cita",
        }
        for producto, f in cfg.PRODUCTOS.items():
            self.assertTrue(campos.issubset(f.keys()), f"Falta campo en {producto}")
            if producto in cfg.SENSOR_A_PRODUCTO.values():
                self.assertEqual(cfg.SENSOR_A_PRODUCTO[f["nombre"]], producto)

    def test_resolver_producto(self):
        parser = cfg.crear_parser()
        args = parser.parse_args([])
        self.assertEqual(cfg.resolver_producto(args), cfg.PRODUCTO_DEFAULT)
        args = parser.parse_args(["--producto", "firms_viirs_jpss1_presencia"])
        self.assertEqual(
            cfg.resolver_producto(args), "firms_viirs_jpss1_presencia"
        )

    def test_ficha_desconocida(self):
        with self.assertRaises(KeyError):
            cfg.ficha("producto_que_no_existe")

class TestDatos(unittest.TestCase):
    """Tests de carga de datos."""

    def setUp(self):
        if not cfg.DATA.exists():
            self.skipTest(f"Datos no disponibles: {cfg.DATA}")

    def test_rutas_csv(self):
        meses = pd.date_range("2018-05-01", "2018-08-01", freq="MS")
        rutas = cfg._rutas_csv(meses)
        self.assertIn("firms_viirs_jpss1_presencia", rutas)
        self.assertIn("firms_modis_presencia", rutas)
        self.assertIsInstance(
            rutas["firms_viirs_jpss1_presencia"]["ven"][0], Path
        )

    def test_cargar_csv_viirs_jpss1_2018(self):
        """Carga real de datos VIIRS JPSS1 2018."""
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, guy = leer_csv("firms_viirs_jpss1_presencia", meses)
        # Al menos uno debe tener datos
        self.assertFalse(
            ven.empty and guy.empty,
            "No se cargaron datos de ninguna zona"
        )


    def test_filtrar_por_meses(self):
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, _ = leer_csv("firms_viirs_jpss1_presencia", meses)
        if not ven.empty:
            filtrado = filtrar_por_meses(ven, meses)
            self.assertIsInstance(filtrado, pd.DataFrame)

    def test_a_geo(self):
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, _ = leer_csv("firms_viirs_jpss1_presencia", meses)
        if not ven.empty:
            gdf = a_geo(ven)
            self.assertTrue(hasattr(gdf, "geometry"))
            self.assertEqual(gdf.crs.to_string(), "EPSG:4326")

    def test_cobertura_mensual(self):
        from fuente.datos import archivos_csv_venezuela, cobertura_mensual
        archivos = archivos_csv_venezuela("firms_viirs_jpss1_presencia")
        if not archivos:
            self.skipTest("Sin CSVs VIIRS JPSS1 de Venezuela")
        resultado = cobertura_mensual(archivos[0])
        self.assertIsNotNone(resultado)
        anno, meses = resultado
        self.assertGreaterEqual(anno, 2000)
        self.assertTrue(all(1 <= m <= 12 for m in meses))

    def test_parse_datetime_sin_acq_time(self):
        from fuente.datos import _parse_datetime
        df = pd.DataFrame({
            "latitude": [8.5],
            "longitude": [-62.1],
            "acq_date": ["2018-05-03"],
        })
        resultado = _parse_datetime(df)
        self.assertIn("acq_datetime", resultado.columns)
        self.assertFalse(resultado["acq_datetime"].isna().any())

    def test_procesar_datos_retorna_gdf_ese(self):
        from fuente.datos import procesar_datos
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        resultado = procesar_datos("firms_viirs_jpss1_presencia", meses, esequibo=True, rayas=False)
        self.assertEqual(len(resultado), 7)


class TestProductosFRP(unittest.TestCase):
    """Tests de productos de valor continuo (FRP)."""

    def _gdf_frp(self):
        import geopandas as gpd

        df = pd.DataFrame({
            "latitude": [8.0, 8.001, 5.0],
            "longitude": [-62.0, -62.001, -66.0],
            "acq_date": ["2018-05-01"] * 3,
            "acq_datetime": pd.to_datetime(["2018-05-01"] * 3),
            "frp": [100.0, 300.0, 50.0],
        })
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326",
        )

    def test_fichas_frp(self):
        for producto in ("firms_modis_frp", "firms_viirs_jpss1_frp"):
            f = cfg.ficha(producto)
            self.assertEqual(f["columna_valor"], "frp")
            self.assertEqual(f["unidad"], "MW")
            self.assertEqual(f["coloracion"], "continua_valor")
            self.assertEqual((f["vmin"], f["vmax"]), (0, 300))
            self.assertIn("maximo", f["agregaciones"])
            self.assertIn("promedio", f["agregaciones"])
            self.assertGreater(f["res_deg"], 0)

    def test_fuentes_csv_unicas(self):
        self.assertEqual(len(cfg.PRODUCTOS), 5)
        self.assertEqual(len(cfg.fuentes_csv_unicas()), 3)

    def test_parser_agregacion(self):
        parser = cfg.crear_parser()
        args = parser.parse_args([])
        self.assertEqual(args.agregacion, "maximo")
        args = parser.parse_args(["--agregacion", "promedio"])
        self.assertEqual(args.agregacion, "promedio")

    def test_agregacion_maximo_y_promedio(self):
        from fuente.datos import agregar_valor_por_pixel

        f = cfg.ficha("firms_modis_frp")
        gdf = self._gdf_frp()
        # Los dos primeros puntos caen en el mismo pixel MODIS (0.009 deg)
        ag_max = agregar_valor_por_pixel(gdf, f, "maximo")
        self.assertEqual(len(ag_max), 2)
        self.assertAlmostEqual(max(ag_max["frp"]), 300.0)
        ag_mean = agregar_valor_por_pixel(gdf, f, "promedio")
        self.assertEqual(len(ag_mean), 2)
        self.assertAlmostEqual(sorted(ag_mean["frp"])[1], 200.0)

    def test_mapa_frp_sintetico(self):
        import matplotlib
        matplotlib.use("Agg")
        import geopandas as gpd
        import matplotlib.pyplot as plt
        from fuente.mapa import generar_mapa

        f = cfg.ficha("firms_modis_frp")
        meses = cfg.parsear_meses(["2018-05"])
        fig = generar_mapa(
            gdf=self._gdf_frp(),
            world=gpd.GeoDataFrame(),
            meses=meses,
            satelital=False,
            esequibo=False,
            rayas=False,
            res_texto=f["res_texto"],
            total_píxeles=3,
            sensor_nombre=f["nombre"],
            ficha=f,
        )
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_renderer_continuo_devuelve_coleccion(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from fuente.mapa import _plot_valor_continuo

        f = cfg.ficha("firms_modis_frp")
        fig, ax = plt.subplots()
        sc = _plot_valor_continuo(ax, self._gdf_frp(), f)
        self.assertIsNotNone(sc)
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
