"""
Zeiten Berechnen — Arbeitszeit, Pausen und Wochenlohn.

Stundenlohn, Wochen- und Tagesmaximum sowie eine Pausenregel einstellen,
dann pro Wochentag Beginn und Ende eintragen. Fehlt an einem Tag das Ende,
schlägt das Programm die Feierabend-Zeit vor.

Oberfläche nach dem Ru-Services-Designsystem (theme.py / widgets.py).

Autor: Finn Rummel
"""

import os
import sys
from datetime import date

import customtkinter as ctk

import theme as t
import widgets as w
import berechnung as calc
from berechnung import WEEKDAYS
from storage import Store


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


SETTING_FIELDS = [
    ("stundenlohn", "Stundenlohn (€)", "z. B. 14,50"),
    ("wochenMaxStunden", "Maximale Wochenarbeitszeit (h)", "z. B. 40"),
    ("tagesMaxStunden", "Maximale Tagesarbeitszeit (h)", "z. B. 8"),
    ("pauseAbStunden", "Pause ab (Stunden Arbeit)", "z. B. 6"),
    ("pauseDauerMinuten", "Pausendauer (Minuten)", "z. B. 45"),
]

SETTING_MINIMUMS = {
    "stundenlohn": 0,
    "wochenMaxStunden": 0.01,
    "tagesMaxStunden": 0.01,
    "pauseAbStunden": 0,
    "pauseDauerMinuten": 0,
}


def format_number(value):
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return str(value).replace(".", ",")


