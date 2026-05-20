import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_SCHEDULE_PATH = os.path.join(PROJECT_ROOT, 'data', 'local_schedule.json')
ROUTES_LIST_JS_PATH = os.path.join(PROJECT_ROOT, 'static', 'js', 'components', 'route', 'routes-list.js')
ROUTES_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'routes.json')
STATIONS_LIST_JS_PATH = os.path.join(PROJECT_ROOT, 'static', 'js', 'components', 'station', 'stations-list.js')
STATIONS_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'stations.json')
ROUTES_GEODATA_DIR = os.path.join(PROJECT_ROOT, 'static', 'data', 'routes_geodata')
ROUTES_REFS_FOR_PARSING = []
RAILWAY_NETWORK_JS_PATH = os.path.join(PROJECT_ROOT, 'static', 'js', 'components', 'railway-network', 'railway-network-data.js')