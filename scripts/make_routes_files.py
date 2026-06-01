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


def is_route_active(route_ref, routes):
    try:
        ref_int = int(float(route_ref))
    except (ValueError, TypeError):
        return False
    for route in routes:
        try:
            if int(float(route["ref"])) == ref_int:
                return str(route.get("active", "")).strip().lower() == "y"
        except (ValueError, TypeError, KeyError):
            continue
    return False


def make_routes_files():
    gr_workbook = GeoRoutesExcelHandler()
    routes = gr_workbook.routes_json
    routes_handled = []

    for i in routes:
        if i["show_on_site"] == 'n':
            continue
        route = {"id": int(i["id"]),
                 "ref": int(i["ref"]),
                 "name:ka": remove_patterns(i["name_ka"]),
                 "name:en": remove_patterns(i["name_en"]),
                 "name:ru": remove_patterns(i["name_ru"]),
                 "active": string_value_to_bool(i, "active"),
                 "frequency": empty_to_none(i["frequency"]),
                 "start_date": to_unixtime(i["start_date"]),
                 "end_date": to_unixtime(i["end_date"]),
                 "complete": string_value_to_bool(i, "complete"),
                 "online": string_value_to_bool(i, "online"),
                 "online_tickets_current_site": string_value_to_bool(i, "online_tickets_current_site"),
                 "online_tickets_new_site": string_value_to_bool(i, "online_tickets_new_site"),
                 "train_type": empty_to_none(i["train_type"]),
                 "has_arrival_time": string_value_to_bool(i, "has_arrival_time"),
                 "description_en": empty_to_none(i["description_en"]),
                 "description_ru": empty_to_none(i["description_ru"]),
                 "description_ka": empty_to_none(i["description_ka"]),
                 "extended_description_en": empty_to_none(i["extended_description_en"]),
                 "extended_description_ru": empty_to_none(i["extended_description_ru"]),
                 "extended_description_ka": empty_to_none(i["extended_description_ka"])
                 }
        # Routes from excel (if route sheet exists)
        if gr_workbook.is_sheet_exists(i["ref"]):
            stations_temp = []
            stations_json = gr_workbook.get_route_stations_with_time(route["ref"])

            for idx, station in enumerate(stations_json):
                role = "start" if idx == 0 else "end" if idx == len(stations_json) - 1 else "middle"

                station_data = {
                    "code": station['station'],
                    "role": role,
                }

                if 'time' in station:
                    station_data['departure_time'] = station['time'] if station['time'] is not None else 'nn:nn'
                    station_data['arrival_time'] = None
                    station_data['stop_time'] = None
                else:
                    station_data['departure_time'] = station['departure_time'] if station['departure_time'] != '' else '-'
                    station_data['arrival_time'] = station['arrival_time'] if station['arrival_time'] != '' else '-'
                    station_data['stop_time'] = get_time_difference(station_data['arrival_time'], station_data['departure_time'])

                stations_temp.append(station_data)

            route["stations"] = stations_temp
        elif i['active'] == 'y':
            raise ValueError(f"Route {i['ref']} is active but has no sheet in the spreadsheet")
        if i['active'] == 'y':
            route['travel_time'] = get_route_travel_time(route['stations'])
        route['price'] = get_route_price(parse_price(i["price_2_class"], "price_2_class", i["ref"]),
                                         parse_price(i["price_1_class"], "price_1_class", i["ref"]),
                                         parse_price(i["price_business"], "price_business", i["ref"]),
                                         parse_price(i["price_standard"], "price_standard", i["ref"]))
        # analogue: пустая строка — нет аналогов; одно число — один аналог; числа через запятую без пробела — несколько
        # заголовок в таблице может быть "analogue", "Analogue", "аналог" и т.д.
        analogue_val = None
        for key in ("analogue", "Analogue", "Аналог", "аналог"):
            if key in i and i[key] is not None and str(i[key]).strip() != "":
                analogue_val = i[key]
                break
        analogue_str = str(analogue_val or "").strip()
        if not analogue_str:
            route["analogue"] = []
        else:
            parts = [p.strip() for p in analogue_str.split(",") if p.strip()]
            refs = []
            for p in parts:
                try:
                    refs.append(str(int(float(p))))  # "11.0" из Excel → "11"
                except (ValueError, TypeError):
                    continue
            route["analogue"] = [ref for ref in refs if is_route_active(ref, routes)]
        routes_handled.append(route)

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
