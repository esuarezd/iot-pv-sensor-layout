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
view.py  - Prueba interactiva para UNA capacidad.
  python app/view.py -d ./data --cap-jb 4 --l-jb-tb 100
Requiere: pip install click
"""
import json, click
from pathlib import Path
import logic


@click.command()
@click.option("-d", "--data", default="./data", show_default=True)
@click.option("--cap-jb",  default=6,  type=int,   show_default=True)
@click.option("--l-tt-jb", default=3.0, type=float, show_default=True)
@click.option("--l-jb-tb", default=50.0, type=float, show_default=True)
@click.option("--l-tt-tb", default=12.0, type=float, show_default=True)
@click.option("-v", "--verbose", is_flag=True)
def main(data, cap_jb, l_tt_jb, l_jb_tb, l_tt_tb, verbose):
    cfg = logic.Settings(cap_jb=cap_jb, l_tt_jb=l_tt_jb,
                         l_jb_tb=l_jb_tb, l_tt_tb=l_tt_tb,
                         solver_msg=verbose)
    res = logic.solve(Path(data), cfg)
    x, y, d, k = (res["vars"][v] for v in ("x", "y", "d", "k"))

    tb = res["tablero"]
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
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
