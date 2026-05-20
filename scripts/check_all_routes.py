import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
from utils.overpass_handler import OverpassHandler
from utils.string_utils import make_station_code

gr_workbook = GeoRoutesExcelHandler()
overpass = OverpassHandler()


def station_lists_diff(local_stations, osm_stations):
    if set(local_stations) == set(osm_stations):
        return False, None, None
    else:
        osm_diff = []
        local_diff = []
        for local_station in local_stations:
            if local_station not in osm_stations:
                local_diff.append(local_station)
        for osm_station in osm_stations:
            if osm_station not in local_stations:
                osm_diff.append(osm_station)
        return True, local_diff, osm_diff


def check_all_routes():
    active_routes = [
        r for r in gr_workbook.routes_json
        if r.get('active') == 'y' and gr_workbook.is_sheet_exists(r['ref'])
    ]

    osm_id_to_ref = {int(r['id']): r['ref'] for r in active_routes}

    routes_data = overpass.get_routes_data(list(osm_id_to_ref.keys()))

    route_stop_ids = {}
    all_stop_ids = set()
    for route in routes_data['elements']:
        stop_ids = [m['ref'] for m in route['members'] if m['role'] == 'stop']
        route_stop_ids[route['id']] = stop_ids
        all_stop_ids.update(stop_ids)

    stations_data = overpass.get_stations_data(all_stop_ids)
    station_code_by_id = {}
    for s in stations_data['elements']:
        if 'tags' in s and 'name:en' in s['tags']:
            station_code_by_id[s['id']] = make_station_code(s['tags']['name:en'])
        else:
            station_code_by_id[s['id']] = f'unknownstation{s["id"]}'

    diffs = []
    for osm_id, route_ref in osm_id_to_ref.items():
        existing = gr_workbook.get_route_stations(route_ref)
        actual = [station_code_by_id.get(sid, f'unknownstation{sid}') for sid in route_stop_ids.get(osm_id, [])]
        has_diff, local_diff, osm_diff = station_lists_diff(existing, actual)
        if has_diff:
            diffs.append((route_ref, local_diff, osm_diff))

    if not diffs:
        print('All routes are consistent with OSM')
    else:
        for route_ref, local_diff, osm_diff in diffs:
            print(f'Route {route_ref} requires a manual check')
            print(f'  Only in local data: {local_diff}')
            print(f'  Only in OSM: {osm_diff}')


if __name__ == '__main__':
    check_all_routes()
