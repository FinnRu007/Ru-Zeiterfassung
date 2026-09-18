"""
Zeiten Berechnen — Arbeitszeit, Pausen, Urlaub und Wochenlohn.

Stundenlohn, Wochen- und Tagesmaximum sowie eine Pausenregel einstellen,
dann pro Wochentag Beginn und Ende eintragen (oder den Tag als Urlaub
markieren). Fehlt an einem Tag das Ende, schlägt das Programm die
Feierabend-Zeit vor. Jede Kalenderwoche bleibt dauerhaft editierbar; das
Urlaubsentgelt wird nach § 11 BUrlG aus dem Durchschnittsverdienst der
letzten 13 Wochen berechnet.

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
        self.current_week_key = calc.week_key(date.today())

        self.settings_expanded = False
        self._autosave_job = None

        self.title("Zeiten Berechnen")
        self._place_window()
        self.minsize(720, 480)
        self.configure(fg_color=t.BG)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self._build_ui()
        self._load_settings_from_store()
        self._load_week_into_ui()
        self._calculate()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- Fenster
    def _place_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(880, screen_w - 80)
        height = min(640, screen_h - 80)
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
            font=t.font(ctk, t.SIZE_LABEL), wraplength=700,
        )
        self.error_label.pack(fill="x", pady=(0, 8))
        w.primary_button(bottom, "Berechnen", command=self._calculate).pack(fill="x")

        body = ctk.CTkScrollableFrame(self, fg_color=t.BG)
        body.pack(fill="both", expand=True, padx=pad - 6, pady=(0, t.PAD_GROUP))

        self._build_settings_card(body)
        self._build_week_nav(body)
        self._build_days_card(body)
        self._build_summary_panel(body)
        self._build_overview_card(body)

    def _build_settings_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, t.PAD_TIGHT))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=18, pady=12)

        header = ctk.CTkFrame(inner, fg_color=t.BG)
        header.pack(fill="x")
        left = ctk.CTkFrame(header, fg_color=t.BG)
        left.pack(side="left", fill="x", expand=True)
        w.caption(left, "Einstellungen").pack(anchor="w")
        self.settings_summary = w.label(left, "")
        self.settings_summary.pack(anchor="w", pady=(2, 0))
        self.settings_toggle_btn = w.ghost_button(
            header, "", command=self._toggle_settings)
        self.settings_toggle_btn.pack(side="right")

        self.settings_body = ctk.CTkFrame(inner, fg_color=t.BG)

        grid = ctk.CTkFrame(self.settings_body, fg_color=t.BG)
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

        self._render_settings_collapse_state()

    def _toggle_settings(self):
        self.settings_expanded = not self.settings_expanded
        self._render_settings_collapse_state()

    def _settings_summary_text(self):
        settings, errors = self._read_settings()
        if errors:
            return "Ungültige Werte – zum Prüfen aufklappen."
        return (
            f"{format_number(settings['stundenlohn'])} €/h · "
            f"Woche max. {format_number(settings['wochenMaxStunden'])}h · "
            f"Tag max. {format_number(settings['tagesMaxStunden'])}h · "
            f"Pause ab {format_number(settings['pauseAbStunden'])}h "
            f"für {format_number(settings['pauseDauerMinuten'])}min"
        )

    def _render_settings_collapse_state(self):
        if self.settings_expanded:
            self.settings_body.pack(fill="x")
            self.settings_toggle_btn.configure(text="▾ Einklappen")
            self.settings_summary.pack_forget()
        else:
            self.settings_body.pack_forget()
            self.settings_toggle_btn.configure(text="▸ Bearbeiten")
            self.settings_summary.configure(text=self._settings_summary_text())
            self.settings_summary.pack(anchor="w", pady=(2, 0))

    def _build_week_nav(self, parent):
        panel = w.soft_panel(parent)
        panel.pack(fill="x", pady=(0, t.PAD_TIGHT))
        row = ctk.CTkFrame(panel, fg_color=t.BG_SOFT)
        row.pack(fill="x", padx=14, pady=8)

        w.secondary_button(row, "‹", compact=True, width=40,
                            command=self._go_prev_week).pack(side="left")
        self.week_heading = ctk.CTkLabel(
            row, text="", text_color=t.INK, anchor="center",
            font=t.font(ctk, t.SIZE_H3, "bold", display=True),
        )
        self.week_heading.pack(side="left", fill="x", expand=True)
        w.secondary_button(row, "›", compact=True, width=40,
                            command=self._go_next_week).pack(side="left")
        w.ghost_button(row, "Heute", command=self._go_today).pack(side="left", padx=(10, 0))

    def _build_days_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, t.PAD_TIGHT))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=18, pady=14)

        w.caption(inner, "Woche").pack(fill="x", pady=(0, 2))
        w.label(
            inner,
            "HH:MM eintragen oder als Urlaub markieren. Ende leer → Feierabend-Vorschlag.",
        ).pack(fill="x", pady=(0, t.PAD_TIGHT))

        grid = ctk.CTkFrame(inner, fg_color=t.BG)
        grid.pack(fill="x")
        for col in range(len(WEEKDAYS)):
            grid.columnconfigure(col, weight=1)

        for col, name in enumerate(WEEKDAYS):
            w.label(grid, name, soft=False).grid(
                row=0, column=col, sticky="ew", padx=4, pady=(0, 4))

            urlaub_var = ctk.BooleanVar(value=False)
            checkbox = ctk.CTkCheckBox(
                grid, text="Urlaub", variable=urlaub_var,
                checkbox_width=16, checkbox_height=16,
                fg_color=t.PRIMARY, hover_color=t.PRIMARY_DARK,
                border_color=t.LINE, checkmark_color=t.WHITE,
                text_color=t.INK_SOFT, font=t.font(ctk, t.SIZE_LABEL),
                command=lambda n=name: self._on_urlaub_toggle(n),
            )
            checkbox.grid(row=1, column=col, sticky="w", padx=4, pady=(0, 6))

            begin = w.entry(grid, "08:00")
            begin.grid(row=2, column=col, sticky="ew", padx=4, pady=(0, 4))
            begin.bind("<KeyRelease>", self._schedule_autosave)
            begin.bind("<FocusOut>", lambda e: self._save_current_week())

            end = w.entry(grid, "16:30")
            end.grid(row=3, column=col, sticky="ew", padx=4, pady=(0, 6))
            end.bind("<KeyRelease>", self._schedule_autosave)
            end.bind("<FocusOut>", lambda e: self._save_current_week())

            result = ctk.CTkLabel(
                grid, text="—", anchor="center", text_color=t.INK_FAINT, justify="center",
                font=t.font(ctk, t.SIZE_LABEL), wraplength=130,
            )
            result.grid(row=4, column=col, sticky="ew", padx=4, pady=(0, 2))
            self.day_rows[name] = {
                "begin": begin, "end": end, "urlaub_var": urlaub_var, "result": result,
            }

    def _on_urlaub_toggle(self, name):
        widgets = self.day_rows[name]
        is_urlaub = bool(widgets["urlaub_var"].get())
        state = "disabled" if is_urlaub else "normal"
        widgets["begin"].configure(state=state)
        widgets["end"].configure(state=state)
        if is_urlaub:
            widgets["result"].configure(text="Urlaub", text_color=t.INK_SOFT)
        else:
            widgets["result"].configure(text="—", text_color=t.INK_FAINT)
        self._save_current_week()

    def _schedule_autosave(self, _event=None):
        if self._autosave_job is not None:
            self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(400, self._autosave_now)

    def _autosave_now(self):
        self._autosave_job = None
        self._save_current_week()

    def _build_summary_panel(self, parent):
        panel = w.soft_panel(parent)
        panel.pack(fill="x", pady=(0, t.PAD_TIGHT))
        inner = ctk.CTkFrame(panel, fg_color=t.BG_SOFT)
        inner.pack(fill="x", padx=18, pady=14)

        w.label(inner, "Zusammenfassung", soft=False).pack(anchor="w", pady=(0, 8))

        grid = ctk.CTkFrame(inner, fg_color=t.BG_SOFT)
        grid.pack(fill="x")
        for col in range(3):
            grid.columnconfigure(col, weight=1)

        self.stat_worked = self._make_stat_tile(grid, 0, 0, "Gearbeitet")
        self.stat_remaining = self._make_stat_tile(grid, 0, 1, "Frei bis Wochenmax.")
        self.stat_earned = self._make_stat_tile(grid, 0, 2, "Verdienst bisher")
        self.stat_projected = self._make_stat_tile(grid, 1, 0, "Prognose Feierabend")
        self.stat_urlaubstage = self._make_stat_tile(grid, 1, 1, "Urlaubstage")
        self.stat_urlaubsentgelt = self._make_stat_tile(grid, 1, 2, "Urlaubsentgelt")

        self.warning_frame = ctk.CTkFrame(inner, fg_color=t.BG_SOFT)
        # wird bei Bedarf in _render_warnings gepackt/entpackt

    def _make_stat_tile(self, parent, row, col, title):
        box = ctk.CTkFrame(
            parent, fg_color=t.BG, corner_radius=t.R_SM,
            border_width=1, border_color=t.LINE,
        )
        box.grid(row=row, column=col, sticky="nsew",
                  padx=(0 if col == 0 else 4, 0 if col == 2 else 4),
                  pady=(0, 6) if row == 0 else (0, 0))
        inner = ctk.CTkFrame(box, fg_color=t.BG)
        inner.pack(padx=10, pady=8, fill="both")
        w.label(inner, title).pack(anchor="w")
        value = ctk.CTkLabel(
            inner, text="—", text_color=t.INK, anchor="w",
            font=t.font(ctk, t.SIZE_H3, "bold", display=True),
        )
        value.pack(anchor="w", pady=(2, 0))
        return value

    def _build_overview_card(self, parent):
        card = w.card(parent)
        card.pack(fill="x", pady=(0, 0))
        inner = ctk.CTkFrame(card, fg_color=t.BG)
        inner.pack(fill="x", padx=18, pady=14)

        w.caption(inner, "Übersicht").pack(fill="x", pady=(0, 2))
        w.label(inner, "Alle Wochen — anklicken, um zu bearbeiten.").pack(
            fill="x", pady=(0, t.PAD_TIGHT))

        self.overview_list = ctk.CTkFrame(inner, fg_color=t.BG)
        self.overview_list.pack(fill="x")

    # ------------------------------------------------------- Wochen-Navigation
    def _go_prev_week(self):
        self._save_current_week()
        self.current_week_key = calc.week_key_shift(self.current_week_key, -1)
        self._load_week_into_ui()
        self._calculate()

    def _go_next_week(self):
        self._save_current_week()
        self.current_week_key = calc.week_key_shift(self.current_week_key, 1)
        self._load_week_into_ui()
        self._calculate()

    def _go_today(self):
        self._save_current_week()
        self.current_week_key = calc.week_key(date.today())
        self._load_week_into_ui()
        self._calculate()

    def _go_to_week(self, key):
        self._save_current_week()
        self.current_week_key = key
        self._load_week_into_ui()
        self._calculate()

    # ------------------------------------------------------------- Laden
    def _load_settings_from_store(self):
        settings = self.store.settings
        for key, _, _ in SETTING_FIELDS:
            entry = self.setting_entries[key]
            entry.delete(0, "end")
            entry.insert(0, format_number(settings[key]))
        self._render_settings_collapse_state()

    def _load_week_into_ui(self):
        self.week_heading.configure(text=calc.week_label(self.current_week_key))
        days = self.store.get_week_days(self.current_week_key)
        for name, widgets in self.day_rows.items():
            day = days[name]
            widgets["begin"].configure(state="normal")
            widgets["end"].configure(state="normal")
            widgets["begin"].delete(0, "end")
            widgets["begin"].insert(0, day["begin"])
            widgets["end"].delete(0, "end")
            widgets["end"].insert(0, day["end"])
            widgets["urlaub_var"].set(bool(day["urlaub"]))
            if day["urlaub"]:
                widgets["begin"].configure(state="disabled")
                widgets["end"].configure(state="disabled")
        self._render_overview()

    # ----------------------------------------------------------- Speichern
    def _save_current_week(self):
        days = {
            name: {
                "begin": widgets["begin"].get(),
                "end": widgets["end"].get(),
                "urlaub": bool(widgets["urlaub_var"].get()),
            }
            for name, widgets in self.day_rows.items()
        }
        self.store.update_week_days(self.current_week_key, days)

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
            name: {
                "begin": widgets["begin"].get(),
                "end": widgets["end"].get(),
                "urlaub": bool(widgets["urlaub_var"].get()),
            }
            for name, widgets in self.day_rows.items()
        }

        if setting_errors:
            self.error_label.configure(text="\n".join(setting_errors))
            self.status_pill.configure(text="  Fehler  ", text_color=t.DANGER, fg_color=t.DANGER_TINT)
            return

        self.store.update_settings(**settings)
        self._render_settings_collapse_state()
        self.store.update_week_days(self.current_week_key, day_inputs)

        result = calc.compute_week(day_inputs, settings)
        urlaub_result = calc.compute_urlaubsentgelt(self.store.weeks, self.current_week_key, settings)
        self.last_result = result
        self._render_result(result, urlaub_result)
        self._render_overview()

    def _render_result(self, result, urlaub_result):
        for day in result.days:
            widgets = self.day_rows[day.name]
            label = widgets["result"]
            if day.is_urlaub:
                label.configure(text="Urlaub", text_color=t.INK_SOFT)
            elif day.error:
                label.configure(text="⚠ Fehler", text_color=t.DANGER)
            elif day.complete:
                pause_text = (
                    f"Pause {calc.format_duration(day.break_minutes)}"
                    if day.break_minutes else "keine Pause"
                )
                label.configure(
                    text=f"{calc.format_duration(day.work_minutes)}\n{pause_text}",
                    text_color=t.INK,
                )
            elif day.suggested_end_minutes is not None:
                label.configure(
                    text=f"Feierabend\n{calc.format_clock(day.suggested_end_minutes)}",
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

        self.stat_urlaubstage.configure(text=str(result.urlaub_days))
        if result.urlaub_days == 0:
            self.stat_urlaubsentgelt.configure(text="–", text_color=t.INK)
        elif urlaub_result.tagessatz is not None:
            self.stat_urlaubsentgelt.configure(
                text=calc.format_money(urlaub_result.betrag), text_color=t.INK)
        else:
            self.stat_urlaubsentgelt.configure(text="keine Basis", text_color=t.AMBER)

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

    # ------------------------------------------------------------ Übersicht
    def _render_overview(self):
        for child in self.overview_list.winfo_children():
            child.destroy()
        keys = self.store.overview()
        if not keys:
            w.label(self.overview_list, "Noch keine Woche mit Daten.").pack(fill="x")
            return

        settings = self.store.settings
        for key in keys:
            days = self.store.get_week_days(key)
            week_result = calc.compute_week({name: days[name] for name in WEEKDAYS}, settings)

            row = ctk.CTkFrame(self.overview_list, fg_color=t.BG)
            row.pack(fill="x", pady=(0, 6))
            is_current = key == self.current_week_key

            text = f"{calc.week_label(key)} — {calc.format_duration(week_result.total_work_minutes)}"
            text += f" · {calc.format_money(week_result.earned_so_far)}"
            if week_result.urlaub_days:
                text += f" · {week_result.urlaub_days} Urlaubstag(e)"

            ctk.CTkLabel(
                row, text=text, anchor="w", justify="left",
                text_color=t.PRIMARY if is_current else t.INK_SOFT,
                font=t.font(ctk, t.SIZE_BODY, "bold" if is_current else "normal"),
            ).pack(side="left", fill="x", expand=True)

            if not is_current:
                w.ghost_button(
                    row, "Bearbeiten", command=lambda k=key: self._go_to_week(k),
                ).pack(side="right")
            w.ghost_button(
                row, "Leeren", command=lambda k=key: self._clear_week(k),
            ).pack(side="right", padx=(0, 4))

    def _clear_week(self, key):
        self.store.clear_week(key)
        if key == self.current_week_key:
            self._load_week_into_ui()
        self._calculate()

    # -------------------------------------------------------------- Ende
    def _on_close(self):
        if self._autosave_job is not None:
            self.after_cancel(self._autosave_job)
            self._autosave_job = None
        self._save_current_week()
        self._calculate()
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    t.register_fonts()
    App().mainloop()
