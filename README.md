# iot-pv-sensor-layout
Model to place junction boxes and a central panel board for PV transmitters sensors.

Author: Edison Suarez. 

markdown ## License Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

Enable virtual environment
source .venv/bin/activate

Run the milp according to the capacity to evaluate
python -m app.view -d ./data --cap-jb 1  --l-jb-tb 100 --plot

python -m app.view -d ./data --cap-jb 2  --l-jb-tb 100 --plot

python -m app.view -d ./data --cap-jb 3  --l-jb-tb 100 --plot

python -m app.view -d ./data --cap-jb 4  --l-jb-tb 100 --plot

python -m app.view -d ./data --cap-jb 6  --l-jb-tb 100 --plot


Check Comparative curve
python batch/summary.py         # compara resultados


