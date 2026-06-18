"""
Test logika bot secara offline pakai data palsu (mock), tanpa perlu token Telegram
asli atau koneksi internet. Jalankan: python3 test_offline.py

Berguna untuk verifikasi alur sebelum setup credential asli.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "dummy-chat-id")
os.environ.setdefault("AI_PROVIDER", "none")  # tidak perlu API key buat test ini
os.environ["STATE_FILE"] = "state.test.json"
os.environ["DAILY_AGENDA_HOUR"] = "0"

from bot import calendar_fetcher, telegram_sender  # noqa: E402
import main  # noqa: E402

TZ = ZoneInfo("Asia/Jakarta")
NOW = datetime.now(TZ)

FAKE_RAW_EVENTS = [
    {
        "title": "Non-Farm Payrolls",
        "country": "USD",
        "date": (NOW - timedelta(minutes=30)).astimezone(ZoneInfo("UTC")).isoformat(),
        "impact": "High",
        "forecast": "180K",
        "previous": "150K",
        "actual": "225K",
    },
    {
        "title": "Unemployment Rate",
        "country": "USD",
        "date": (NOW - timedelta(minutes=15)).astimezone(ZoneInfo("UTC")).isoformat(),
        "impact": "High",
        "forecast": "4.0%",
        "previous": "3.9%",
        "actual": "4.2%",
    },
    {
        "title": "Retail Sales m/m",
        "country": "GBP",
        "date": (NOW + timedelta(hours=2)).astimezone(ZoneInfo("UTC")).isoformat(),
        "impact": "High",
        "forecast": "0.3%",
        "previous": "0.1%",
        "actual": "",  # belum rilis
    },
    {
        "title": "Some Low Impact Thing",
        "country": "EUR",
        "date": NOW.astimezone(ZoneInfo("UTC")).isoformat(),
        "impact": "Low",
        "forecast": "",
        "previous": "",
        "actual": "",
    },
]

sent_messages = []


def fake_send_message(token, chat_id, text):
    sent_messages.append(text)
    print("=" * 60)
    print(text)
    print("=" * 60)
    return {"ok": True}


if os.path.exists("state.test.json"):
    os.remove("state.test.json")

with mock.patch.object(calendar_fetcher, "fetch_calendar_raw", return_value=FAKE_RAW_EVENTS), \
     mock.patch.object(telegram_sender, "send_message", side_effect=fake_send_message), \
     mock.patch("main.telegram_sender.send_message", side_effect=fake_send_message):
    main.run()

print(f"\nTotal pesan terkirim (mock): {len(sent_messages)}")
assert len(sent_messages) >= 2, "Harus ada minimal agenda + 1 alert hasil"

with open("state.test.json") as f:
    state = json.load(f)
print("\nIsi state.test.json setelah run pertama:")
print(json.dumps(state, indent=2, ensure_ascii=False))
assert len(state["alerted_results"]) == 2, "NFP dan Unemployment Rate harus tercatat sudah dialert"

# Run kedua dengan data SAMA -> seharusnya tidak ada alert baru (anti-duplikat)
sent_messages.clear()
with mock.patch.object(calendar_fetcher, "fetch_calendar_raw", return_value=FAKE_RAW_EVENTS), \
     mock.patch("main.telegram_sender.send_message", side_effect=fake_send_message):
    main.run()

assert len(sent_messages) == 0, "Run kedua tidak boleh mengirim alert duplikat"
print("\n[PASS] Anti-duplikat bekerja: run kedua tidak mengirim ulang.")

os.remove("state.test.json")
print("\nSEMUA TEST OFFLINE BERHASIL ✅")
