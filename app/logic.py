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
logic.py
MILP para ubicar junction-boxes (JB) y un tablero (TB) en un arreglo FV.
• Sensores 'normal'  : TT→JB (≤ l_tt_jb)  +  JB→TB
• Sensores 'directo' : TT→TB  (≤ l_tt_tb)
• Nº de cables PUR 4x0.34 mm² por JB  =  ceil((sensores_en_JB + 2) / 4)
  linealizado:   4·k_j - s_j  ∈  [3, 6]
Función objetivo = longitud total de cable JB→TB · k_j  +  TT→JB  +  directos
Requiere:  pip install pulp pandas
"""

from dataclasses import dataclass
from pathlib import Path
import math, pandas as pd
import pulp as pl


# ───────────────────────── Configuración ───────────────────────────────
@dataclass
class Settings:
    cap_jb: int = 6          # sensores máx. por JB
    l_tt_jb: float = 3.0     # límite TT→JB  (m)
    l_jb_tb: float = 50.0    # límite JB→TB  (m)  (1e6 = sin límite)
    l_tt_tb: float = 12.0    # límite TT→TB para 'directo' (m)
    solver_msg: bool = False # True → muestra traza CBC


def _dist(a, b) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


# ─────────────────────── API principal solve() ─────────────────────────
def solve(data_dir: str | Path, cfg: Settings = Settings()) -> dict:
    data_dir = Path(data_dir)

    sens  = pd.read_csv(data_dir / "sensores.csv")            # id,x,y,tipo
    cajas = (pd.read_csv(data_dir / "cajas.csv")
             if (data_dir / "cajas.csv").exists()
             else sens[["id", "x", "y"]].assign(id=lambda d: "JB_" + d.id))
    tbs   = pd.read_csv(data_dir / "tableros.csv")            # id,x,y

    best = {"cost": float("inf")}
    for _, tb in tbs.iterrows():
        m, var = _build_model(sens, cajas, tb, cfg)
        m.solve(pl.PULP_CBC_CMD(msg=cfg.solver_msg))
        if m.status == 1 and pl.value(m.objective) < best["cost"]:
            best = {"cost":      pl.value(m.objective),
                    "tablero":   tb.to_dict(),
                    "vars":      var,
                    "settings":  cfg}
    return best


# ─────────────────── Constructor del MILP interno ──────────────────────
def _build_model(sens, cajas, tb, s):
    norm   = sens.tipo.str.lower().str.strip() == "normal"
    direct = sens.tipo.str.lower().str.strip() == "directo"

    d_tt_jb = {(i.id, j.id): _dist(i, j)
               for _, i in sens[norm].iterrows()
               for _, j in cajas.iterrows()
               if _dist(i, j) <= s.l_tt_jb}

    d_jb_tb = {j.id: _dist(j, tb)
               for _, j in cajas.iterrows()
               if _dist(j, tb) <= s.l_jb_tb}

    d_tt_tb = {i.id: _dist(i, tb)
               for _, i in sens[direct].iterrows()
               if _dist(i, tb) <= s.l_tt_tb}

    m = pl.LpProblem(f"PV_{tb.id}", pl.LpMinimize)
    x = pl.LpVariable.dicts("x", d_tt_jb.keys(), 0, 1, pl.LpBinary)   # TT→JB
    y = pl.LpVariable.dicts("y", d_jb_tb.keys(), 0, 1, pl.LpBinary)   # JB activa
    d = pl.LpVariable.dicts("d", d_tt_tb.keys(), 0, 1, pl.LpBinary)   # directo
    k = pl.LpVariable.dicts("k", d_jb_tb.keys(), lowBound=0, cat="Integer")

    s_j = {j: pl.lpSum(x[(i, j)] for i in sens.id if (i, j) in x) for j in cajas.id}

    # 1) asignación única
    for _, i in sens.iterrows():
        m += pl.lpSum(x[(i.id, j)] for j in cajas.id if (i.id, j) in x) == 1 - d.get(i.id, 0)

    # 2) capacidad JB
    for j in cajas.id:
        if j in y:
            m += s_j[j] <= s.cap_jb * y[j]

    # 3) enlace x ≤ y
    for (i, j) in x:
        if j in y:
            m += x[(i, j)] <= y[j]

    # 4) nº cables PUR: 4·k - s ∈ [3,6]
    M = math.ceil((s.cap_jb + 2) / 4)   # 2 si cap_jb ≤ 6
    for j in s_j:
        m += 4 * k[j] - s_j[j] >= 2 * y[j]   # solo obliga si la caja está activa
        m += k[j] <= M * y[j]                # k = 0 cuando y = 0

    # 5) Objetivo
    m += (
        pl.lpSum(d_tt_jb[idx] * x[idx] for idx in x) +      # TT→JB  (no cuesta si superpuestos)
        pl.lpSum(d_jb_tb[j]   * k[j]  for j in k) +         # JB→TB  por cada cable
        pl.lpSum(d_tt_tb[i]   * d[i]  for i in d)           # directos
    )

    return m, {"x": x, "y": y, "d": d, "k": k}
