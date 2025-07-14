# app/view.py
"""
Vista CLI - flujo sin MILP
· build_cajas ➜ cajas_<cap>.csv + sensores_jb_<cap>.csv
· multipar    ➜ metros JB→TB + tablero óptimo
"""

from __future__ import annotations
import json, click
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import math
from app import cluster, logic

DATA_SENSORES_CSV = "sensores.csv"
DATA_PANELES_CSV = "paneles.csv"

# ──────────────────────────── Capa de orquestación ─────────────────────────
def run(data_dir: Path, cap: int, radius: float, do_plot: bool, metric: str):
    
    cajas_csv, memb_csv = cluster.build_cajas(data_dir, cap, radius=radius, metric=metric)
    res   = logic.multipar(data_dir, cajas_csv, metric)

    sens   = (pd.read_csv(data_dir / DATA_SENSORES_CSV)
              if (data_dir / DATA_SENSORES_CSV).exists() else None)
    cajas  = pd.read_csv(cajas_csv)
    memb   = pd.read_csv(memb_csv)
    tb     = res["tablero"]
    panels = (pd.read_csv(data_dir / DATA_PANELES_CSV)
              if (data_dir / DATA_PANELES_CSV).exists() else None)
    
    sens["dist_tb"] = ((sens.x - tb["x"])**2 + (sens.y - tb["y"])**2).pow(0.5)
    bad_direct = sens[
        (sens.id.isin(memb.loc[memb.jb_id.isna() | (memb.jb_id==""), "sensor_id"]))
        & (sens.l_tt_cable_m < sens.dist_tb)        # cable insuficiente
    ]

    if not bad_direct.empty:
        next_idx = len(cajas) + 1
        for _, s in bad_direct.iterrows():
            jb_id = f"JB{next_idx:02d}"
            # añadir JB individual
            cajas = pd.concat(
                [cajas,
                pd.DataFrame([{"id": jb_id, "x": s.x, "y": s.y, "n": 1}])],
                ignore_index=True
                )

            memb  = pd.concat(
                [memb,
                pd.DataFrame([{"sensor_id": s.id, "jb_id": jb_id}])],
                ignore_index=True
                )
            
            # sumar su cable a las listas de metros
            d = s.dist_tb
            res["dists"].append(float(d))
            res["cables"].append(1)
            res["metros"] += d
            next_idx += 1

        # ordenar: NaN/"" primero, JBxx después
        memb = memb.sort_values("jb_id", na_position="first")

        # eliminar la fila duplicada de cada sensor y quedarte con la “buena”
        memb = memb.drop_duplicates(subset="sensor_id", keep="last")

        # reindexar de 0…N-1 para dejar el DataFrame limpio
        memb = memb.reset_index(drop=True)
        
        # actualizar lista de directos (quitar los bad)
        direct_ok = memb.loc[memb.jb_id.isna() | (memb.jb_id==""), "sensor_id"]
    else:
        direct_ok = memb.loc[memb.jb_id.isna() | (memb.jb_id==""), "sensor_id"]

    _print_report(tb, cajas, memb, res, list(direct_ok))
    _save_json(cap, tb, cajas, memb, res, list(direct_ok))
    if do_plot:
        _draw_layout(cap, sens, cajas, memb, tb, panels, res["metros"], metric)

# ──────────────────────────── 1. Consola ───────────────────────────────────
def _print_report(tb, cajas, memb, res, directos):
    click.secho(f"\n►  Tablero elegido: {tb['id']}  "
                f"@ ({tb['x']:.2f},{tb['y']:.2f})", fg="yellow")
    click.echo(f"   Multipar total = {res['metros']:.2f} m\n")

    click.echo("Junction boxes activadas:")
    for i, row in cajas.iterrows():
        sensores = memb.loc[memb.jb_id == row.id, "sensor_id"].tolist()
        click.echo(f"  • {row.id}: {len(sensores)} sens, "
                   f"{res['cables'][i]} cables → {sensores}")

    click.echo("\nSensores directos al tablero:")
    click.echo(f"   {directos or '—'}\n")

    click.echo("Lista de cortes (JB → TB):")
    total = 0
    for i, row in cajas.iterrows():
        L, nc = res["dists"][i], res["cables"][i]
        tramo = L*nc; total += tramo
        click.echo(f"  • {row.id}: {nc} × {L:.2f} m  =  {tramo:.2f} m")
    click.echo(f"  Total multipar = {total:.2f} m\n")

