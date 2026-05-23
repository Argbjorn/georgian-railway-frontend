# make_stations_json() обновляет stations-list.js, который используется на фронте для отрисовки станций, а также на
# бэке в make_routes_files.py для названий станций на разных языках.
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config import STATIONS_LIST_JS_PATH, STATIONS_JSON_PATH, ROUTES_JSON_PATH
from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
from utils.overpass_handler import OverpassHandler
from utils.string_utils import *
from pathlib import Path

file_path = Path(__file__).parent.parent / "data" / "station_gr_codes.json"
gr_workbook = GeoRoutesExcelHandler()
overpass = OverpassHandler()


def get_station_gr_code(station_name):
    """По коду станции (английское название, пропущенное через lower и без пробелов) получает код ГЖД (GR).
    Есть несколько станций, код которых нельзя сопоставить с источником кодов GR, поэтому создан словарь
    exceptional_stations"""
    exceptional_stations = {'batumicentral': 'Batumi',
                            'borjomiparki': 'Borjomi',
                            'jumati': 'Djumati',
                            'kutaisiinternationalairport': 'Kutaisi International Airport',
                            'kutaisi1': 'Kutaisi I',
                            'platform11km': 'Platform 11 km',
                            'platform16km': 'Platform 16 km',
                            'rustavicentral': 'Rustavi -pass.',
                            'samtredia1': 'Samtredia',
                            'samtredia2': 'Samtredia II',
                            'tbilisicentralstation': 'Tbilisi-pass.',
                            'navtlughi': 'Tbilisi-cross.',
                            'tbilisimarshalling': 'Tbilisi-sort.',
                            'rustavicargo': 'Rustavi-fr.'}

    with open(file_path, "r", encoding='utf-8') as station_codes_file:
        station_codes = json.load(station_codes_file)
    if station_name in exceptional_stations:
        station_name = exceptional_stations[station_name]
    for station in station_codes:
        if station['Name'].lower() == station_name.lower():
            return station['Code']
    return '00000'


def get_existing_station_descriptions():
    """Первоисточником описаний станций является stations.json. Поэтому при обновлении stations-list.js и stations.json
     сначала сохраняем существующие описания и добавляем их обратно в пересозданный файл"""
    with open(STATIONS_JSON_PATH, 'r', encoding='utf-8') as file:
        stations = json.load(file)
    station_descriptions = {}
    for station in stations:
        if 'description' in station:
            station_descriptions[station['code']] = station['description']
    return station_descriptions


def add_route_to_stations_list(stations_list, station_code, route_data, role, arrival_time, departure_time, stop_time):
    """Получает словарь станций и проходящих через них маршрутов и добавляет данный маршрут в соответствии с его
    ролью"""
    stations_list_updated = stations_list.copy()
    route_data_updated = route_data.copy()
    route_data_updated['arrival_time'] = arrival_time
    route_data_updated['departure_time'] = departure_time
    route_data_updated['stop_time'] = stop_time
    if station_code not in stations_list:
        stations_list_updated[station_code] = {'departure': [], 'arrival': [], 'via': [], }
        if role == 'start':
            stations_list_updated[station_code]['departure'] = [route_data_updated]
        elif role == 'end':
            stations_list_updated[station_code]['arrival'] = [route_data_updated]
        else:
            stations_list_updated[station_code]['via'] = [route_data_updated]
    else:
        if role == 'start':
            stations_list_updated[station_code]['departure'].append(route_data_updated)
        elif role == 'end':
            stations_list_updated[station_code]['arrival'].append(route_data_updated)
        else:
            stations_list_updated[station_code]['via'].append(route_data_updated)
    return stations_list_updated


def get_routes_for_stations():
    """Составляет словарь всех станций и проходящих через них маршрутов"""
    with open(ROUTES_JSON_PATH, 'r', encoding="utf-8") as file:
        routes_data = json.load(file)
    stations_with_routes = {}
    for r in routes_data:
        route_data = {
            'ref': r['ref'],
            'name_en': r['name:en'],
            'name_ru': r['name:ru'],
            'name_ka': r['name:ka'],
            'frequency': r['frequency'],
            'start_date': r['start_date'],
            'end_date': r['end_date'],
            }
        if r.get('stations'):
            for s in r['stations']:
                stations_with_routes = add_route_to_stations_list(stations_with_routes, s['code'], route_data, s['role'], s['arrival_time'], s['departure_time'], s['stop_time'])
    return stations_with_routes


def make_stations_json():
    all_route_osm_ids = gr_workbook.get_all_routes_osm_id(show_on_site_only=True)
    routes_data = overpass.get_routes_data(all_route_osm_ids)
    station_ids = set()
    for route in routes_data['elements']:
        for member in route['members']:
            if member['role'] == 'stop':
                station_ids.add(member['ref'])
    stations_data = overpass.get_stations_data(station_ids)
    station_descriptions = get_existing_station_descriptions()
    stations_with_routes = get_routes_for_stations()
    stations_arr = []
    for station in stations_data['elements']:
        tags = station.get('tags', {})
        generic_name = tags.get('name', 'unknown station')
        name_en = tags.get('name:en', generic_name)
        name_ka = tags.get('name:ka', generic_name)
        name_ru = tags.get('name:ru', generic_name)
        code = make_station_code(name_en)
        exists = False
        for s in stations_arr:
            if s['code'] == code:
                s['id'].append(station['id'])
                exists = True
                continue
        if not exists:
            station_type = 'secondary'
            if code == 'batumicentral':
                station_type = 'beach'
            elif code == 'kutaisiinternationalairport':
                station_type = 'airport'
            elif code == 'tbilisicentralstation':
                station_type = 'main'
            station_data = {"id": [station['id']],
                            "coords": [station['lat'], station['lon']],
                            "code": code,
                            "type": station_type,
                            "name_en": name_en,
                            "name_ka": name_ka,
                            "name_ru": name_ru,
                            "gr_code": get_station_gr_code(code)
                            }
            if code in station_descriptions:
                station_data['description'] = station_descriptions[code]
            if code in stations_with_routes:
                station_data['routes'] = stations_with_routes[code]
            stations_arr.append(station_data)
    result = json.dumps(sorted(stations_arr, key=lambda x: x['name_en']), ensure_ascii=False, indent=3)
    with open(STATIONS_LIST_JS_PATH, 'w', encoding='utf-8') as file:
        file.write("export const stations = " + result)
        print('station-list.js was rewrited')
    with open(STATIONS_JSON_PATH, 'w', encoding='utf-8') as file:
        file.write(result)
        print('stations.json was rewrited')


if __name__ == '__main__':
    for attempt in range(1, 6):
        try:
            make_stations_json()
            break
        except Exception as e:
            if attempt == 5:
                raise
            print(f"Attempt {attempt} failed: {e}. Retrying in 3s...")
            time.sleep(3)
