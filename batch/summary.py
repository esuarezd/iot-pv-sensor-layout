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
summary.py
Lee los JSON generados por sweep_caps.py y produce:
  • Tabla resumen en consola
  • Gráfica cable vs capacidad  (results/comparison.png)
Requiere: pip install matplotlib pandas
"""
from pathlib import Path
import json, pandas as pd, matplotlib.pyplot as plt

RES_DIR = Path("./results")
rows = []
for jf in RES_DIR.glob("cap_*.json"):
    with open(jf, encoding="utf-8") as f:
        d = json.load(f)
    rows.append({"cap_jb": d["cap_jb"],
                 "cable_m": d["total_m"],
                 "jb_activas": len(d["junction_boxes"]),
                 "directos": len(d["directos"])})
df = pd.DataFrame(rows).set_index("cap_jb").sort_index()
print("\nTabla resumen (m de cable):\n")
print(df)

plt.plot(df.index, df.cable_m, marker="o")
plt.grid(True)
plt.xlabel("Capacidad (sensores por JB)")
plt.ylabel("Cable total [m]")
plt.title("Cable total vs capacidad")
plt.tight_layout()
plt.savefig(RES_DIR / "comparison.png", dpi=150)
plt.show()
