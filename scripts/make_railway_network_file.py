import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RAILWAY_NETWORK_JS_PATH
from utils.overpass_handler import OverpassHandler

QUERY = """[out:json][timeout:25];
( area[name="საქართველო"]; )->.searchArea;
nwr["railway"="rail"]["usage"!="industrial"]["service"!="spur"]["service"!="yard"]["service"!="siding"](area.searchArea);
out geom;"""

OUTPUT_PATH = RAILWAY_NETWORK_JS_PATH

overpass = OverpassHandler()


def overpass_to_geojson(data):
    features = []
    for element in data.get('elements', []):
        el_type = element.get('type')
        el_id = element.get('id')
        properties = {"@id": f"{el_type}/{el_id}"}
        properties.update(element.get('tags', {}))

        if el_type == 'node':
            lat, lon = element.get('lat'), element.get('lon')
            if lat is None or lon is None:
                continue
            geometry = {"type": "Point", "coordinates": [lon, lat]}

        elif el_type == 'way':
            geom = element.get('geometry', [])
            if not geom:
                continue
            coords = [[p['lon'], p['lat']] for p in geom]
            geometry = {"type": "LineString", "coordinates": coords}

        elif el_type == 'relation':
            lines = []
            for member in element.get('members', []):
                if member.get('type') == 'way' and 'geometry' in member:
                    coords = [[p['lon'], p['lat']] for p in member['geometry']]
                    if coords:
                        lines.append(coords)
            if not lines:
                continue
            geometry = {"type": "MultiLineString", "coordinates": lines}

        else:
            continue

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    return {"type": "FeatureCollection", "features": features}


def update_file(data):
    geojson = overpass_to_geojson(data)
    content = "export const railwayNetworkData = " + json.dumps(geojson, ensure_ascii=False, indent=2)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"railway-network-data.js updated")


if __name__ == '__main__':
    data = overpass.get_data(QUERY)
    update_file(data)
