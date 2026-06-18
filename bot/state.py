"""
State sederhana berbasis file JSON, supaya bot tidak mengirim alert
yang sama dua kali setiap kali workflow/cron jalan lagi.
"""

import json
import os


DEFAULT_STATE = {
    "agenda_sent_date": None,   # tanggal terakhir agenda harian dikirim (YYYY-MM-DD)
    "alerted_results": [],      # daftar key event yang sudah dikirim hasil + analisanya
}


def load_state(path):
    if not os.path.exists(path):
        return dict(DEFAULT_STATE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_STATE)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATE)


def save_state(path, state):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def event_key(event):
    """Key unik untuk satu event (negara + judul + waktu rilis)."""
    return f"{event.get('country')}|{event.get('title')}|{event.get('date')}"


def prune_old_keys(state, current_event_keys):
    """Buang key event lama yang sudah tidak ada di feed minggu ini,
    supaya file state.json tidak terus membesar."""
    current = set(current_event_keys)
    state["alerted_results"] = [k for k in state.get("alerted_results", []) if k in current]
    return state
