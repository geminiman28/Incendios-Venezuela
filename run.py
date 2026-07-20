#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher para Spyder — Ejecutar con F5."""

import sys
from fuente.principal import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv = [sys.argv[0], "--meses", "2018-05", "2018-06"]
    main()
