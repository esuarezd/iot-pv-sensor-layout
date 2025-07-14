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

# app/cluster.py
import pandas as pd
import math
from pathlib import Path

def _dist(ax, ay, bx, by, metric):
    if metric == "euclid":
        return math.hypot(ax - bx, ay - by)
    else:
        return abs(ax - bx) + abs(ay - by)

def _vecinos(seed, restantes, sens, radius, cap, metric):
    """Devuelve índices globales dentro del radio, hasta cap–1 vecinos."""
    vecinos = []
    for idx in restantes:
        if idx == seed:
            continue
        if len(vecinos) >= cap - 1:
            break
        if _dist(sens.x[seed], sens.y[seed], sens.x[idx], sens.y[idx], metric) <= radius:
            vecinos.append(idx)
    return vecinos

def build_cajas(data_dir: Path, cap: int, radius: float = 3.0, metric: str = "euclid"):
    """
    Genera data/cajas_<cap>.csv  y  data/sensores_jb_<cap>.csv
    Devuelve las dos rutas.
    """
    cajas_csv = data_dir / f"cajas_{cap}.csv"
    memb_csv  = data_dir / f"sensores_jb_{cap}.csv"

    # siempre regenerar: evita incoherencias si cambian sensores.csv
    for p in (cajas_csv, memb_csv):
        p.unlink(missing_ok=True)

    sens = pd.read_csv(data_dir / "sensores.csv")      # id,x,y,l_tt_cable_m
    tbs  = pd.read_csv(data_dir / "tableros.csv")      # id,x,y

    # --- sensores que llegan directos al tablero --------------------------
    directos, clust_indices = [], []
    for idx, s in sens.iterrows():
        dmin = ((_dist(s.x, s.y, tb.x, tb.y, metric) for _, tb in tbs.iterrows()))
        if s.l_tt_cable_m >= min(dmin):
            directos.append(idx)
        else:
            clust_indices.append(idx)

    # --- clustering de los restantes -------------------------------------
    remaining = clust_indices.copy()
    clusters  = []
    while remaining:
        seed = remaining[0]
        cand = _vecinos(seed, remaining, sens, radius, cap, metric)
        grupo = [seed] + cand
        clusters.append(grupo)
        for idx in grupo:
            remaining.remove(idx)

    # --- construir CSVs ---------------------------------------------------
    cajas_rows, memb_rows = [], []
    for k, grp in enumerate(clusters, 1):
        xy = sens.loc[grp, ["x", "y"]].mean()
        cajas_rows.append({"id": f"JB{k:02d}", "x": xy.x, "y": xy.y, "n": len(grp)})
        for idx in grp:
            memb_rows.append({"sensor_id": sens.id[idx], "jb_id": f"JB{k:02d}"})

    for idx in directos:
        memb_rows.append({"sensor_id": sens.id[idx], "jb_id": ""})

    pd.DataFrame(cajas_rows).to_csv(cajas_csv, index=False)
    pd.DataFrame(memb_rows).to_csv(memb_csv,  index=False)
    print(f"Generadas {len(cajas_rows)} JB en '{cajas_csv.name}' "
          f"(directos: {len(directos)})")
    return cajas_csv, memb_csv