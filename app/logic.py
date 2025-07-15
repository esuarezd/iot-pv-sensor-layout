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

# app/logic.py
import math
import numpy as np
import pandas as pd

def _rule_cables(n):      # ceil((n+2)/4)
    return math.ceil((n + 2) / 4)

def dist(ax, ay, bx, by, metric):
    if metric == "euclid":
        # return math.hypot(ax - bx, ay - by) 
        # esuarez: TypeError: cannot convert the series to <class 'float'>
        return np.hypot(ax - bx, ay - by) # vectorizado
    else: # manhattan
        return abs(ax - bx) + abs(ay - by)
    
def tablero_centroide(sens: pd.DataFrame) -> dict:
    return {"id": "TB_AUTO",
            "x":  sens.x.mean(),
            "y":  sens.y.mean()}

def coste_directo(sens, tb, metric):
    return dist(sens.x, sens.y, tb["x"], tb["y"], metric).sum()

def coste_jb(cajas, tb, metric):
    d = dist(cajas.x, cajas.y, tb["x"], tb["y"], metric)
    k = cajas.n.apply(_rule_cables)
    return float((d*k).sum()), d.tolist(), k.tolist()