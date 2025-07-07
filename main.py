# Copyright 2025 Edison Suárez Ducón
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
main.py
Ejecuta el solver para cap_jb = 2 … 18 y guarda un JSON por capacidad.
"""
from pathlib import Path
import json
from app import logic

DATA_DIR   = Path("./data")
RESULT_DIR = Path("./results")
RESULT_DIR.mkdir(exist_ok=True)

CAP_MIN, CAP_MAX = 2, 18
LIM_JB_TB = 50.0     # o 1e6 para “sin límite”

for cap in range(CAP_MIN, CAP_MAX + 1):
    cfg = logic.Settings(cap_jb=cap, l_jb_tb=LIM_JB_TB)
    res = logic.solve(DATA_DIR, cfg)

    safe = {
        "cap_jb": cap,
        "cost_m": res["cost"],
        "tablero": res["tablero"],
        "junction_boxes": {
            jb: [i for (i, jj), xv in res["vars"]["x"].items()
                 if jj == jb and xv.value()]
            for jb, v in res["vars"]["y"].items() if v.value()
        },
        "directos": [i for i, dv in res["vars"]["d"].items() if dv.value()]
    }
    with open(RESULT_DIR / f"cap_{cap}.json", "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)

    print(f"cap {cap:2d} → cable={safe['cost_m']:.2f} m,  "
          f"JB={len(safe['junction_boxes'])}")
