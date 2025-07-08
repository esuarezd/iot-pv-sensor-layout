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
""" app/cluster.py 
A partir de los sensores, crear cluster de sensores y los agrupa en jb
"""
import pandas as pd, numpy as np, math
from pathlib import Path

def build_cajas(data_dir: Path, cap: int, radius: float = 3.0) -> Path:
    """Genera data/cajas_<cap>.csv si no existe y devuelve su ruta."""
    out_csv = data_dir / f"cajas_{cap}.csv"
    if out_csv.exists():
        return out_csv                          # ya hecho

    sens = pd.read_csv(data_dir / "sensores.csv")
    coords = sens[["x", "y"]].values
    remaining = list(range(len(sens)))
    clusters = []

    while remaining:
        seed = remaining[0]
        dist = np.sqrt(((coords[remaining] - coords[seed])**2).sum(axis=1))
        cand = [remaining[i] for i,d in enumerate(dist) if d <= radius and remaining[i]!=seed][:cap-1]
        group = [seed] + cand
        clusters.append(group)
        for idx in group:
            remaining.remove(idx)

    rows = []
    for k, g in enumerate(clusters, 1):
        xy = coords[g].mean(axis=0)
        rows.append({"id": f"JB{k:02d}", "x": xy[0], "y": xy[1]})
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    return out_csv
