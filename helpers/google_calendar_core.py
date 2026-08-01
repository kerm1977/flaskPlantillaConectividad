from urllib.parse import quote
from datetime import datetime, timedelta


def _parse_date_str(value):
    if not value:
        return None
    if isinstance(value, str):
        if '/' in value:
            parts = value.split('/')
            if len(parts) == 3:
                return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        elif '-' in value:
            parts = value.split('-')
            if len(parts) == 3:
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    return value


def _format_dates(start_date, end_date=None):
    if start_date and not end_date:
        end_date = start_date + timedelta(days=1)
    start_str = start_date.strftime("%Y%m%dT000000") if start_date else ""
    end_str = end_date.strftime("%Y%m%dT000000") if end_date else ""
    return start_str, end_str


def build_google_calendar_url(title, start_date, end_date, description_parts, location=""):
    start_str, end_str = _format_dates(start_date, end_date)
    description = "\n\n".join(description_parts)
    base_url = "https://www.google.com/calendar/render"
    params = {
        "action": "TEMPLATE",
        "text": quote(title),
        "dates": f"{start_str}/{end_str}" if start_str and end_str else "",
        "details": quote(description),
        "location": quote(location),
        "rem": "popup:P7D,popup:P2D",
        "ctz": "America/Costa_Rica"
    }
    params = {k: v for k, v in params.items() if v}
    return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
