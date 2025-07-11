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
from pathlib import Path
from shutil import copyfile
from app import logic, cluster

import matplotlib.pyplot as plt

@click.command()
@click.option("-d", "--data", default="./data", show_default=True)
@click.option("--cap-jb",  default=6, type=int,   show_default=True)
@click.option("--l-tt-jb", default=3.0, type=float, show_default=True)
@click.option("--l-jb-tb", default=50.0, type=float, show_default=True)
@click.option("--l-tt-tb", default=12.0, type=float, show_default=True)
@click.option("--plot/--no-plot", default=False, show_default=True)
@click.option("-v", "--verbose", is_flag=True)
def main(data, cap_jb, l_tt_jb, l_jb_tb, l_tt_tb, plot, verbose):
    data_path = Path(data)

    # 1) construir o reutilizar cajas_<cap>.csv
    cajas_csv = cluster.build_cajas(data_path, cap_jb, radius=l_tt_jb)
    copyfile(cajas_csv, data_path / "cajas.csv")
    click.echo(f"Usando {cajas_csv.name}")

    # 2) resolver MILP
    cfg = logic.Settings(cap_jb=cap_jb, l_tt_jb=l_tt_jb,
                         l_jb_tb=l_jb_tb, l_tt_tb=l_tt_tb,
                         solver_msg=verbose)
    res = logic.solve(data_path, cfg)

    if "vars" not in res:
        click.secho(f"\n✖  No existe solución factible con cap_jb = {cap_jb}", fg="red")
        return

    # 3) desempaquetar
    x, y, d, k = (res["vars"][v] for v in ("x", "y", "d", "k"))
    len_jb_tb  = res["vars"]["len"]["jb_tb"]
    tb = res["tablero"]

    # ── impresión básica ─────────────────────────────────────────────
    click.secho(f"\n►  Tablero elegido: {tb['id']}  @ ({tb['x']:.2f}, {tb['y']:.2f})", fg="yellow")
    click.echo(f"   Longitud total de cable = {res['cost']:.2f} m\n")

    click.echo("Junction boxes activadas:")
    for jb, var in y.items():
        if var.value():
            sensores = [i for (i, jj), xv in x.items() if jj == jb and xv.value()]
            click.echo(f"  • {jb}: {len(sensores)} sensores, {int(k[jb].value())} cable(s) → {sensores}")

    directos = [i for i, dv in d.items() if dv.value()]
    click.echo("\nSensores directos al tablero:")
    click.echo(f"   {directos}")

    # ── lista de cortes JB→Tablero ───────────────────────────────────
    click.echo("\nLista de cortes (multipar):")
    total_m = 0.0
    for jb, var in y.items():
        if var.value():
            L = len_jb_tb[jb]
            nc = int(k[jb].value())
            tramo = L * nc
            total_m += tramo
            click.echo(f"  • {jb}: {nc} × {L:.2f} m  =  {tramo:.2f} m")
    res["total_m"] = total_m
    click.echo(f"  Total multipar: {total_m:.2f} m\n")

    # ── guardar JSON ────────────────────────────────────────────────
    Path("results").mkdir(exist_ok=True)
    safe = {
        "cap_jb": cap_jb,
        "cost_m": res["cost"],
        "tablero": tb,
        "total_m": total_m,
        "junction_boxes": {
            jb: {"sensores": [i for (i, jj), xv in x.items() if jj == jb and xv.value()],
                 "cables": int(k[jb].value()),
                 "metros": len_jb_tb[jb] * int(k[jb].value())}
            for jb, var in y.items() if var.value()
        },
        "directos": directos
    }
    with open(f"results/cap_{cap_jb}.json", "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)

    # ── gráfico opcional ────────────────────────────────────────────
    if plot:
        draw_layout(res, cajas_csv)

def draw_layout(res, cajas_csv):
    import pandas as pd
    sens = pd.read_csv("data/sensores.csv")
    cajas = pd.read_csv(cajas_csv)
    tb = res["tablero"]
    x, y, d, k = (res["vars"][v] for v in ("x", "y", "d", "k"))

    fig, ax = plt.subplots()
    ax.scatter(sens.x, sens.y, c="tab:blue", marker="o", label="Sensores")
    act = cajas[cajas.id.isin([j for j,v in y.items() if v.value()])]
    ax.scatter(act.x, act.y, c="tab:orange", marker="s", label="JB activas")
    ax.scatter(tb["x"], tb["y"], c="tab:red", marker="*", s=200, label="Tablero")

    for (i,j), xv in x.items():
        if xv.value():
            si = sens.loc[sens.id==i].iloc[0]
            sj = act.loc[act.id==j].iloc[0]
            ax.plot([si.x, sj.x], [si.y, sj.y], lw=0.5, c="gray")

    for jb, var in y.items():
        if var.value():
            sj = act.loc[act.id==jb].iloc[0]
            ax.plot([sj.x, tb["x"]], [sj.y, tb["y"]], lw=1.0, c="black")

    ax.set_aspect("equal")
    ax.set_title(f"Layout  –  cap_jb = {res['settings'].cap_jb}\nTotal multipar = {res['total_m']:.2f} m")
    ax.legend(loc="center left", bbox_to_anchor=(1.03, 0.5))
    plt.tight_layout()
    plt.savefig(f"results/layout_cap_{res['settings'].cap_jb}.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    main()
