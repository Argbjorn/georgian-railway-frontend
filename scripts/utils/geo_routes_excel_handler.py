import os
import json
from pathlib import Path

# для Google Sheets
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# Strip whitespace/quotes — env can have trailing newline when set from CI
SPREADSHEET_ID = (os.environ.get("GOOGLE_SPREADSHEET_ID") or "").strip().strip('"')


def _get_google_client():
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not credentials_path:
        raise RuntimeError("GOOGLE_CREDENTIALS_PATH is not set")
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _rows_to_records(rows):
    """Преобразует список строк (из API) в список словарей по первой строке как заголовкам.
    Пустые ячейки в конце строки API может не возвращать — дополняем их пустой строкой."""
    if not rows:
        return []
    headers = rows[0]
    result = []
    for row in rows[1:]:
        padded = list(row) + [""] * (len(headers) - len(row))
        result.append(dict(zip(headers, padded[: len(headers)])))
    return result


class GeoRoutesExcelHandler:
    def __init__(self):
        self._sheet_cache = {}
        if not SPREADSHEET_ID:
            raise RuntimeError(
                "GOOGLE_SPREADSHEET_ID is not set. "
                "Set the env var or add it to .env; in CI use the GOOGLE_SPREADSHEET_ID secret."
            )
        client = _get_google_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheets = spreadsheet.worksheets()
        if not worksheets:
            self.routes_json = []
            return
        ranges = [f"'{ws.title}'!A:Z" for ws in worksheets]
        batch = spreadsheet.values_batch_get(ranges)
        value_ranges = batch.get("valueRanges", [])
        for i, ws in enumerate(worksheets):
            rows = value_ranges[i].get("values", []) if i < len(value_ranges) else []
            self._sheet_cache[ws.title] = _rows_to_records(rows)
        self.routes_json = self._sheet_cache.get("routes", [])

    def _get_cached_sheet_data(self, sheet_name):
        """Возвращает данные листа из локального кэша (без обращений к API)."""
        return self._sheet_cache.get(str(sheet_name), [])

    def _get_json_from_sheet(self, sheet_name):
        return self._get_cached_sheet_data(sheet_name)

    def is_sheet_exists(self, sheet_name):
        return str(sheet_name) in self._sheet_cache

    def get_route_osm_id(self, route_ref):
        for route in self.routes_json:
            if route.get("ref") == int(route_ref) or route.get("ref") == route_ref:
                return route["id"]
        raise ValueError(f"There's no route number {route_ref}")

    def get_all_routes_osm_id(self, show_on_site_only=False):
        if show_on_site_only:
            return [route["id"] for route in self.routes_json if route.get("show_on_site") == "y"]
        return [route["id"] for route in self.routes_json]

    def get_all_routes_ref(self):
        return [route["ref"] for route in self.routes_json]

    def get_all_active_routes_ref(self):
        return [route["ref"] for route in self.routes_json if route.get("active") == "y"]

    def get_route_stations(self, route_ref):
        if self.is_sheet_exists(route_ref):
            sheet_json = self._get_cached_sheet_data(route_ref)
            return [station["station"] for station in sheet_json]
        raise ValueError(f"There's no route number {route_ref}")

    def get_route_stations_with_time(self, route_ref):
        if self.is_sheet_exists(route_ref):
            return self._get_cached_sheet_data(route_ref)
        raise ValueError(f"There's no route number {route_ref}")