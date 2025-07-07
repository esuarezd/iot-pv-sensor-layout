"""
summary.py
Lee todos los JSON de ./results y genera un cuadro y gráfico comparativo.
"""
from pathlib import Path
import json, pandas as pd, matplotlib.pyplot as plt

RESULT_DIR = Path("./results")
rows = []

for jf in RESULT_DIR.glob("cap_*.json"):
    with open(jf, encoding="utf-8") as f:
        d = json.load(f)
    rows.append({
        "cap_jb": d["cap_jb"],
        "cable_m": d["cost_m"],
        "jb_activas": len(d["junction_boxes"]),
        "directos": len(d["directos"])
    })

df = pd.DataFrame(rows).set_index("cap_jb").sort_index()
print("\nResumen cable vs capacidad:\n")
print(df)

plt.plot(df.index, df.cable_m, marker="o")
plt.xlabel("Capacidad (sensores por JB)")
plt.ylabel("Cable total [m]")
plt.title("Cable vs capacidad")
plt.grid(True)
plt.tight_layout()
plt.savefig("results/comparison.png", dpi=150)
plt.show()
