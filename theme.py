"""
Ru-Services Designsystem — Desktop (CustomTkinter).
Regeln: https://github.com/FinnRu007/Ru-Design (DESIGN.md)

Diese Werte sind verbindlich. In ein neues Projekt kopieren und
NICHT projektweise abwandeln.
"""

# ---------------------------------------------------------------- Farben
BG          = "#FFFFFF"   # Fensterhintergrund, Karten
BG_SOFT     = "#F6F7FA"   # abgesetzte Sektionen, Hover auf hellen Buttons
BG_SOFT_2   = "#EEF1F6"   # Tags, Zähler, Dropdown-Fläche
INK         = "#12141C"   # Haupttext, Überschriften
INK_SOFT    = "#5B6270"   # Text zweiter Ordnung, Beschriftungen
INK_FAINT   = "#8A909C"   # Platzhalter, deaktiviert
LINE        = "#E6E8EE"   # Ränder, Trennlinien

# Akzent — der EINZIGE Akzentton
PRIMARY      = "#2A4CE0"
PRIMARY_DARK = "#1B34A8"  # Hover
PRIMARY_TINT = "#EDF0FD"  # Akzentfläche (aktiver Tab, Icon-Hintergrund)

# Status (keine Deko — nur Zustände)
SUCCESS = "#12965A";  SUCCESS_TINT = "#E9F8F0"
AMBER   = "#B7791F";  AMBER_TINT   = "#FBF3E4"
DANGER  = "#DC4C3F";  DANGER_TINT  = "#FBEAE8"

WHITE = "#FFFFFF"

# ------------------------------------------------------------ Dark (optional)
# ctk.set_appearance_mode("system") + fg_color=(LIGHT, DARK)-Tupel verwenden.
DARK = {
    "BG": "#12141C", "BG_SOFT": "#1B1E28", "BG_SOFT_2": "#252935",
    "INK": "#F2F4F8", "INK_SOFT": "#A2A8B6", "LINE": "#2E3340",
    "PRIMARY": "#5B78F0", "PRIMARY_DARK": "#3F5AD8", "PRIMARY_TINT": "#20264A",
}

# ---------------------------------------------------------------- Radius
R_SM   = 10   # Inputs, kleine Boxen
R_MD   = 16   # Karten, Panels
R_LG   = 24   # große Container
R_PILL = 999  # Buttons, Chips  (CTk begrenzt auf halbe Höhe -> echte Pill)

# ---------------------------------------------------------------- Abstände
PAD_WINDOW = 22   # Fensterrand
PAD_GROUP  = 16   # zwischen Gruppen
PAD_TIGHT  = 8    # innerhalb einer Gruppe

# ---------------------------------------------------------------- Schrift
FONT_FAMILY  = "Inter"     # Fallback siehe register_fonts()
FONT_DISPLAY = "Manrope"

# Größen (pt):  Body 13 · Label 11 · H3 16 · H2 20 · H1 26
SIZE_BODY = 13
SIZE_LABEL = 11
SIZE_H3 = 16
SIZE_H2 = 20
SIZE_H1 = 26

_HAS_BRAND_FONTS = False


def register_fonts() -> None:
    """Bündelt liegende .ttf laden (Ordner ``fonts/``), sonst Segoe UI.

    Bei mitgelieferten Schriften ``fonts/Inter-Regular.ttf`` etc. ablegen.
    """
    global _HAS_BRAND_FONTS, FONT_FAMILY, FONT_DISPLAY
    import os
    import glob

    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    ttfs = glob.glob(os.path.join(font_dir, "*.ttf")) if os.path.isdir(font_dir) else []

    if ttfs:
        try:
            import ctypes
            for path in ttfs:
                ctypes.windll.gdi32.AddFontResourceW(path)
            _HAS_BRAND_FONTS = True
            return
        except Exception:
            pass

    # Fallback: Windows-Standard, damit nie Times/TkDefault erscheint.
    FONT_FAMILY = "Segoe UI"
    FONT_DISPLAY = "Segoe UI Semibold"


def font(ctk, size: int = SIZE_BODY, weight: str = "normal", display: bool = False):
    """CTkFont im Designsystem. ``ctk`` = das customtkinter-Modul."""
    return ctk.CTkFont(
        family=FONT_DISPLAY if display else FONT_FAMILY,
        size=size,
        weight=weight,
    )
