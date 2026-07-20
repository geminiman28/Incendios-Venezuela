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
        self.assertTrue((cfg.RAIZ / "datos").exists())
        self.assertTrue((cfg.RAIZ / "fuente").exists())

    def test_sensores_validos(self):
        self.assertIn("VIIRS (JPSS1)", cfg.SENSORES_VALIDOS)
        self.assertIn("VIIRS (SNPP)", cfg.SENSORES_VALIDOS)
        self.assertIn("MODIS (Aqua + Terra)", cfg.SENSORES_VALIDOS)

    def test_parser_defaults(self):
        parser = cfg.crear_parser()
        args = parser.parse_args([])
        self.assertEqual(args.sensor, "VIIRS (JPSS1)")
        self.assertTrue(args.satelital)
        self.assertTrue(args.esequibo)
        self.assertFalse(args.rayas)

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


class TestDatos(unittest.TestCase):
    """Tests de carga de datos."""

    def test_rutas_csv(self):
        meses = pd.date_range("2018-05-01", "2018-08-01", freq="MS")
        rutas = cfg._rutas_csv(meses)
        self.assertIn("VIIRS (JPSS1)", rutas)
        self.assertIn("MODIS (Aqua + Terra)", rutas)
        self.assertIsInstance(rutas["VIIRS (JPSS1)"]["ven"][0], Path)

    def test_cargar_csv_viirs_jpss1_2018(self):
        """Carga real de datos VIIRS JPSS1 2018."""
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, guy = leer_csv("VIIRS (JPSS1)", meses)
        # Al menos uno debe tener datos
        self.assertFalse(
            ven.empty and guy.empty,
            "No se cargaron datos de ninguna zona"
        )


    def test_filtrar_por_meses(self):
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, _ = leer_csv("VIIRS (JPSS1)", meses)
        if not ven.empty:
            filtrado = filtrar_por_meses(ven, meses)
            self.assertIsInstance(filtrado, pd.DataFrame)

    def test_a_geo(self):
        meses = pd.date_range("2018-05-01", "2018-07-01", freq="MS")
        ven, _ = leer_csv("VIIRS (JPSS1)", meses)
        if not ven.empty:
            gdf = a_geo(ven)
            self.assertTrue(hasattr(gdf, "geometry"))
            self.assertEqual(gdf.crs.to_string(), "EPSG:4326")


if __name__ == "__main__":
    unittest.main()
