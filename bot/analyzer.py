"""
Dua lapis analisa:
1. rule_based_bias()  -> instan, gratis, bandingkan actual vs forecast/previous secara matematis.
2. ai_market_commentary() -> panggil Claude (atau OpenAI) untuk narasi analisa pasar yang lebih natural,
   memakai hasil rule-based sebagai konteks supaya tidak ngarang.

Disclaimer penting: ini heuristik sederhana untuk konteks edukasi/informasi,
BUKAN sinyal trading atau saran finansial.
"""

import re

import requests

from . import config

# Indikator yang sifatnya "semakin kecil semakin bagus" untuk mata uang terkait
# (kebalikan dari indikator umum seperti GDP/NFP/Retail Sales/PMI yang "semakin besar semakin bagus").
INVERSE_KEYWORDS = [
    "unemployment",
    "jobless claims",
    "claims",
    "deficit",
    "default",
]


def _to_number(value):
    """Ubah string seperti '4.2%', '175K', '1.2M' jadi float. Return None kalau gagal."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in ("n/a", "na", "-", "tentative"):
        return None

    multiplier = 1
    if text.endswith("%"):
        text = text[:-1]
    elif text[-1:].upper() == "K":
        multiplier = 1_000
        text = text[:-1]
    elif text[-1:].upper() == "M":
        multiplier = 1_000_000
        text = text[:-1]
    elif text[-1:].upper() == "B":
        multiplier = 1_000_000_000
        text = text[:-1]

    text = text.replace(",", "").strip()
    # buang karakter selain digit, titik, dan minus (jaga-jaga ada simbol aneh di feed)
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in ("", "-", "."):
        return None
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def rule_based_bias(event):
    """Bandingkan actual vs forecast/previous, hasilkan bias kasar: bullish/bearish/neutral."""
    actual = _to_number(event.get("actual"))
    forecast = _to_number(event.get("forecast"))
    previous = _to_number(event.get("previous"))

    if actual is None:
        return {
            "verdict": "no_data",
            "actual": None,
            "forecast": forecast,
            "previous": previous,
            "vs_previous": None,
            "is_inverse_indicator": False,
            "explanation": "Data actual belum tersedia di feed.",
        }

    title_lower = (event.get("title") or "").lower()
    is_inverse = any(k in title_lower for k in INVERSE_KEYWORDS)

    verdict = "neutral"
    explanation_parts = []

    if forecast is not None and actual != forecast:
        beat_forecast = actual > forecast
        if beat_forecast:
            verdict = "bearish" if is_inverse else "bullish"
            explanation_parts.append("actual lebih tinggi dibanding forecast")
        else:
            verdict = "bullish" if is_inverse else "bearish"
            explanation_parts.append("actual lebih rendah dibanding forecast")
    elif forecast is not None:
        explanation_parts.append("actual sama dengan forecast")

    vs_previous = None
    if previous is not None:
        if actual > previous:
            vs_previous = "naik dari periode sebelumnya"
        elif actual < previous:
            vs_previous = "turun dari periode sebelumnya"
        else:
            vs_previous = "stabil dari periode sebelumnya"
        explanation_parts.append(vs_previous)

    return {
        "verdict": verdict,
        "actual": actual,
        "forecast": forecast,
        "previous": previous,
        "vs_previous": vs_previous,
        "is_inverse_indicator": is_inverse,
        "explanation": ", ".join(explanation_parts) if explanation_parts else "Tidak ada pembanding.",
    }


def _build_prompt(event, rb):
    return f"""Kamu adalah analis pasar forex. Sebuah data ekonomi baru saja rilis hari ini, berikut datanya:

Nama event: {event.get('title')}
Mata uang/negara terdampak: {event.get('country')}
Actual: {event.get('actual')}
Forecast: {event.get('forecast')}
Previous: {event.get('previous')}
Hasil perbandingan otomatis: {rb.get('explanation')} (bias awal: {rb.get('verdict')})

Tulis analisa pasar singkat dalam Bahasa Indonesia (3-4 kalimat, maksimal sekitar 100 kata, dalam bentuk paragraf tanpa bullet point) yang mencakup:
- Apa makna hasil ini dibanding ekspektasi pasar
- Pair mata uang mana yang paling perlu diperhatikan dan kecenderungan arah pergerakannya untuk sisa hari ini
- Satu catatan kewaspadaan (misalnya volatilitas, event lain yang masih ditunggu hari ini, atau risiko pembalikan arah)

Jangan memberi sinyal beli/jual eksplisit atau target harga, cukup gambaran analisa kondisi pasar."""


def ai_market_commentary(event, rb):
    """Panggil LLM (Anthropic atau OpenAI sesuai config.AI_PROVIDER) untuk narasi analisa.
    Return string kosong kalau provider dimatikan / key tidak diset / request gagal."""
    provider = config.AI_PROVIDER
    prompt = _build_prompt(event, rb)

    try:
        if provider == "gemini" and config.GEMINI_API_KEY:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent",
                headers={
                    "x-goog-api-key": config.GEMINI_API_KEY,
                    "content-type": "application/json",
                },
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts).strip()

        if provider == "groq" and config.GROQ_API_KEY:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.GROQ_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": config.GROQ_MODEL,
                    "max_tokens": 350,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        if provider == "anthropic" and config.ANTHROPIC_API_KEY:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": config.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": config.ANTHROPIC_MODEL,
                    "max_tokens": 350,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            return "\n".join(texts).strip()

        if provider == "openai" and config.OPENAI_API_KEY:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": config.OPENAI_MODEL,
                    "max_tokens": 350,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    except Exception as exc:  # noqa: BLE001
        return f"_(Analisa AI gagal dimuat: {exc})_"

    return ""
