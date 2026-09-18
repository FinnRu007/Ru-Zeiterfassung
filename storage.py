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

MAX_OVERVIEW_WEEKS = 20


def _empty_day():
    return {"begin": "", "end": "", "urlaub": False}


def _empty_week():
    return {"days": {name: _empty_day() for name in WEEKDAYS}}


class Store:
    """Haelt Einstellungen und alle Kalenderwochen im Speicher und schreibt
    sie nach jeder Aenderung als JSON-Datei neben die exe. Jede Woche bleibt
    dauerhaft editierbar (kein Archivieren/Loeschen von Wochen selbst, nur
    ihre Tage lassen sich leeren)."""

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
        weeks = {}
        for key, week in loaded.get("weeks", {}).items():
            days = {name: _empty_day() for name in WEEKDAYS}
            for name in WEEKDAYS:
                days[name].update(week.get("days", {}).get(name, {}))
            weeks[key] = {"days": days}

        return {"settings": settings, "weeks": weeks}

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
    def weeks(self):
        return self.data["weeks"]

    def update_settings(self, **values):
        self.data["settings"].update(values)
        self.save()

    def get_week_days(self, key):
        """Tage einer Woche zum Anzeigen (ohne die Woche anzulegen)."""
        week = self.data["weeks"].get(key)
        return week["days"] if week else {name: _empty_day() for name in WEEKDAYS}

    def update_week_days(self, key, days):
        """Alle Tage einer Woche in einem Schreibvorgang speichern.
        ``days``: {Wochentag: {"begin":.., "end":.., "urlaub":..}}."""
        week = self.data["weeks"].setdefault(key, _empty_week())
        for name, values in days.items():
            week["days"][name] = {
                "begin": values.get("begin", ""),
                "end": values.get("end", ""),
                "urlaub": bool(values.get("urlaub")),
            }
        self.save()

    def clear_week(self, key):
        if key in self.data["weeks"]:
            self.data["weeks"][key] = _empty_week()
            self.save()

    def overview(self):
        """Wochen-Schluessel mit irgendwelchen Daten, neueste zuerst,
        auf MAX_OVERVIEW_WEEKS begrenzt (die Rohdaten bleiben unbegrenzt)."""
        keys_with_data = [
            key for key, week in self.data["weeks"].items()
            if any(
                day.get("begin") or day.get("end") or day.get("urlaub")
                for day in week["days"].values()
            )
        ]
        return sorted(keys_with_data, reverse=True)[:MAX_OVERVIEW_WEEKS]
