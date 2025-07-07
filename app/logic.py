"""
logic.py
Core MILP solver for optimal placement of junction-boxes (JB)
and selection of a single panel board (TB) in a PV array.

Requisitos:
    pip install pulp pandas
"""

from dataclasses import dataclass
from pathlib import Path
import math, pandas as pd
import pulp as pl


# ---------- Config -----------------------------------------------------------
@dataclass
class Settings:
    cap_jb: int = 6          # Máx. sensores por JB
    l_tt_jb: float = 3.0     # Límite (m) cable TT → JB
    l_jb_tb: float = 50.0    # Límite (m) cable JB → TB (>>> pon 1e6 si quieres “ilimitado”)
    l_tt_tb: float = 12.0    # Límite (m) sensor 'directo' TT → TB
    solver_msg: bool = False # True para ver la traza del solver


# ---------- Funciones utilitarias -------------------------------------------
def _dist(a, b) -> float:
    """Distancia Euclídea 2-D."""
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


# ---------- Función principal -----------------------------------------------
def solve(data_dir: str | Path, cfg: Settings = Settings()) -> dict:
    """Resuelve el MILP para cada tablero candidato y devuelve la mejor solución."""
    data_dir = Path(data_dir)

    # --- Datos ---------------------------------------------------------------
    sens = pd.read_csv(data_dir / "sensores.csv")           # id,x,y,tipo

    if (data_dir / "cajas.csv").exists():
        cajas = pd.read_csv(data_dir / "cajas.csv")         # id,x,y
    else:  # fallback: cada sensor es candidato de JB
        cajas = sens[["id", "x", "y"]].copy()
        cajas["id"] = "JB_" + cajas["id"]

    tbs = pd.read_csv(data_dir / "tableros.csv")            # id,x,y

    best = {"cost": float("inf")}

    # --- Itera por cada tablero candidato -----------------------------------
    for _, tb in tbs.iterrows():
        model, var = _build_model(sens, cajas, tb, cfg)

        model.solve(pl.PULP_CBC_CMD(msg=cfg.solver_msg))

        if model.status == 1 and pl.value(model.objective) < best["cost"]:
            best = {
                "cost": pl.value(model.objective),
                "tablero": tb.to_dict(),
                "vars": var,
                "settings": cfg,
            }
    return best


# ---------- Constructor del MILP --------------------------------------------
def _build_model(sens: pd.DataFrame, cajas: pd.DataFrame, tb: pd.Series,
                 s: Settings):

    # Máscaras de tipo
    norm_mask = sens.tipo.str.lower().str.strip() == "normal"
    dir_mask  = sens.tipo.str.lower().str.strip() == "directo"

    # Distancias y filtros
    d_tt_jb = {
        (i.id, j.id): _dist(i, j)
        for _, i in sens[norm_mask | dir_mask].iterrows()
        for _, j in cajas.iterrows()
        if _dist(i, j) <= s.l_tt_jb
    }

    d_jb_tb = {
        j.id: _dist(j, tb)
        for _, j in cajas.iterrows()
        if _dist(j, tb) <= s.l_jb_tb
    }

    d_tt_tb = {
        i.id: _dist(i, tb)
        for _, i in sens[dir_mask].iterrows()
        if _dist(i, tb) <= s.l_tt_tb
    }

    # --- Variables ----------------------------------------------------------
    m = pl.LpProblem(f"PV_{tb.id}", pl.LpMinimize)
    x = pl.LpVariable.dicts("x", d_tt_jb.keys(), 0, 1, pl.LpBinary)  # sensor→JB
    y = pl.LpVariable.dicts("y", d_jb_tb.keys(), 0, 1, pl.LpBinary)  # JB activa
    d = pl.LpVariable.dicts("d", d_tt_tb.keys(), 0, 1, pl.LpBinary)  # sensor directo

    # --- Objetivo -----------------------------------------------------------
    m += (
        pl.lpSum(d_tt_jb[k] * x[k] for k in x) +
        pl.lpSum(d_jb_tb[j] * y[j] for j in y) +
        pl.lpSum(d_tt_tb[i] * d[i] for i in d)
    )

    # --- Restricciones ------------------------------------------------------
    # 1) sensor normal o directo: exactamente 1 ruta
    for _, i in sens.iterrows():
        lhs = pl.lpSum(x[(i.id, j)] for j in cajas.id if (i.id, j) in x)
        rhs = 1 - d.get(i.id, 0)   # d_i existe solo si puede ir directo
        m += lhs == rhs

    # 2) Capacidad de JB
    for j in cajas.id:
        if j in y:
            m += pl.lpSum(x[(i, j)] for i in sens.id if (i, j) in x) <= s.cap_jb * y[j]

    # 3) Enlace: no se puede usar una JB que no esté activa
    for (i, j) in x:
        if j in y:
            m += x[(i, j)] <= y[j]

    return m, {"x": x, "y": y, "d": d}
