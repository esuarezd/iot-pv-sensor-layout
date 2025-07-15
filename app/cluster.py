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
from app import logic

def build_cajas(sens: pd.DataFrame,
                cap: int,
                radius: float,
                metric: str):
    """Devuelve (cajas_df, memb_df) respetando cap y radio."""
    # 1) sensores candidatos (los que NO llegan directo al TB)
    cand = sens[~sens["directo"]].copy()

    # 2) greedy-centroid clustering
    remaining = cand.index.tolist()
    cajas_rows, memb_rows = [], []
    while remaining:
        seed = remaining[0]
        # centro provisional = coordenadas del seed
        sx, sy = cand.loc[seed, ["x", "y"]]
        d = logic.dist(cand.x[remaining], cand.y[remaining], sx, sy, metric)
        dentro = [remaining[i] for i,v in enumerate(d<=radius) if v][:cap]
        # centroide final
        xy = cand.loc[dentro, ["x","y"]].mean()
        jb_id = f"JB{len(cajas_rows)+1:02d}"
        cajas_rows.append({"id": jb_id, "x":xy.x, "y":xy.y, "n":len(dentro)})
        memb_rows += [{"sensor_id": cand.id[i], "jb_id": jb_id}
                      for i in dentro]
        for idx in dentro: remaining.remove(idx)

    # 3) sensores directos
    directos = sens[sens["directo"]].id
    memb_rows += [{"sensor_id": sid, "jb_id":""} for sid in directos]

    return (pd.DataFrame(cajas_rows),
            pd.DataFrame(memb_rows))

