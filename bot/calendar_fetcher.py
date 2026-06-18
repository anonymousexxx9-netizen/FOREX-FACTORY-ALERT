"""
Mengambil data economic calendar dari feed publik Forex Factory
(format JSON yang sama dipakai banyak widget/indicator MT4/MT5).

Catatan: ini adalah feed tidak resmi (unofficial). Forex Factory membatasi
maksimal sekitar 2 request / 5 menit per IP untuk endpoint export ini,
jadi jangan polling terlalu sering (interval 10-15 menit sudah lebih dari aman).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from . import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_calendar_raw():
    """Ambil JSON mentah, coba beberapa URL fallback bila salah satu gagal/limit."""
    last_error = None
    for url in config.CALENDAR_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            last_error = RuntimeError(f"Response bukan list JSON dari {url}")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise RuntimeError(f"Gagal mengambil calendar dari semua sumber: {last_error}")


def parse_events(raw_events, tz_name=None):
    """Tambahkan field datetime_local (timezone-aware) ke setiap event."""
    tz = ZoneInfo(tz_name or config.TZ_NAME)
    parsed = []
    for e in raw_events:
        raw_date = e.get("date")
        if not raw_date:
            continue
        try:
            dt = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
        except ValueError:
            continue
        e = dict(e)  # jangan mutasi objek asli
        e["datetime_local"] = dt.astimezone(tz)
        parsed.append(e)
    return parsed


def filter_high_impact(events, min_impact=None):
    target = (min_impact or config.MIN_IMPACT).lower()
    return [e for e in events if str(e.get("impact", "")).lower() == target]


def events_for_today(events, tz_name=None):
    tz = ZoneInfo(tz_name or config.TZ_NAME)
    today = datetime.now(tz).date()
    return [e for e in events if e["datetime_local"].date() == today]


def get_today_high_impact_events(tz_name=None, min_impact=None):
    """Helper utama: fetch -> parse -> filter impact -> filter hari ini."""
    raw = fetch_calendar_raw()
    parsed = parse_events(raw, tz_name)
    high_impact = filter_high_impact(parsed, min_impact)
    return events_for_today(high_impact, tz_name)
