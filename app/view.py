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
view.py - Ejecuta una única capacidad:
  python app/view.py -d ./data --cap-jb 4
Si data/cajas_<cap>.csv no existe, lo construye con cluster.build_cajas().
"""

import json, click
import matplotlib.pyplot as plt

from pathlib import Path
from shutil import copyfile 
from app import logic, cluster

@click.command()
@click.option("-d", "--data", default="./data", show_default=True)
@click.option("--cap-jb",  default=6, type=int,   show_default=True)
@click.option("--l-tt-jb", default=3.0, type=float, show_default=True)
@click.option("--l-jb-tb", default=50.0, type=float, show_default=True)
@click.option("--l-tt-tb", default=12.0, type=float, show_default=True)
@click.option("--plot/--no-plot", default=False, help="Mostrar gráfico con sensores, JB y conexiones")
@click.option("-v", "--verbose", is_flag=True)
def main(data, cap_jb, l_tt_jb, l_jb_tb, l_tt_tb, plot, verbose):
    data_path = Path(data)

    # 1  crea data/cajas_<cap>.csv si aún no existe
    cajas_csv = cluster.build_cajas(data_path, cap_jb, radius=l_tt_jb)
    click.echo(f"Usando posiciones de JB en {cajas_csv.name}")
    
    # 2  asegura que logic.solve vea exactamente ese archivo
    canonical = data_path / "cajas.csv"
    copyfile(cajas_csv, canonical)      # sobrescribe si ya existía
    click.echo(f"Usando {cajas_csv.name} → {canonical.name}")

    # 3  resuelve el MILP
    cfg = logic.Settings(cap_jb=cap_jb, l_tt_jb=l_tt_jb,
                         l_jb_tb=l_jb_tb, l_tt_tb=l_tt_tb,
                         solver_msg=verbose)
    res = logic.solve(data_path, cfg)

    # 4  si no hay solución factible → mensaje y salir
    if "vars" not in res:
        click.secho(f"\n✖  No existe solución factible con cap_jb = {cap_jb}", fg="red")
        return

    # 5  desempaquetar variables de decisión
    x, y, d, k = (res["vars"][v] for v in ("x", "y", "d", "k"))
    tb = res["tablero"]

    # ── impresión amigable ───────────────────────────────────────────────
    click.secho(f"\n►  Tablero elegido: {tb['id']}  @ ({tb['x']:.2f}, {tb['y']:.2f})", fg="yellow")
    click.echo(f"   Longitud total de cable = {res['cost']:.2f} m\n")

    click.echo("Junction boxes activadas:")
    for jb, var in y.items():
        if var.value():
            sensores = [i for (i, jj), xv in x.items() if jj == jb and xv.value()]
            click.echo(f"  • {jb}: {len(sensores)} sensores, {int(k[jb].value())} cable(s) → {sensores}")

    directos = [i for i, dv in d.items() if dv.value()]
    click.echo("\nSensores directos al tablero:")
    click.echo(f"   {directos}\n")

    # ── guardado JSON ────────────────────────────────────────────────────
    Path("results").mkdir(exist_ok=True)
    safe = {
        "cap_jb": cap_jb,
        "cost_m": res["cost"],
        "tablero": tb,
        "junction_boxes": {
            jb: {"sensores": [i for (i, jj), xv in x.items() if jj == jb and xv.value()],
                 "cables": int(k[jb].value())}
            for jb, var in y.items() if var.value()
        },
        "directos": directos
    }
    with open(f"results/cap_{cap_jb}.json", "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)
    
    # --- visualizacion -----------
    if plot:
        draw_layout(res, data_path / f"cajas_{cap_jb}.csv")


def draw_layout(res, cajas_csv):
    import pandas as pd
    sens = pd.read_csv("data/sensores.csv")
    cajas = pd.read_csv(cajas_csv)
    tb    = res["tablero"]

    x, y, d = res["vars"]["x"], res["vars"]["y"], res["vars"]["d"]

    fig, ax = plt.subplots()
    # sensores
    ax.scatter(sens.x, sens.y, c="tab:blue", marker="o", label="Sensores")
    # JB activas
    act = cajas[cajas.id.isin([j for j,v in y.items() if v.value()])]
    ax.scatter(act.x, act.y, c="tab:orange", marker="s", label="JB activas")
    # Tablero
    ax.scatter([tb["x"]], [tb["y"]], c="tab:red", marker="*", s=200, label="Tablero")

    # Conexiones TT→JB
    for (i, j), var in x.items():
        if var.value():
            si = sens.loc[sens.id == i].iloc[0]
            sj = act.loc[act.id == j].iloc[0]
            ax.plot([si.x, sj.x], [si.y, sj.y], lw=0.5, c="gray")
    # Conexiones JB→Tablero
    for j, v in y.items():
        if v.value():
            sj = act.loc[act.id == j].iloc[0]
            ax.plot([sj.x, tb["x"]], [sj.y, tb["y"]], lw=1.0, c="black")

    ax.set_aspect("equal")
    ax.set_title(f"Layout  -  cap_jb = {res['settings'].cap_jb}\nCable total = {res['cost']:.2f} m")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(f"results/layout_cap_{res['settings'].cap_jb}.png", dpi=150)
    plt.show()
    
if __name__ == "__main__":
    main()
