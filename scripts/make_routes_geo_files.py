import os
from config import ROUTES_GEODATA_DIR
from utils.overpass_handler import OverpassHandler
from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
import json

overpass = OverpassHandler()
gr_workbook = GeoRoutesExcelHandler()

active_osm_ids = set(int(i) for i in gr_workbook.get_all_routes_osm_id(active_only=True))
routes_data = overpass.get_routes_data(list(active_osm_ids))

for route in routes_data['elements']:
    file_path = os.path.join(ROUTES_GEODATA_DIR, f'{route["id"]}.json')
    new_content = json.dumps(route)
    existing_content = None
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as f:
            existing_content = f.read()
    if new_content != existing_content:
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(new_content)
        print(f'{route["id"]}.json updated')

returned_ids = {route['id'] for route in routes_data['elements']}
for osm_id in active_osm_ids - returned_ids:
    print(f'WARNING: route {osm_id} is active but was not returned by Overpass')

for filename in os.listdir(ROUTES_GEODATA_DIR):
    if not filename.endswith('.json'):
        continue
    file_osm_id = int(filename[:-5])
    if file_osm_id not in active_osm_ids:
        os.remove(os.path.join(ROUTES_GEODATA_DIR, filename))
        print(f'{filename} removed (route is not active)')
