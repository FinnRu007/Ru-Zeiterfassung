import json
import os

from berechnung import WEEKDAYS
from config import DATA_DIR, DATA_PATH

DEFAULT_SETTINGS = {
    "stundenlohn": 0.0,
    "wochenMaxStunden": 40.0,
    "tagesMaxStunden": 8.0,
    "pauseAbStunden": 6.0,
    "pauseDauerMinuten": 45,
}

MAX_HISTORY = 12


def _empty_week():
    return {name: {"begin": "", "end": ""} for name in WEEKDAYS}


class Store:
    """Haelt Einstellungen, aktuelle Woche und Verlauf im Speicher und
    schreibt sie nach jeder Aenderung als JSON-Datei neben die exe."""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        loaded = {}
        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except (json.JSONDecodeError, OSError):
                loaded = {}

        settings = {**DEFAULT_SETTINGS, **loaded.get("settings", {})}
        week = _empty_week()
        for name in WEEKDAYS:
            week[name].update(loaded.get("week", {}).get(name, {}))
        history = loaded.get("history", [])
        if not isinstance(history, list):
            history = []

        return {"settings": settings, "week": week, "history": history}

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp_path = DATA_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DATA_PATH)

    @property
    def settings(self):
        return self.data["settings"]

    @property
    def week(self):
        return self.data["week"]

    @property
    def history(self):
        return self.data["history"]

    def update_settings(self, **values):
        self.data["settings"].update(values)
        self.save()

    def update_day(self, name, begin, end):
        self.data["week"][name] = {"begin": begin, "end": end}
        self.save()

    def finish_week(self, label, work_minutes, earned):
        self.data["history"].insert(0, {
            "label": label,
            "workMinutes": work_minutes,
            "earned": earned,
        })
        self.data["history"] = self.data["history"][:MAX_HISTORY]
        self.data["week"] = _empty_week()
        self.save()

    def remove_history_entry(self, index):
        if 0 <= index < len(self.data["history"]):
            self.data["history"].pop(index)
            self.save()
