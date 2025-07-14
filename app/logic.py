# app/view.py
import pandas as pd
import math
import numpy as np
from pathlib import Path

def _rule_cables(n):      # ceil((n+2)/4)
    return math.ceil((n + 2) / 4)

def _dist(ax, ay, bx, by, metric):
    if metric == "euclid":
        # return math.hypot(ax - bx, ay - by) # esuarez: TypeError: cannot convert the series to <class 'float'>
        return np.hypot(ax - bx, ay - by) # vectorizado
    else: # manhattan
        return abs(ax - bx) + abs(ay - by)
    
def multipar(data_dir: Path, cajas_csv: Path, metric="euclid") -> dict:
    cajas = pd.read_csv(cajas_csv)              # id,x,y,n
    tbs   = pd.read_csv(data_dir / "tableros.csv")

    best = None
    for _, tb in tbs.iterrows():
        d = _dist(cajas.x, cajas.y, tb.x, tb.y, metric)
        k = cajas.n.apply(_rule_cables)
        metros = (d * k).sum()
        if best is None or metros < best["metros"]:
            best = {"tablero": tb.to_dict(),
                    "metros":  float(metros),
                    "dists":   d.tolist(),
                    "cables":  k.tolist()}
    return best