# ──────────────────────────── 3. JSON ─────────────────────────────────────
def _save_json(cap, tb, cajas, memb, res, directos):
    Path("results").mkdir(exist_ok=True)
    out = {
        "cap_jb": cap,
        "multipar_m": res["metros"],
        "tablero": tb,
        "directos": directos,
        "junction_boxes": {
            row.id: {
                "sensores": memb.loc[memb.jb_id == row.id,
                                     "sensor_id"].tolist(),
                "cables":   int(res["cables"][i]),
                "metros":   float(res["dists"][i]*res["cables"][i])
            }
            for i, row in cajas.iterrows()
        }
    }
    with open(f"results/cap_{cap}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

# ──────────────────────────── 4. Figura ───────────────────────────────────
def _draw_layout(cap, sens, cajas, memb, tb, panels, metros, metric):
    
    fig, ax = plt.subplots()
    
    # paneles FV
    _plot_panels(ax, panels)
    # puntos, lineas y etiquetas de sensores, cajas y tableros
    _plot_items(ax, sens, cajas, memb, tb, metric)
    # agregar titulos en plot y guardar
    _plot_finalize(fig, ax, cap, metros)
    
# ── 4a paneles ─────────────────────────────────
def _plot_panels(ax, panels):
    
    if panels is not None:
        for _, p in panels.iterrows():
            xs = [p.x1, p.x2, p.x3, p.x4, p.x1]
            ys = [p.y1, p.y2, p.y3, p.y4, p.y1]
            # dibujar el rectangulo
            ax.plot(xs, ys, c="lightgray", lw=0.8, zorder=0)
            # calcular el centroide
            cx = (p.x1 + p.x2 + p.x3 + p.x4) / 4
            cy = (p.y1 + p.y2 + p.y3 + p.y4) / 4
            # plot de la etiqueta
            ax.text(cx, cy, p.id, fontsize=6, color="dimgray",
                ha="center", va="center", zorder=0)

# ── 4b Puntos, líneas y etiquetas ─────────────────────────────────
def _plot_items(ax, sens, cajas, memb, tb, metric):
    
    ax.scatter(sens.x, sens.y, c="tab:blue", s=25, label="Sensores", zorder=3)
    for _, s in sens.iterrows():
        ax.text(s.x + 0.12, s.y + 0.12, s.id, fontsize=6, color="blue")

    ax.scatter(cajas.x, cajas.y, c="tab:orange", marker="s",
               s=40, label="JB", zorder=4)
    for _, j in cajas.iterrows():
        ax.text(j.x - 0.15, j.y + 0.12, j.id, fontsize=6,
                color="darkorange", ha="right")

    ax.scatter(tb["x"], tb["y"], c="tab:red", marker="*",
               s=180, label="Tablero", zorder=5)
    ax.text(tb["x"] + 0.12, tb["y"] - 0.3, tb["id"],
            fontsize=7, color="red", va="top")

    # Sensor → JB (filtra directos)
    for _, link in memb[memb.jb_id.notna() & (memb.jb_id != "")].iterrows():
        srow = sens.loc[sens.id == link.sensor_id].iloc[0]
        jrow = cajas.loc[cajas.id == link.jb_id].iloc[0]
        ax.plot([srow.x, jrow.x], [srow.y, jrow.y],
                lw=0.5, c="gray", zorder=1)

    # JB → Tablero
    for _, row in cajas.iterrows():
        if metric == "euclid":
            ax.plot([row.x, tb["x"]], [row.y, tb["y"]],
                lw=1.0, c="black", zorder=2)
        else: # manhattan
            # trazo en “L”: primero horizontal, luego vertical
            ax.plot([row.x, tb["x"]], [row.y, row.y],
                    lw=1, c="black", zorder=2)
            ax.plot([tb["x"], tb["x"]], [row.y, tb["y"]],
                    lw=1, c="black", zorder=2)

# ── 4c Título, leyenda y guardado ─────────────────────────────────
def _plot_finalize(fig, ax, cap, metros):
    
    ax.set_aspect("equal")
    ax.set_title(f"cap={cap}   multipar={metros:.1f} m")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    plt.savefig(f"results/layout_cap_{cap}.png", dpi=150)
    plt.show()

# ──────────────────────────── CLI wrapper ────────────────────────────────
@click.command()
@click.option("-d", "--data", default="./data", show_default=True)
@click.option("--cap-jb",     default=6,  type=int)
@click.option("--l-tt-jb",    default=3.0, type=float, show_default=True)
@click.option("--plot/--no-plot", default=False)
@click.option("--metric", type=click.Choice(["euclid", "manhattan"]),
              default="euclid", show_default=True)
def cli(data, cap_jb, l_tt_jb, plot, metric):
    run(Path(data), cap_jb, radius=l_tt_jb, do_plot=plot, metric=metric)

if __name__ == "__main__":
    cli()