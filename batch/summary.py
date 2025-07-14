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

RES = Path("./results")
rows = []
for jf in RES.glob("cap_*.json"):
    with open(jf) as f:
        d = json.load(f)
    rows.append({"cap": d["cap_jb"],
                 "multi": d["multipar_m"],
                 "jb": len(d["junction_boxes"]),
                 "directos": len(d["directos"])})
df = pd.DataFrame(rows).set_index("cap").sort_index()
print("\nTabla resumen multipar [m]:\n"); print(df)

plt.plot(df.index, df.multi, marker="o")
plt.grid(True); plt.xlabel("Capacidad (sensores/JB)")
plt.ylabel("Multipar [m]")
plt.title("Metros de multipar vs capacidad")
plt.tight_layout()
RES.mkdir(exist_ok=True)
plt.savefig(RES / "comparison.png", dpi=150)
plt.show()
