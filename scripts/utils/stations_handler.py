import json
from config import STATIONS_LIST_JS_PATH


class StationsHandler:
    def __init__(self):
        with open(STATIONS_LIST_JS_PATH, 'r', encoding='utf-8') as file:
            stations = json.loads(file.read().lstrip('export const stations = '))
        self._stations = stations

    def get_station_names_by_code(self, code):
        station = self._stations.get(code)
        if station:
            return [station['name_en'], station['name_ru'], station['name_ka']]
        return ['unknown station', 'неизвестная станция', 'unknown station']
