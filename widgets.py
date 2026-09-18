"""
Fertige Bausteine im Ru-Services-Stil.
Alle Funktionen geben ein CustomTkinter-Widget zurück, das direkt
gepackt/gegridet werden kann.
"""

import customtkinter as ctk

import theme as t


def heading(master, text, level=2):
    size = {1: t.SIZE_H1, 2: t.SIZE_H2, 3: t.SIZE_H3}[level]
    return ctk.CTkLabel(
        master, text=text, text_color=t.INK, anchor="w",
        font=t.font(ctk, size, "bold", display=True),
    )


def label(master, text, soft=True):
    return ctk.CTkLabel(
        master, text=text, anchor="w",
        text_color=t.INK_SOFT if soft else t.INK,
        font=t.font(ctk, t.SIZE_BODY),
    )


def caption(master, text):
    return ctk.CTkLabel(
        master, text=text.upper(), anchor="w", text_color=t.PRIMARY,
        font=t.font(ctk, t.SIZE_LABEL, "bold", display=True),
    )


def card(master, **kwargs):
    """Panel mit 1px-Rand + Radius (Schatten kann Tkinter nicht)."""
    return ctk.CTkFrame(
        master, fg_color=t.BG, border_width=1, border_color=t.LINE,
        corner_radius=t.R_MD, **kwargs,
    )


def soft_panel(master, **kwargs):
    return ctk.CTkFrame(master, fg_color=t.BG_SOFT, corner_radius=t.R_MD, **kwargs)


def primary_button(master, text, command=None, compact=False, **kwargs):
    return ctk.CTkButton(
        master, text=text, command=command,
        fg_color=t.PRIMARY, hover_color=t.PRIMARY_DARK, text_color=t.WHITE,
        corner_radius=t.R_PILL, height=32 if compact else 40,
        font=t.font(ctk, t.SIZE_BODY, "bold"), **kwargs,
    )


def secondary_button(master, text, command=None, compact=False, **kwargs):
    return ctk.CTkButton(
        master, text=text, command=command,
        fg_color=t.BG, hover_color=t.BG_SOFT, text_color=t.INK,
        border_width=1, border_color=t.LINE,
        corner_radius=t.R_PILL, height=32 if compact else 40,
        font=t.font(ctk, t.SIZE_BODY, "bold"), **kwargs,
    )


def ghost_button(master, text, command=None, **kwargs):
    return ctk.CTkButton(
        master, text=text, command=command,
        fg_color="transparent", hover_color=t.BG_SOFT, text_color=t.PRIMARY,
        corner_radius=t.R_PILL, height=32,
        font=t.font(ctk, t.SIZE_BODY, "bold"), **kwargs,
    )


def entry(master, placeholder="", **kwargs):
    return ctk.CTkEntry(
        master, placeholder_text=placeholder,
        fg_color=t.BG, border_color=t.LINE, border_width=1,
        text_color=t.INK, placeholder_text_color=t.INK_FAINT,
        corner_radius=t.R_SM, height=38,
        font=t.font(ctk, t.SIZE_BODY), **kwargs,
    )


def option_menu(master, values, **kwargs):
    return ctk.CTkOptionMenu(
        master, values=values,
        fg_color=t.BG_SOFT_2, button_color=t.PRIMARY,
        button_hover_color=t.PRIMARY_DARK, text_color=t.INK,
        corner_radius=t.R_SM, font=t.font(ctk, t.SIZE_BODY), **kwargs,
    )


def segmented(master, values, **kwargs):
    return ctk.CTkSegmentedButton(
        master, values=values,
        selected_color=t.PRIMARY, selected_hover_color=t.PRIMARY_DARK,
        unselected_color=t.BG_SOFT, unselected_hover_color=t.BG_SOFT_2,
        text_color=t.INK, corner_radius=t.R_PILL,
        font=t.font(ctk, t.SIZE_BODY), **kwargs,
    )


_STATUS = {
    "active":   (t.SUCCESS, t.SUCCESS_TINT),
    "progress": (t.AMBER,   t.AMBER_TINT),
    "archived": (t.INK_SOFT, t.BG_SOFT_2),
    "error":    (t.DANGER,  t.DANGER_TINT),
}


def status_pill(master, text, kind="active"):
    fg, bg = _STATUS[kind]
    return ctk.CTkLabel(
        master, text=f"  {text}  ", text_color=fg, fg_color=bg,
        corner_radius=t.R_PILL, font=t.font(ctk, t.SIZE_LABEL, "bold"),
    )


def divider(master):
    return ctk.CTkFrame(master, height=1, fg_color=t.LINE)
