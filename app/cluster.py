# Copyright 2025 Edison Suárez
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

# app/cluster.py
import pandas as pd
import math,numpy as np

# helpers ----
def _dist(ax, ay, bx, by, metric):
    
    if metric == "euclid":
        return np.hypot(ax - bx, ay - by)
    else:
        return abs(ax - bx) + abs(ay - by)

def _vecinos(seed, restantes, sensores, radius, cap, metric):

    vecinos = []
    for idx in restantes:
        if idx == seed:
            continue
        if len(vecinos) >= cap - 1:
            break
        if _dist(sensores.x[seed], sensores.y[seed], sensores.x[idx], sensores.y[idx], metric) <= radius:
            vecinos.append(idx)
    return vecinos

# API publica
def build_cajas(sens: pd.DataFrame,
                cap: int,
                radius: float = 3.0,
                metric: str = "euclid") -> pd.DataFrame:
    """Devuelve DF con id,x,y,n de cada JB."""
    remaining = list(range(len(sens)))
    clusters  = []
    while remaining:
        seed   = remaining[0]
        vecinos = _vecinos(seed, remaining, sens, radius, cap, metric)
        grupo  = [seed] + vecinos
        clusters.append(grupo)
        for idx in grupo:
            remaining.remove(idx)

    rows = []
    for k, grp in enumerate(clusters, 1):
        xy = sens.loc[grp, ["x", "y"]].mean()
        rows.append({"id": f"JB{k:02d}",
                     "x":  xy.x, "y": xy.y,
                     "n":  len(grp)})
    return pd.DataFrame(rows)


def build_sensores_por_caja(sens: pd.DataFrame,
                            cajas: pd.DataFrame,
                            tableros: pd.DataFrame,
                            metric: str = "euclid") -> pd.DataFrame:
    """Asignación sensor → JB  ('' si llega directo)."""
    # distancia sensor ↔ tablero más cercano
    d_tb = tableros.apply(
        lambda tb: _dist(sens.x, sens.y, tb.x, tb.y, metric), axis=1)
    sens["dist_tb"] = d_tb.min(axis=0).values

    memb_rows = []
    for _, s in sens.iterrows():
        if s.l_tt_cable_m >= s.dist_tb:          # llega directo
            memb_rows.append({"sensor_id": s.id, "jb_id": ""})
        else:                                    # busca la caja más próxima
            cajas["d"] = _dist(cajas.x, cajas.y, s.x, s.y, metric)
            jb = cajas.loc[cajas.d.idxmin(), "id"]
            memb_rows.append({"sensor_id": s.id, "jb_id": jb})
    return pd.DataFrame(memb_rows)