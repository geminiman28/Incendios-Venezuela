"""Lanzador legacy para Spyder/F5.

Mantiene el caso histórico de run.py: mapa político, Esequibo como
unidad, meses 2018-05/2018-06 y salida mapa_politico_spyder.png.

Para el flujo configurable por defaults/.env usar:
    python -m fuente.ejecutar_spyder
"""

import sys

from fuente.principal import main

ARGS_SPYDER_LEGACY = [
    "--no-satelital",
    "--esequibo",
    "--no-rayas",
    "--meses", "2018-05", "2018-06",
    "--guardar", "mapa_politico_spyder.png",
]

if __name__ == "__main__":
    sys.argv = ["run.py", *ARGS_SPYDER_LEGACY]
    main()
