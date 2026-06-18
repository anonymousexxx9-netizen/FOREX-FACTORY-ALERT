"""Kirim pesan ke Telegram + helper format pesan."""

import requests


def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    if not resp.ok:
        # Tampilkan body error Telegram supaya mudah didebug (misal token salah, parse error, dll)
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text}")
    return resp.json()


VERDICT_EMOJI = {
    "bullish": "🟢",
    "bearish": "🔴",
    "neutral": "⚪",
    "no_data": "⚪",
}

VERDICT_LABEL_ID = {
    "bullish": "cenderung BULLISH untuk mata uang ini",
    "bearish": "cenderung BEARISH untuk mata uang ini",
    "neutral": "NETRAL, sesuai ekspektasi",
    "no_data": "data belum lengkap",
}


def format_daily_agenda(events, tz_name):
    if not events:
        return (
            "🗓️ *Agenda Forex High Impact Hari Ini*\n\n"
            "Tidak ada event high-impact terjadwal hari ini. Pasar kemungkinan relatif tenang, "
            "tapi tetap waspada terhadap berita mendadak (unscheduled news).\n\n"
            "_Bot akan tetap memantau dan mengirim alert bila ada perubahan._"
        )

    lines = ["🗓️ *Agenda Forex High Impact Hari Ini*\n"]
    for e in sorted(events, key=lambda x: x["datetime_local"]):
        jam = e["datetime_local"].strftime("%H:%M")
        lines.append(
            f"🔴 *{jam}* — {e.get('country')}: {e.get('title')}\n"
            f"     Forecast: `{e.get('forecast') or '-'}`  Previous: `{e.get('previous') or '-'}`"
        )
    lines.append("\n_Alert + analisa otomatis akan dikirim begitu masing-masing data rilis._")
    return "\n".join(lines)


def format_result_alert(event, rb, ai_text):
    emoji = VERDICT_EMOJI.get(rb["verdict"], "⚪")
    label = VERDICT_LABEL_ID.get(rb["verdict"], "")
    jam = event["datetime_local"].strftime("%H:%M")

    parts = [
        "🚨 *HIGH IMPACT NEWS RILIS*",
        f"🕒 {jam} WIB\n",
        f"*{event.get('title')}* ({event.get('country')})",
        f"Actual: `{event.get('actual') or '-'}`   "
        f"Forecast: `{event.get('forecast') or '-'}`   "
        f"Previous: `{event.get('previous') or '-'}`",
        f"\n{emoji} *Bias awal (otomatis):* {label}",
    ]

    if ai_text:
        parts.append(f"\n🧠 *Analisa Market Hari Ini:*\n{ai_text}")

    parts.append(
        "\n_⚠️ Ini analisa otomatis untuk edukasi, bukan saran finansial. "
        "Selalu cek konfirmasi price action sebelum mengambil keputusan trading._"
    )
    return "\n".join(parts)
