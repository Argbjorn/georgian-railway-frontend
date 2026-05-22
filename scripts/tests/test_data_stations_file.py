"""Тесты для проверки data файла stations.json"""

import json
import pytest
import fastjsonschema
from utils import STATIONS_FILE, time_string_to_minutes

STATIONS_SCHEMA = {
  "$schema": "http://json-schema.org/schema#",
  "title": "Station",
  "type": "object",
  "properties": {
    "id": {
      "type": "array",
      "items": { "type": "integer" },
      "minItems": 1
    },
    "coords": {
      "type": "array",
      "items": { "type": "number", "minimum": -90, "maximum": 90 },
      "minItems": 2,
      "maxItems": 2
    },
    "code": {
      "type": "string",
      "minLength": 1
    },
    "type": {
      "type": "string",
      "enum": ["primary", "secondary", "beach", "airport", "main"]
    },
    "name_en": {
      "type": "string",
      "minLength": 1
    },
    "name_ka": {
      "type": "string",
      "minLength": 1
    },
    "name_ru": {
      "type": "string",
      "minLength": 1
    },
    "gr_code": {
      "type": ["integer", "string"]
    },
    "description": {
      "type": "object",
      "properties": {
        "en": {"type": "string", "minLength": 1},
        "ru": {"type": "string", "minLength": 1},
        "ka": {"type": "string", "minLength": 1}
      },
      "required": ["en", "ru"]
    },
    "routes": {
      "type": "object",
      "properties": {
        "departure": { "$ref": "#/$defs/Route" },
        "arrival": { "$ref": "#/$defs/Route" },
        "via": { "$ref": "#/$defs/Route" }
      },
      "required": ["departure", "arrival", "via"]
    }
  },
  "required": [
    "id",
    "coords",
    "code",
    "type",
    "name_en",
    "name_ka",
    "name_ru",
    "gr_code",
    "routes"
  ],
  "$defs": {
    "Route": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ref": { "type": "integer" },
          "name_en": { "type": "string", "minLength": 1 },
          "name_ru": { "type": "string", "minLength": 1 },
          "name_ka": { "type": "string", "minLength": 1 },
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
          "arrival_time": {
            "type": ["string", "null"],
            "anyOf": [{"pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"},
                      {"pattern": "^(-)$"}]
          },
          "departure_time": {
            "type": "string",
            "anyOf": [{"pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"},
                      {"pattern": "^(-)$"}]
          },
          "stop_time": {
            "type": ["integer", "null"],
            "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
          }
        },
        "required": [
          "ref",
          "name_en",
          "name_ka",
          "name_ru",
          "frequency",
          "departure_time"
        ]
      }
    }
  }
}


@pytest.fixture(scope="class")
def stations_data():
    with open(STATIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.mark.stations_file
class TestDataStationsFile:

    def test_stations_file_schema(self, stations_data):
        station_validator = fastjsonschema.compile(STATIONS_SCHEMA)
        for station in stations_data:
            try:
                station_validator(station)
            except fastjsonschema.JsonSchemaException as e:
                pytest.fail(f"Станция {station['code']} не соответствует схеме: {e}")