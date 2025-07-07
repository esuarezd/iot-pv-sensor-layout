# iot-pv-sensor-layout
Mixed-Integer Linear Programming (MILP) model to place junction boxes and a central panel board for PV module temperature sensors.

# activar entorno virtual
source .venv/bin/activate

# 1) correr batch completo
python main.py

# 2) ver la curva comparativa
python summary.py

# 3) para una sola capacidad “ad hoc”
python app/view.py -d ./data --cap-jb 4 --l-jb-tb 100
