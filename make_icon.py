"""
Erzeugt das Ru-Zeiterfassung-Logo: icon.png (512x512) und icon.ico
(mehrere Größen).

Designsystem (Ru-Design/DESIGN.md): weißes Uhr-Motiv auf dem einzigen
Akzent #2A4CE0 — wie eine Wortmarke, zur App-Kachel gemacht.

    pip install pillow
    python make_icon.py

Das Ergebnis ist eingecheckt; dieses Skript nur bei Designänderungen ausführen.
"""

import math

from PIL import Image, ImageDraw

SIZE = 512
SS = 4                      # Supersampling für weiche Kanten
S = SIZE * SS

BLUE = (42, 76, 224, 255)   # #2A4CE0
WHITE = (255, 255, 255, 255)


def _hand(draw, cx, cy, angle_deg, length, width):
    """Zeiger von der Mitte aus, 0° = 12 Uhr, im Uhrzeigersinn. Mit
    abgerundeten Enden (Kreise an beiden Punkten, da PIL keine
    ``round``-Cap-Linien kennt)."""
    rad = math.radians(angle_deg - 90)
    ex = cx + length * math.cos(rad)
    ey = cy + length * math.sin(rad)
    draw.line([cx, cy, ex, ey], fill=WHITE, width=width)
    r = width / 2
    draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=WHITE)


def build() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Abgerundetes Quadrat in Akzentblau
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.235), fill=BLUE)

    # Uhr-Ring
    cx, cy = S * 0.5, S * 0.5
    r = S * 0.30
    ring = int(S * 0.045)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=ring)

    # Zeiger in "10:10"-Stellung (klassischer, freundlicher Uhren-Look)
    _hand(d, cx, cy, 60, r * 0.68, int(S * 0.036))    # Minutenzeiger
    _hand(d, cx, cy, -60, r * 0.42, int(S * 0.046))   # Stundenzeiger

    # Mittelpunkt
    dot = S * 0.03
    d.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=WHITE)

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    icon = build()
    icon.save("icon.png")
    icon.save("icon.ico",
               sizes=[(16, 16), (32, 32), (48, 48), (64, 64),
                      (128, 128), (256, 256)])
    print("icon.png und icon.ico geschrieben.")


if __name__ == "__main__":
    main()
