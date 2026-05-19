# Этот скрипт берет все маршруты их таблицы маршрутов и через Overpass API получает их геоданные, которые сохраняет в виде отдельных json файлов в папке geodata. Эти файлы потом используются для отображения маршрутов на карте (непосредственной отрисовки).

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ROUTES_GEODATA_DIR
from utils.overpass_handler import OverpassHandler
from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
import json

overpass = OverpassHandler()
gr_workbook = GeoRoutesExcelHandler()

routes = gr_workbook.get_all_routes_osm_id()
print('Overpass data receiving')
routes_data = overpass.get_routes_data(routes)
print('Overpass data was received')

for route in routes_data['elements']:
    file_path = os.path.join(ROUTES_GEODATA_DIR, f'{route["id"]}.json')
    with open(file_path, 'w', encoding="utf-8") as json_file:
        json_file.write(json.dumps(route))
    print(f'{route["id"]}.json was successfully updated')