def parse_number(text):
    return float(text.strip().replace(",", "."))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.store = Store()
        self.setting_entries = {}
        self.day_rows = {}
        self.last_result = None

        self.title("Zeiten Berechnen")
        self._place_window()
        self.minsize(760, 600)
        self.configure(fg_color=t.BG)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self._build_ui()
        self._load_from_store()
        self._calculate()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- Fenster
    def _place_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1000, screen_w - 80)
        height = min(820, screen_h - 80)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ----------------------------------------------------------------- UI
    def _build_ui(self):
        pad = t.PAD_WINDOW

        header = ctk.CTkFrame(self, fg_color=t.BG)
        header.pack(fill="x", padx=pad, pady=(pad, t.PAD_GROUP))
        ctk.CTkLabel(header, text="●", text_color=t.PRIMARY,
                     font=t.font(ctk, 14, "bold")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header, text="Zeiten Berechnen", text_color=t.INK,
                     font=t.font(ctk, t.SIZE_H3, "bold", display=True)).pack(side="left")
        self.status_pill = w.status_pill(header, "Bereit", "active")
        self.status_pill.pack(side="right")

        w.divider(self).pack(fill="x", padx=pad)

        bottom = ctk.CTkFrame(self, fg_color=t.BG)
        bottom.pack(fill="x", side="bottom", padx=pad, pady=pad)
        self.error_label = ctk.CTkLabel(
            bottom, text="", text_color=t.DANGER, anchor="w", justify="left",
            font=t.font(ctk, t.SIZE_LABEL), wraplength=680,
        )
        self.error_label.pack(fill="x", pady=(0, 8))
        w.primary_button(bottom, "Berechnen", command=self._calculate).pack(fill="x")

        body = ctk.CTkScrollableFrame(self, fg_color=t.BG)
        body.pack(fill="both", expand=True, padx=pad - 6, pady=(0, t.PAD_GROUP))

        self._build_settings_card(body)
        self._build_days_card(body)
        self._build_summary_panel(body)
        self._build_history_card(body)

    def _build_settings_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, t.PAD_GROUP))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=22, pady=20)

        w.caption(inner, "Einstellungen").pack(fill="x", pady=(0, 4))
        w.heading(inner, "Deine Rahmenbedingungen", level=3).pack(fill="x", pady=(0, t.PAD_TIGHT))

        grid = ctk.CTkFrame(inner, fg_color=t.BG)
        grid.pack(fill="x", pady=(t.PAD_TIGHT, 0))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, (key, label_text, placeholder) in enumerate(SETTING_FIELDS):
            row, col = divmod(i, 2)
            box = ctk.CTkFrame(grid, fg_color=t.BG)
            box.grid(row=row, column=col, sticky="ew",
                      padx=(0, 10) if col == 0 else (10, 0), pady=(0, 10))
            w.label(box, label_text, soft=False).pack(anchor="w", pady=(0, 4))
            entry = w.entry(box, placeholder)
            entry.pack(fill="x")
            self.setting_entries[key] = entry

    def _build_days_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, t.PAD_GROUP))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=22, pady=20)

        w.caption(inner, "Woche").pack(fill="x", pady=(0, 4))
        w.heading(inner, "Deine Zeiten", level=3).pack(fill="x", pady=(0, t.PAD_TIGHT))
        w.label(
            inner,
            "Beginn und Ende im Format HH:MM eintragen. Fehlt das Ende, "
            "schlage ich die Feierabend-Zeit vor.",
        ).pack(fill="x", pady=(0, t.PAD_GROUP))

        grid = ctk.CTkFrame(inner, fg_color=t.BG)
        grid.pack(fill="x")
        grid.columnconfigure(4, weight=1)

        for i, name in enumerate(WEEKDAYS):
            w.label(grid, name, soft=False).grid(
                row=i, column=0, sticky="w", padx=(0, 12), pady=6)
            begin = w.entry(grid, "08:00", width=90)
            begin.grid(row=i, column=1, padx=(0, 6), pady=6)
            ctk.CTkLabel(grid, text="–", text_color=t.INK_FAINT, width=16).grid(
                row=i, column=2)
            end = w.entry(grid, "16:30", width=90)
            end.grid(row=i, column=3, padx=(6, 16), pady=6)
            result = ctk.CTkLabel(
                grid, text="—", anchor="w", text_color=t.INK_SOFT, justify="left",
                font=t.font(ctk, t.SIZE_BODY),
            )
            result.grid(row=i, column=4, sticky="ew", pady=6)
            self.day_rows[name] = {"begin": begin, "end": end, "result": result}

    def _build_summary_panel(self, parent):
        panel = w.soft_panel(parent)
        panel.pack(fill="x", pady=(0, t.PAD_GROUP))
        inner = ctk.CTkFrame(panel, fg_color=t.BG_SOFT)
        inner.pack(fill="x", padx=24, pady=20)

        w.label(inner, "Zusammenfassung", soft=False).pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(inner, fg_color=t.BG_SOFT)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.stat_worked = self._make_stat_tile(grid, 0, 0, "Gearbeitet diese Woche")
        self.stat_remaining = self._make_stat_tile(grid, 0, 1, "Frei bis Wochenmaximum")
        self.stat_earned = self._make_stat_tile(grid, 1, 0, "Verdienst bisher")
        self.stat_projected = self._make_stat_tile(grid, 1, 1, "Prognose mit Feierabend")

        self.warning_frame = ctk.CTkFrame(inner, fg_color=t.BG_SOFT)
        # wird bei Bedarf in _render_warnings gepackt/entpackt

    def _make_stat_tile(self, parent, row, col, title):
        box = ctk.CTkFrame(
            parent, fg_color=t.BG, corner_radius=t.R_SM,
            border_width=1, border_color=t.LINE,
        )
        box.grid(row=row, column=col, sticky="nsew",
                  padx=(0, 8) if col == 0 else (8, 0),
                  pady=(0, 8) if row == 0 else (0, 0))
        inner = ctk.CTkFrame(box, fg_color=t.BG)
        inner.pack(padx=16, pady=14, fill="both")
        w.label(inner, title).pack(anchor="w")
        value = ctk.CTkLabel(
            inner, text="—", text_color=t.INK, anchor="w",
            font=t.font(ctk, t.SIZE_H3, "bold", display=True),
        )
        value.pack(anchor="w", pady=(4, 0))
        return value

    def _build_history_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, 0))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=22, pady=20)

        head = ctk.CTkFrame(inner, fg_color=t.BG)
        head.pack(fill="x", pady=(0, t.PAD_TIGHT))
        w.heading(head, "Frühere Wochen", level=3).pack(side="left")
        w.secondary_button(
            head, "Woche abschließen & neu beginnen", compact=True,
            command=self._finish_week,
        ).pack(side="right")

        self.history_list = ctk.CTkFrame(inner, fg_color=t.BG)
        self.history_list.pack(fill="x", pady=(t.PAD_TIGHT, 0))

    # ------------------------------------------------------------- Laden
    def _load_from_store(self):
        settings = self.store.settings
        for key, _, _ in SETTING_FIELDS:
            entry = self.setting_entries[key]
            entry.delete(0, "end")
            entry.insert(0, format_number(settings[key]))

        week = self.store.week
        for name, widgets in self.day_rows.items():
            widgets["begin"].delete(0, "end")
            widgets["begin"].insert(0, week[name]["begin"])
            widgets["end"].delete(0, "end")
            widgets["end"].insert(0, week[name]["end"])

        self._render_history()

    # ---------------------------------------------------------- Berechnen
    def _read_settings(self):
        values = {}
        errors = []
        for key, label_text, _ in SETTING_FIELDS:
            text = self.setting_entries[key].get()
            try:
                value = parse_number(text)
            except ValueError:
                errors.append(f"{label_text}: „{text}“ ist keine gültige Zahl.")
                continue
            minimum = SETTING_MINIMUMS[key]
            if value < minimum:
                errors.append(f"{label_text}: muss mindestens {format_number(minimum)} sein.")
                continue
            values[key] = value
        return values, errors

    def _calculate(self):
        settings, setting_errors = self._read_settings()
        day_inputs = {
            name: {"begin": widgets["begin"].get(), "end": widgets["end"].get()}
            for name, widgets in self.day_rows.items()
        }

        if setting_errors:
            self.error_label.configure(text="\n".join(setting_errors))
            self.status_pill.configure(text="  Fehler  ", text_color=t.DANGER, fg_color=t.DANGER_TINT)
            return

        self.store.update_settings(**settings)
        for name, values in day_inputs.items():
            self.store.update_day(name, values["begin"], values["end"])

        result = calc.compute_week(day_inputs, settings)
        self.last_result = result
        self._render_result(result)

    def _render_result(self, result):
        for day in result.days:
            widgets = self.day_rows[day.name]
            label = widgets["result"]
            if day.error:
                label.configure(text=day.error, text_color=t.DANGER)
            elif day.complete:
                pause_text = (
                    f"Pause {calc.format_duration(day.break_minutes)}"
                    if day.break_minutes else "keine Pause"
                )
                label.configure(
                    text=f"{calc.format_duration(day.work_minutes)} · {pause_text}",
                    text_color=t.INK,
                )
            elif day.suggested_end_minutes is not None:
                label.configure(
                    text=f"→ Feierabend ca. {calc.format_clock(day.suggested_end_minutes)}",
                    text_color=t.PRIMARY,
                )
            else:
                label.configure(text="—", text_color=t.INK_FAINT)

        self.stat_worked.configure(text=calc.format_duration(result.total_work_minutes))

        if result.remaining_week_minutes >= 0:
            self.stat_remaining.configure(
                text=calc.format_duration(result.remaining_week_minutes), text_color=t.INK)
        else:
            self.stat_remaining.configure(
                text=f"-{calc.format_duration(-result.remaining_week_minutes)}",
                text_color=t.DANGER)

        self.stat_earned.configure(text=calc.format_money(result.earned_so_far))
        self.stat_projected.configure(
            text=calc.format_money(result.earned_projected)
            if result.earned_projected is not None
            else "–"
        )

        self.error_label.configure(text="\n".join(result.errors) if result.errors else "")
        self._render_warnings(result.warnings)

        if result.errors:
            self.status_pill.configure(text="  Fehler  ", text_color=t.DANGER, fg_color=t.DANGER_TINT)
        elif result.warnings:
            self.status_pill.configure(text="  Hinweis  ", text_color=t.AMBER, fg_color=t.AMBER_TINT)
        else:
            self.status_pill.configure(text="  Bereit  ", text_color=t.SUCCESS, fg_color=t.SUCCESS_TINT)

    def _render_warnings(self, warnings):
        for child in self.warning_frame.winfo_children():
            child.destroy()
        if not warnings:
            self.warning_frame.pack_forget()
            return
        for text in warnings:
            ctk.CTkLabel(
                self.warning_frame, text=f"⚠ {text}", anchor="w", justify="left",
                text_color=t.AMBER, font=t.font(ctk, t.SIZE_LABEL), wraplength=680,
            ).pack(fill="x", pady=(6, 0))
        self.warning_frame.pack(fill="x", pady=(10, 0))

    # ------------------------------------------------------------ Verlauf
    def _finish_week(self):
        self._calculate()
        result = self.last_result
        if result is None or not any(d.complete for d in result.days):
            self.error_label.configure(
                text="Noch keine vollständige Woche eingetragen – nichts zum Abschließen.")
            return
        label = f"Woche bis {date.today().strftime('%d.%m.%Y')}"
        self.store.finish_week(label, result.total_work_minutes, result.earned_so_far)
        self._load_from_store()
        self._calculate()

    def _render_history(self):
        for child in self.history_list.winfo_children():
            child.destroy()
        history = self.store.history
        if not history:
            w.label(self.history_list, "Noch keine abgeschlossene Woche.").pack(fill="x")
            return
        for index, entry in enumerate(history):
            row = ctk.CTkFrame(self.history_list, fg_color=t.BG)
            row.pack(fill="x", pady=(0, 6))
            text = (
                f"{entry['label']} — {calc.format_duration(entry['workMinutes'])} · "
                f"{calc.format_money(entry['earned'])}"
            )
            ctk.CTkLabel(
                row, text=text, anchor="w", text_color=t.INK_SOFT,
                font=t.font(ctk, t.SIZE_BODY),
            ).pack(side="left", fill="x", expand=True)
            w.ghost_button(
                row, "Entfernen", command=lambda i=index: self._remove_history(i),
            ).pack(side="right")

    def _remove_history(self, index):
        self.store.remove_history_entry(index)
        self._render_history()

    # -------------------------------------------------------------- Ende
    def _on_close(self):
        self._calculate()
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    t.register_fonts()
    App().mainloop()
