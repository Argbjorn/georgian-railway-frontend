import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from config import ROUTES_LIST_JS_PATH, ROUTES_JSON_PATH
from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
from utils.string_utils import remove_patterns
import calendar
from datetime import datetime, timedelta


def string_value_to_bool(row, key):
    return row[key] == "y"


def empty_to_none(val):
    if val is None:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def to_unixtime(val):
    """Преобразует значение из таблицы в Unix timestamp в миллисекундах (UTC). Пустое -> None."""
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    if isinstance(val, (int, float)):
        num = float(val)
        if num >= 1e12:
            return int(num)  # уже в миллисекундах
        if num >= 1e9:
            return int(num * 1000)  # в секундах -> в миллисекунды
        # Excel serial (дни с 1899-12-30), трактуем как UTC
        epoch = datetime(1899, 12, 30)
        dt = epoch + timedelta(days=num)
        return calendar.timegm(dt.timetuple()) * 1000
    s = val.strip()
    # Форматы: ISO, EU (d.m.y), US (m/d/y), d/m/y — дата как полночь UTC
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            return calendar.timegm(dt.timetuple()) * 1000
        except ValueError:
            continue
    return None


def get_time_difference(start, end):
    if start in ['-', '', None] or end in ['-', '', None]:
        return None
    start_dt = datetime.strptime(start, '%H:%M')
    end_dt = datetime.strptime(end, '%H:%M')
    diff = end_dt - start_dt if end_dt > start_dt else end_dt + timedelta(hours=24) - start_dt
    return int(diff.total_seconds() / 60)


def get_route_travel_time(stations):
    if stations[1]['arrival_time'] is None:
        start = stations[0]['departure_time']
        end = stations[-1]['departure_time']
    else:
        start = stations[0]['departure_time']
        end = stations[-1]['arrival_time']

    if start == '-' or end == '-':
        return '-'

    start_dt = datetime.strptime(start, '%H:%M')
    end_dt = datetime.strptime(end, '%H:%M')
    diff = end_dt - start_dt if end_dt > start_dt else end_dt + timedelta(hours=24) - start_dt

    total_minutes = int(diff.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    return f"{hours:02d}:{minutes:02d}"


def get_route_price(*args):
    real_prices = [p for p in args if p is not None]
    if len(real_prices) == 0:
        return None
    elif len(real_prices) == 1:
        return {"price_type": "exact", "price": real_prices[0]}
    else:
        return {"price_type": "from", "price": min(real_prices)}


def parse_price(val, field, route_ref):
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValueError(f"Route {route_ref}: invalid price value '{val}' in field '{field}'")



def build_station(station, idx, total):
    data = {
        "code": station['station'],
        "role": "start" if idx == 0 else "end" if idx == total - 1 else "middle",
    }
    if 'time' in station:
        data['departure_time'] = station['time'] if station['time'] is not None else 'nn:nn'
        data['arrival_time'] = None
        data['stop_time'] = None
    else:
        data['departure_time'] = station['departure_time'] if station['departure_time'] != '' else '-'
        data['arrival_time'] = station['arrival_time'] if station['arrival_time'] != '' else '-'
        data['stop_time'] = get_time_difference(data['arrival_time'], data['departure_time'])
    return data


def build_route(row, gr_workbook):
    route = {
        "id": int(row["id"]),
        "ref": int(row["ref"]),
        "name:ka": remove_patterns(row["name_ka"]),
        "name:en": remove_patterns(row["name_en"]),
        "name:ru": remove_patterns(row["name_ru"]),
        "active": string_value_to_bool(row, "active"),
        "frequency": empty_to_none(row["frequency"]),
        "start_date": to_unixtime(row["start_date"]),
        "end_date": to_unixtime(row["end_date"]),
        "complete": string_value_to_bool(row, "complete"),
        "online": string_value_to_bool(row, "online"),
        "online_tickets_current_site": string_value_to_bool(row, "online_tickets_current_site"),
        "online_tickets_new_site": string_value_to_bool(row, "online_tickets_new_site"),
        "train_type": empty_to_none(row["train_type"]),
        "has_arrival_time": string_value_to_bool(row, "has_arrival_time"),
        "description_en": empty_to_none(row["description_en"]),
        "description_ru": empty_to_none(row["description_ru"]),
        "description_ka": empty_to_none(row["description_ka"]),
        "extended_description_en": empty_to_none(row["extended_description_en"]),
        "extended_description_ru": empty_to_none(row["extended_description_ru"]),
        "extended_description_ka": empty_to_none(row["extended_description_ka"]),
    }

    if gr_workbook.is_sheet_exists(row["ref"]):
        stations_json = gr_workbook.get_route_stations_with_time(route["ref"])
        route["stations"] = [build_station(s, idx, len(stations_json)) for idx, s in enumerate(stations_json)]
    elif row['active'] == 'y':
        raise ValueError(f"Route {row['ref']} is active but has no sheet in the spreadsheet")

    if row['active'] == 'y':
        route['travel_time'] = get_route_travel_time(route['stations'])

    route['price'] = get_route_price(
        parse_price(row["price_2_class"], "price_2_class", row["ref"]),
        parse_price(row["price_1_class"], "price_1_class", row["ref"]),
        parse_price(row["price_business"], "price_business", row["ref"]),
        parse_price(row["price_standard"], "price_standard", row["ref"]),
    )

    return route


def compute_analogues_and_reverse(routes):
    index = {}
    for route in routes:
        if not route.get('active') or not route.get('stations'):
            continue
        start = next((s['code'] for s in route['stations'] if s['role'] == 'start'), None)
        end = next((s['code'] for s in route['stations'] if s['role'] == 'end'), None)
        if start and end:
            index.setdefault((start, end), []).append(route['ref'])

    for route in routes:
        if not route.get('stations'):
            route['analogue'] = []
            route['reverse'] = []
            continue
        start = next((s['code'] for s in route['stations'] if s['role'] == 'start'), None)
        end = next((s['code'] for s in route['stations'] if s['role'] == 'end'), None)
        route['analogue'] = [ref for ref in index.get((start, end), []) if ref != route['ref']]
        route['reverse'] = index.get((end, start), [])


def make_routes_files():
    gr_workbook = GeoRoutesExcelHandler()
    routes_handled = [
        build_route(row, gr_workbook)
        for row in gr_workbook.routes_json
        if row["show_on_site"] != 'n'
    ]
    compute_analogues_and_reverse(routes_handled)

    json_result = json.dumps(sorted(routes_handled, key=lambda x: int(x["ref"])), ensure_ascii=False, indent=3)
    js_result = "export const routes = " + json_result

    updated = False
    for path, content, label in [
        (ROUTES_LIST_JS_PATH, js_result, "routes-list.js"),
        (ROUTES_JSON_PATH, json_result, "routes.json"),
    ]:
        existing = None
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                existing = f.read()
        if content != existing:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{label} updated")
            updated = True
    if not updated:
        print("All files are up to date")


if __name__ == '__main__':
    make_routes_files()
