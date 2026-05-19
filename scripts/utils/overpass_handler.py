import requests
from utils.string_utils import *


class OverpassHandler:
    def __init__(self):
        self.base_url = 'https://overpass-api.de/api/interpreter'
        self.base_url_test = 'https://maps.mail.ru/osm/tools/overpass/api/interpreter'

    def get_data(self, query):
        headers = {
            "User-Agent": "georailway",
        }
        result = requests.get(self.base_url, data={"data": query}, headers=headers, timeout=25)
        if result.status_code != 200:
            raise Exception(f"Failed to get data from Overpass API: {result.status_code} {result.text}")
        return result.json()

    def get_route_stations_id(self, route_id):
        stations = []
        data = self.get_data(self.create_route_query(route_id))
        for member in data['elements'][0]['members']:
            if member['role'] == 'stop':
                stations.append(member['ref'])
        return stations

    def get_stations_code(self, stations_id):
        query = self._create_stations_query(stations_id)
        data = self.get_data(query)
        codes = []
        for station_id in stations_id:
            for i in range(len(stations_id)):
                if station_id == data['elements'][i]['id']:
                    if 'tags' in data['elements'][i]:
                        station_name = data['elements'][i]['tags']['name:en']
                        codes.append(make_station_code(station_name))
                    else:
                        codes.append("unknownstation" + " " + str(station_id))
        return codes

    def get_routes_data(self, routes_id):
        query = self._create_routes_query(routes_id)
        return self.get_data(query)

    def get_stations_data(self, stations_id):
        query = self._create_stations_query(stations_id)
        return self.get_data(query)

    def create_route_query(self, route_id):
        return "[out:json][timeout:25];" + "relation(" + str(route_id) + ");" + "out geom;"

    def create_station_query(self, station_id):
        return "[out:json][timeout:25];" + "node(" + str(station_id) + ");" + "out geom;"

    def _create_stations_query(self, station_ids):
        query = "[out:json][timeout:25];("
        for station_id in station_ids:
            query += "node(" + str(station_id) + ");"
        query += ");out geom;"
        return query

    def _create_routes_query(self, routes_id):
        query = "[out:json][timeout:25];("
        for route_id in routes_id:
            query += "relation(" + str(route_id) + ");"
        query += ");out geom;"
        return query