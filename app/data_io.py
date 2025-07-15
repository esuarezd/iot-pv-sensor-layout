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

#app/data_io.py
from pathlib import Path
import pandas as pd

def load_sensores(dir: Path) -> pd.DataFrame:
    """lee sensores.csv y lo convierte en un df
    sensores.csv esperado es:
    id,x,y,l_tt_cable_m
    S01,8,-0.5,3
    
    Args:
        dir (Path): ruta de ubicacion de sensores.csv

    Returns:
        pd.DataFrame: dataframe con la ubicacion de los sensores
    """
    return pd.read_csv (dir / "sensores.csv")

def load_tableros(dir: Path) -> pd.DataFrame:
    """lee tableros.csv y lo convierte en un df
    tableros.csv esperado es 
    id,x,y
    TB01,7,-4
    
    Args:
        dir (Path): ruta de ubicacion de tableros.csv

    Returns:
        pd.DataFrame: dataframe con la ubicacion posible del tablero
    """
    return pd.read_csv(dir / "tableros.csv")

def load_paneles(dir: Path) -> pd.DataFrame | None:
    """lee paneles.csv y lo convierte en un df
    paneles.csv esperado es:
    id,x1,y1,x2,y2,x3,y3,x4,y4
    PV01,6.0,0.0,8.0,0.0,8.0,-1.0,6.0,-1.0
    
    Args:
        dir (Path): ruta de ubicacion de paneles.csv

    Returns:
        pd.DataFrame | None: dataframe con la ubicacion de los paneles
    """
    file = dir / "paneles.csv"
    if file.exists():
        return pd.read_csv(file) 
    else:
        return None



