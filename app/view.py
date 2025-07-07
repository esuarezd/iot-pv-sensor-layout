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
view.py
CLI para lanzar el optimizador MILP y mostrar el resultado.

Requisitos:
    pip install click
"""

import json, click
from pathlib import Path
from app import logic


@click.command()
@click.option("-d", "--data", default="./data", help="Carpeta con CSV")
@click.option("--cap-jb", default=6, type=int, show_default=True,
              help="Capacidad (sensores) por junction-box")
@click.option("--l-tt-jb", default=3.0, type=float, show_default=True,
              help="Máx. distancia TT→JB (m)")
@click.option("--l-jb-tb", default=50.0, type=float, show_default=True,
              help="Máx. distancia JB→Tablero (m)")
@click.option("--l-tt-tb", default=12.0, type=float, show_default=True,
              help="Máx. distancia TT→Tablero para sensores 'directo' (m)")
@click.option("-v", "--verbose", is_flag=True, help="Muestra trazas del solver")
def main(data, cap_jb, l_tt_jb, l_jb_tb, l_tt_tb, verbose):
    cfg = logic.Settings(
        cap_jb=cap_jb,
        l_tt_jb=l_tt_jb,
        l_jb_tb=l_jb_tb,
        l_tt_tb=l_tt_tb,
        solver_msg=verbose,
    )

    result = logic.solve(Path(data), cfg)
    x, y, d = result["vars"]["x"], result["vars"]["y"], result["vars"]["d"]

    # --- Imprime resumen legible -------------------------------------------
    tb = result["tablero"]
    click.secho(f"\n►  Tablero elegido: {tb['id']}  @ ({tb['x']:.2f}, {tb['y']:.2f})",
                fg="yellow")
    click.echo(f"   Longitud total de cable = {result['cost']:.2f} m\n")

    click.echo("Junction boxes activadas:")
    for jb_id, var in y.items():
        if var.value() == 1:
            sensores = [i for (i, jj), xv in x.items() if jj == jb_id and xv.value() == 1]
            click.echo(f"  • {jb_id}: {len(sensores)} sensores → {sensores}")

    directos = [i for i, dv in d.items() if dv.value() == 1]
    click.echo("\nSensores directos al tablero:")
    click.echo(f"   {directos}\n")

    # --- Guarda resumen JSON (seguro) --------------------------------------
    safe = {
        "cost": result["cost"],
        "tablero": tb,
        "settings": vars(result["settings"]),
        "directos": directos,
        "junction_boxes": {
            jb_id: [
                i for (i, jj), xv in x.items()
                if jj == jb_id and xv.value() == 1
            ]
            for jb_id, var in y.items() if var.value() == 1
        }
    }
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
