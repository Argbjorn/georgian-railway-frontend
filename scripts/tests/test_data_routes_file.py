"""Тесты для проверки data файла routes.json"""

import json
import pytest
import fastjsonschema
from utils import ROUTES_FILE, time_string_to_minutes

ROUTE_SCHEMA = {
  "$schema": "http://json-schema.org/schema#",
  "title": "Route",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "minimum": 1
    },
    "ref": {
      "type": "integer",
      "minimum": 1
    },
    "name:ka": {
      "type": "string",
      "minLength": 1
    },
    "name:en": {
      "type": "string",
      "minLength": 1
    },
    "name:ru": {
      "type": "string",
      "minLength": 1
    },
    "frequency": {
      "type": "string",
      "enum": ["daily", "every second day", "on odd days", "on even days", "on workdays"]
    },
    "start_date": {
      "type": ["integer", "null"]
    },
    "end_date": {
      "type": ["integer", "null"]
    },
    "complete": {
      "type": "boolean"
    },
    "online": {
      "type": "boolean"
    },
    "online_tickets_current_site": {
      "type": "boolean"
    },
    "online_tickets_new_site": {
      "type": "boolean"
    },
    "train_type": {
        "anyOf": [
                {"type": "string", 
                 "enum": ["stadler", "suburban", "vmk-grt"]},
                {"type": "null"}
        ]
    },
    "has_arrival_time": {
      "type": "boolean"
    },
    "description_en": {
      "type": ["string", "null"]
    },
    "description_ru": {
      "type": ["string", "null"]
    },
    "description_ka": {
      "type": ["string", "null"]
    },
    "stations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": {
            "type": "string"
          },
          "role": {
            "type": "string",
            "enum": ["start", "middle", "end"]
          },
          "name_en": {
            "type": "string"
          },
          "name_ru": {
            "type": "string"
          },
          "name_ka": {
            "type": "string"
          },
          "departure_time": {
            "type": "string",
            "anyOf": [
              { "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$" },
              { "pattern": "^(-)$" }
            ]
          },
          "arrival_time": {
            "type": ["string", "null"],
            "anyOf": [
              { "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$" },
              { "pattern": "^(-)$" }
            ]
          },
          "stop_time": {
            "type": ["integer", "null"]
          }
        },
        "required": [
          "code",
          "role",
          "name_en",
          "name_ru",
          "name_ka",
          "departure_time"
        ]
      }
    },
    "travel_time": {
      "type": "string",
      "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    },
    "price": {
      "type": ["object", "null"],
      "properties": {
        "price_type": {
          "type": "string",
          "enum": ["exact", "from"]
        },
        "price": {
          "type": "number",
          "minimum": 0
        }
      },
      "required": ["price_type", "price"]
    },
    "analogue": {
      "type": ["array", "null"]
    }
  },
  "required": [
    "id",
    "ref",
    "name:ka",
    "name:en",
    "name:ru",
    "frequency",
    "complete",
    "online",
    "online_tickets_current_site",
    "online_tickets_new_site",
    "has_arrival_time"
  ]
}

@pytest.fixture(scope="class")
def routes_data():
    with open(ROUTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.mark.routes_file
class TestDataRoutesFile:

    def test_routes_file_schema(self, routes_data):
        """Проверяет, что файл routes.json соответствует схеме"""
        route_validator = fastjsonschema.compile(ROUTE_SCHEMA)
        for route in routes_data:
            try:
                route_validator(route)
            except fastjsonschema.JsonSchemaException as e:
                pytest.fail(f"Маршрут {route['ref']} (id: {route['id']}) не соответствует схеме: {e}")

    def test_travel_time_is_reasonable(self, routes_data):
        """Проверяет, что время в пути в диапазоне от 0 до 24 часов (только для маршрутов с указанным travel_time)"""
        for route in routes_data:
            travel_time = route.get('travel_time')
            if not travel_time:
                continue
            hours, minutes = map(int, travel_time.split(':'))
            total_minutes = hours * 60 + minutes
            assert total_minutes <= 24 * 60 and total_minutes > 0, f"Время в пути для маршрута {route['ref']} (id: {route['id']}) превышает 24 часа или меньше 0"

    def test_stations_have_correct_roles(self, routes_data):
        """Проверяет, что станции маршрута имеют правильные роли"""
        for route in routes_data:
            stations = route.get('stations')
            if not stations:
                continue
            for i, station in enumerate(stations):
                if i == 0:
                    assert station['role'] == "start", f"Первая станция маршрута {route['ref']} (id: {route['id']}) имеет роль {station['role']}"
                elif i == len(stations) - 1:
                    assert station['role'] == "end", f"Последняя станция маршрута {route['ref']} (id: {route['id']}) имеет роль {station['role']}"
                else:
                    assert station['role'] == "middle", f"Промежуточная станция маршрута {route['ref']} (id: {route['id']}) имеет роль {station['role']}"

    def test_route_stations_arrival_times_are_sequential(self, routes_data):
        """Проверяет, что время прибытия на станциях маршрута идет по порядку"""
        for route in routes_data:
            if route.get('travel_time') and route.get('stations'):
              travel_time = time_string_to_minutes(route['travel_time'])
              prev_station_time = time_string_to_minutes(route['stations'][0]['departure_time'])
              real_time = []
              real_time.append(prev_station_time)
              current_day = 0
              for station in route['stations'][1:]:
                  # У маршрутов с временем прибытия для конечной станции задан только arrival_time
                  if route['has_arrival_time'] == True and station['role'] == 'end':
                      current_station_time = time_string_to_minutes(station['arrival_time'])
                  else:
                      current_station_time = time_string_to_minutes(station['departure_time'])
                  if current_station_time < prev_station_time % 1440:
                      current_day += 1
                  current_station_time += current_day * 1440
                  real_time.append(current_station_time)
                  prev_station_time = current_station_time
              calculated_travel_time = real_time[-1] - real_time[0]
              assert travel_time == calculated_travel_time, f"Время в расписании станций на маршруте {route['ref']} (id: {route['id']}) идет не по порядку"
            else:
                continue
            
    def test_route_analogues_are_active(self, routes_data):
        """Проверяет, что аналоги маршрута активны (тоже присутствуют в файле)"""
        active_routes = [str(route['ref']) for route in routes_data]
        for route in routes_data:
            if route['analogue']:
                for analogue in route['analogue']:
                    assert analogue in active_routes, f"Аналог маршрута {route['ref']} (id: {route['id']}) не присутствует в файле"

    def test_route_has_arrival_time(self, routes_data):
        """Проверяет, что у маршрута c has_arrival_time=true действительно есть arrival_time для всех станций кроме начальной"""
        for route in routes_data:
            if route['has_arrival_time'] == True:
                for station in route['stations'][1:]:
                    assert station['arrival_time'] is not None and station['arrival_time'] != "-", f"У маршрута {route['ref']} (id: {route['id']}) нет arrival_time для станции {station['code']}"

    def test_routes_are_unique(self, routes_data):
        """Проверяет, что маршруты уникальны по ref"""
        assert len(routes_data) == len(set(route['ref'] for route in routes_data)), "Маршруты не уникальны по ref"