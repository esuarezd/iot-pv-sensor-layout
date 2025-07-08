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
sweep_caps.py
Recorre cap_jb = 2…18, llama logic.solve() y guarda un JSON por capacidad.
"""
from pathlib import Path
import json
from app import logic   # importar vía package

DATA_DIR   = Path("./data")
RESULT_DIR = Path("./results")
RESULT_DIR.mkdir(exist_ok=True)

for cap in range(1, 19):
    cfg = logic.Settings(cap_jb=cap, l_jb_tb=50.0)
    res = logic.solve(DATA_DIR, cfg)

    out = {
        "cap_jb": cap,
        "cost_m": res["cost"],
        "tablero": res["tablero"],
        "junction_boxes": {
            jb: {"sensores": [i for (i, jj), xv in res["vars"]["x"].items()
                              if jj == jb and xv.value()],
                 "cables": int(res["vars"]["k"][jb].value())}
            for jb, var in res["vars"]["y"].items() if var.value()
        },
        "directos": [i for i, dv in res["vars"]["d"].items() if dv.value()]
    }
    with open(RESULT_DIR / f"cap_{cap}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"cap {cap:2d} → cable={out['cost_m']:.2f} m,  JB={len(out['junction_boxes'])}")
