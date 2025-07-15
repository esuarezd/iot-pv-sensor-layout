# iot-pv-sensor-layout
Model to place junction boxes and a central panel board for PV transmitters sensors.

Author: Edison Suarez. 

markdown ## License Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

Enable virtual environment
source .venv/bin/activate

Run the milp according to the capacity to evaluate
python -m app.view  --cap-jb 1  --plot --metric manhattan

python -m app.view  --cap-jb 2  --plot --metric manhattan

python -m app.view  --cap-jb 3  --plot --metric manhattan

python -m app.view  --cap-jb 4  --plot --metric manhattan

python -m app.view  --cap-jb 5  --plot --metric manhattan

python -m app.view  --cap-jb 6  --plot --metric manhattan


Check Comparative curve
python batch/summary.py         # compara resultados


