# iot-pv-sensor-layout
Mixed-Integer Linear Programming (MILP) model to place junction boxes and a central panel board for PV module temperature sensors.

Author: Edison Suarez. 
markdown ## License Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

pv-jb-milp/
│
├─ app/
│   ├─ logic.py      ← Modelo MILP
│   └─ view.py       ← Vista CLI (1 capacidad)
│
├─ sweep_caps.py ← Barrido cap_jb = 1…18
├─ summary.py    ← Tabla + gráfica
│
└─ data/   (CSV)   └─ results/  (salidas JSON & PNG)

Enable virtual environment
source .venv/bin/activate

Run the batch
python batch/sweep_caps.py      # consigue cap_* .json

Check Comparative curve
python batch/summary.py         # compara resultados

For an specific capacity: 
python app/view.py -d ./data --cap-jb 4 --l-jb-tb 100


