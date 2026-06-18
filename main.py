"""
Entry point bot. Didesain untuk dijalankan SEKALI per eksekusi (cocok untuk
cron / GitHub Actions schedule), bukan proses yang nyala terus-menerus.

Setiap kali dijalankan, bot akan:
1. Ambil economic calendar (filter: hanya impact High, hanya hari ini).
2. Kalau belum pernah, kirim agenda harian (sekali per hari, setelah jam DAILY_AGENDA_HOUR).
3. Untuk setiap event yang waktunya sudah lewat dan actual-nya sudah terisi,
   tapi belum pernah dikirim -> kirim alert hasil + analisa (rule-based + AI), lalu catat di state.
"""

import sys
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv()  # tidak melakukan apa pun kalau file .env tidak ada (misal di GitHub Actions)
except ImportError:
    pass

from bot import config, calendar_fetcher, analyzer, telegram_sender, state as state_mod


def run():
    config.validate()

    tz = ZoneInfo(config.TZ_NAME)
    now = datetime.now(tz)
    today_str = now.date().isoformat()

    state = state_mod.load_state(config.STATE_FILE)

    today_events = calendar_fetcher.get_today_high_impact_events()
    current_keys = [state_mod.event_key(e) for e in today_events]
    state = state_mod.prune_old_keys(state, current_keys)

    # 1) Agenda harian (sekali per hari)
    if state.get("agenda_sent_date") != today_str and now.hour >= config.DAILY_AGENDA_HOUR:
        msg = telegram_sender.format_daily_agenda(today_events, config.TZ_NAME)
        telegram_sender.send_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, msg)
        state["agenda_sent_date"] = today_str
        state_mod.save_state(config.STATE_FILE, state)
        print(f"[OK] Agenda harian terkirim ({len(today_events)} event).")

    # 2) Alert hasil + analisa untuk event yang sudah rilis
    alerted = set(state.get("alerted_results", []))
    sent_count = 0

    for event in sorted(today_events, key=lambda x: x["datetime_local"]):
        key = state_mod.event_key(event)
        if key in alerted:
            continue
        if event["datetime_local"] > now:
            continue  # belum waktunya rilis
        if not event.get("actual"):
            continue  # sudah lewat waktu tapi actual belum keluar di feed, tunggu run berikutnya

        rb = analyzer.rule_based_bias(event)
        ai_text = analyzer.ai_market_commentary(event, rb)

        msg = telegram_sender.format_result_alert(event, rb, ai_text)
        telegram_sender.send_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, msg)

        alerted.add(key)
        state["alerted_results"] = sorted(alerted)
        state_mod.save_state(config.STATE_FILE, state)
        sent_count += 1
        print(f"[OK] Alert terkirim: {event.get('title')} ({event.get('country')})")

    if sent_count == 0:
        print("[INFO] Tidak ada event baru yang perlu dialert saat ini.")


if __name__ == "__main__":
    try:
        run()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
