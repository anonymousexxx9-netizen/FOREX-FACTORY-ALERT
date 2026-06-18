"""
Konfigurasi bot, semua nilai diambil dari environment variable supaya
tidak ada kredensial yang ter-hardcode di kode maupun ter-commit ke GitHub.
"""

import os

# --- Wajib diisi ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Untuk analisa AI (opsional, tapi disarankan) ---
# Pilihan: "gemini" / "groq" (gratis, tanpa kartu kredit) | "anthropic" / "openai" (berbayar) | "none" (matikan)
AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()

# Gratis - Google AI Studio (aistudio.google.com), tanpa kartu kredit
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Gratis - GroqCloud (console.groq.com), tanpa kartu kredit, inference sangat cepat
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Berbayar (opsional, kalau mau kualitas reasoning lebih tinggi)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# --- Pengaturan umum ---
TZ_NAME = os.environ.get("TZ_NAME", "Asia/Jakarta")
DAILY_AGENDA_HOUR = int(os.environ.get("DAILY_AGENDA_HOUR", "6"))
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
MIN_IMPACT = os.environ.get("MIN_IMPACT", "High")  # filter: hanya event dengan impact ini

# Sumber data kalender (feed publik yang dipakai banyak widget Forex Factory).
# Ada juga endpoint cdn- sebagai fallback bila endpoint utama kena rate-limit.
CALENDAR_URLS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json",
]


def validate():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        raise RuntimeError(
            "Environment variable berikut belum diset: " + ", ".join(missing)
        )
