"""
Rechenlogik fuer Arbeitszeit, Pause und Lohn - keine UI-Abhaengigkeiten.

Pausenregel: bis ``pause_after_minutes`` Arbeit zaehlt alles als Arbeit.
Danach sind die naechsten ``pause_minutes`` Minuten automatisch Pause statt
Arbeit, die Zeit danach wieder Arbeit.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]

REFERENZ_WOCHEN = 13  # § 11 BUrlG: Bezugszeitraum fuer das Urlaubsentgelt


def week_key(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def week_key_shift(key: str, delta_weeks: int) -> str:
    """Kalenderwochen-Schluessel um ``delta_weeks`` verschieben (jahresuebergreifend)."""
    year_text, week_text = key.split("-W")
    monday = date.fromisocalendar(int(year_text), int(week_text), 1)
    return week_key(monday + timedelta(weeks=delta_weeks))


def week_label(key: str) -> str:
    year_text, week_text = key.split("-W")
    return f"KW {int(week_text)} · {year_text}"


def parse_time(text):
    """'HH:MM' -> Minuten seit Mitternacht, oder None wenn leer/ungueltig."""
    text = (text or "").strip()
    if not text or ":" not in text:
        return None
    parts = text.split(":")
    if len(parts) != 2:
        return None
    try:
        hours, minutes = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 60 + minutes


def format_duration(minutes):
    minutes = max(0, round(minutes))
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}min" if h else f"{m}min"


def format_clock(minutes):
    minutes = round(minutes) % (24 * 60)
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def format_money(amount):
    text = f"{amount:,.2f}"
    text = text.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{text} €"


def split_work_and_break(elapsed_minutes, pause_after_minutes, pause_minutes):
    """Verstrichene Uhrzeit-Spanne -> (Arbeitsminuten, Pausenminuten)."""
    if elapsed_minutes <= pause_after_minutes:
        return elapsed_minutes, 0
    if elapsed_minutes <= pause_after_minutes + pause_minutes:
        return pause_after_minutes, elapsed_minutes - pause_after_minutes
    return elapsed_minutes - pause_minutes, pause_minutes


def elapsed_for_target_work(target_work_minutes, pause_after_minutes, pause_minutes):
    """Umkehrung von split_work_and_break: welche Uhrzeit-Spanne liefert genau
    ``target_work_minutes`` Netto-Arbeit (inklusive der Pause auf dem Weg)?"""
    target_work_minutes = max(0, target_work_minutes)
    if target_work_minutes <= pause_after_minutes:
        return target_work_minutes
    return target_work_minutes + pause_minutes


@dataclass
class DayResult:
    name: str
    begin_text: str = ""
    end_text: str = ""
    is_urlaub: bool = False
    error: Optional[str] = None
    complete: bool = False
    work_minutes: int = 0
    break_minutes: int = 0
    suggested_end_minutes: Optional[int] = None


@dataclass
class WeekResult:
    days: list = field(default_factory=list)
    total_work_minutes: int = 0
    remaining_week_minutes: int = 0
    earned_so_far: float = 0.0
    earned_projected: Optional[float] = None
    urlaub_days: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class UrlaubsentgeltResult:
    tagessatz: Optional[float] = None   # durchschnittl. Tagesverdienst der Referenzwochen
    basis_tage: int = 0                 # Anzahl Arbeitstage, auf die sich der Satz stuetzt
    basis_wochen: int = 0               # Anzahl Wochen mit Daten im Referenzzeitraum
    urlaubstage: int = 0                # Urlaubstage in der betrachteten Woche
    betrag: float = 0.0                 # tagessatz * urlaubstage


def compute_week(day_inputs, settings):
    """day_inputs: {Wochentag: {"begin": str, "end": str}}.
    settings: dict mit stundenlohn, wochenMaxStunden, tagesMaxStunden,
    pauseAbStunden, pauseDauerMinuten (siehe storage.DEFAULT_SETTINGS)."""
    pause_after = round(settings["pauseAbStunden"] * 60)
    pause_minutes = round(settings["pauseDauerMinuten"])
    daily_max = round(settings["tagesMaxStunden"] * 60)
    weekly_max = round(settings["wochenMaxStunden"] * 60)
    wage = settings["stundenlohn"]

    days = []
    errors = []
    warnings = []
    total_work = 0

    urlaub_days = 0
    for name in WEEKDAYS:
        raw = day_inputs.get(name, {})
        is_urlaub = bool(raw.get("urlaub"))
        begin_text = "" if is_urlaub else (raw.get("begin") or "").strip()
        end_text = "" if is_urlaub else (raw.get("end") or "").strip()
        day = DayResult(name=name, begin_text=begin_text, end_text=end_text, is_urlaub=is_urlaub)

        if is_urlaub:
            urlaub_days += 1
            days.append(day)
            continue

        if not begin_text and not end_text:
            days.append(day)
            continue

        begin_minutes = parse_time(begin_text)
        end_minutes = parse_time(end_text)

        if begin_text and begin_minutes is None:
            day.error = f"{name}: Beginn „{begin_text}“ ist keine gueltige Uhrzeit (HH:MM)."
        elif end_text and end_minutes is None:
            day.error = f"{name}: Ende „{end_text}“ ist keine gueltige Uhrzeit (HH:MM)."
        elif end_text and not begin_text:
            day.error = f"{name}: Ende eingetragen, aber kein Beginn."
        elif begin_minutes is not None and end_minutes is not None:
            elapsed = end_minutes - begin_minutes
            if elapsed <= 0:
                day.error = f"{name}: Ende muss nach Beginn liegen."
            else:
                work, brk = split_work_and_break(elapsed, pause_after, pause_minutes)
                day.complete = True
                day.work_minutes = work
                day.break_minutes = brk
                total_work += work
                if work > daily_max:
                    warnings.append(
                        f"{name}: Tagesmaximum überschritten "
                        f"({format_duration(work)} von {format_duration(daily_max)})."
                    )

        if day.error:
            errors.append(day.error)
        days.append(day)

    remaining_week = weekly_max - total_work
    earned_so_far = (total_work / 60) * wage

    earned_projected = None
    for day in days:
        if day.error or day.complete:
            continue
        begin_minutes = parse_time(day.begin_text)
        if begin_minutes is None:
            continue
        allowed = max(0, min(daily_max, remaining_week))
        elapsed = elapsed_for_target_work(allowed, pause_after, pause_minutes)
        day.suggested_end_minutes = begin_minutes + elapsed
        if earned_projected is None:
            earned_projected = earned_so_far
        earned_projected += (allowed / 60) * wage

    if total_work > weekly_max:
        warnings.append(
            f"Wochenmaximum überschritten ({format_duration(total_work)} von "
            f"{format_duration(weekly_max)})."
        )

    return WeekResult(
        days=days,
        total_work_minutes=total_work,
        remaining_week_minutes=remaining_week,
        earned_so_far=earned_so_far,
        earned_projected=earned_projected,
        urlaub_days=urlaub_days,
        errors=errors,
        warnings=warnings,
    )


def compute_urlaubsentgelt(weeks_data, target_week_key, settings):
    """Urlaubsentgelt nach § 11 BUrlG: durchschnittlicher Tagesverdienst der
    letzten 13 Wochen vor der betrachteten Woche (nur tatsaechlich
    gearbeitete Tage, unbezahlte/Urlaubstage zaehlen nicht in die Basis),
    multipliziert mit den Urlaubstagen der betrachteten Woche.

    Vereinfachung gegenueber dem Gesetzestext: keine Sonderbehandlung von
    Ueberstundenzuschlaegen oder Kurzarbeit, da dieser Rechner nur einen
    einzigen, flachen Stundenlohn kennt.
    """
    pause_after = round(settings["pauseAbStunden"] * 60)
    pause_minutes = round(settings["pauseDauerMinuten"])
    wage = settings["stundenlohn"]

    total_earned = 0.0
    total_days = 0
    weeks_used = 0

    for offset in range(1, REFERENZ_WOCHEN + 1):
        key = week_key_shift(target_week_key, -offset)
        week = weeks_data.get(key)
        if not week:
            continue
        found_in_week = False
        for name in WEEKDAYS:
            day = week.get("days", {}).get(name, {})
            if day.get("urlaub"):
                continue
            begin_minutes = parse_time(day.get("begin", ""))
            end_minutes = parse_time(day.get("end", ""))
            if begin_minutes is None or end_minutes is None or end_minutes <= begin_minutes:
                continue
            work, _ = split_work_and_break(end_minutes - begin_minutes, pause_after, pause_minutes)
            total_earned += (work / 60) * wage
            total_days += 1
            found_in_week = True
        if found_in_week:
            weeks_used += 1

    target_week = weeks_data.get(target_week_key, {})
    urlaubstage = sum(
        1 for name in WEEKDAYS
        if target_week.get("days", {}).get(name, {}).get("urlaub")
    )

    tagessatz = (total_earned / total_days) if total_days else None
    betrag = (tagessatz * urlaubstage) if tagessatz is not None else 0.0

    return UrlaubsentgeltResult(
        tagessatz=tagessatz,
        basis_tage=total_days,
        basis_wochen=weeks_used,
        urlaubstage=urlaubstage,
        betrag=betrag,
    )
