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
import logging
import os

# Definir la ruta del directorio de logs 
log_dir = 'log'

# Crear las carpetas log si no existe
os.makedirs(log_dir, exist_ok=True)

# Definir la ruta del directorio de logs 
log_file = 'log/app.log'

# Configurar el sistema de logging
logging.basicConfig(
    level=logging.INFO,  # Nivel de severidad (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",  # Formato del mensaje
    handlers=[
        logging.StreamHandler(),  # Mostrar en la terminal
        logging.FileHandler(log_file, mode="a", encoding="utf-8-sig")  # Registrar en un archivo
    ]
)

from app import view
    
# Main function
def main():
    view.main()


# Main function call to run the program
if __name__ == '__main__':
    main()