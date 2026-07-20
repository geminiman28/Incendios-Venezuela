"""Ejecutar en Spyder: edita CONFIGURACION en configuracion.py y presiona F5."""

import sys
from pathlib import Path
from datetime import datetime

# Importar configuracion editable desde configuracion.py
from fuente import configuracion as cfg

# Construir argv con el formato unificado de configuracion.py
sys.argv = ["principal.py"]

if cfg.MODO_POLITICO:
    sys.argv.append("--no-satelital")
else:
    sys.argv.append("--satelital")

if cfg.MOSTRAR_ESEQUIBO:
    sys.argv.append("--esequibo")
else:
    sys.argv.append("--no-esequibo")

if cfg.MOSTRAR_RAYAS:
    sys.argv.append("--rayas")

sys.argv.extend(["--sensor", cfg.SENSOR_DEFAULT])
sys.argv.extend(["--meses"] + cfg.MESES_DEFAULT)
sys.argv.extend(["--dpi", str(cfg.DPI_DEFAULT)])

if cfg.GUARDAR_DEFAULT:
    sys.argv.extend(["--guardar", cfg.GUARDAR_DEFAULT])
else:
    # Generar nombre automatico
    modo = "politico" if cfg.MODO_POLITICO else "satelital"
    eseq = "_esequibo" if cfg.MOSTRAR_ESEQUIBO else ""
    ray = "_rayas" if cfg.MOSTRAR_RAYAS else ""
    meses_str = "-".join(m.replace("-", "") for m in cfg.MESES_DEFAULT)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sensor_cod = cfg.SENSOR_DEFAULT.replace(" ", "_").replace("(", "").replace(")", "")
    nombre = f"{modo}{eseq}{ray}_{sensor_cod}_{cfg.MESES_DEFAULT[0][:4]}_meses{meses_str}_{timestamp}.png"
    ruta_auto = str(cfg.MAPAS_GENERADOS / nombre)
    sys.argv.extend(["--guardar", ruta_auto])

print(f"⚙️  Ejecutando: {' '.join(sys.argv[1:])}")

# Ejecutar principal.py directamente
import runpy
runpy.run_module("fuente.principal", run_name="__main__")
