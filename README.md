# Ru-Zeiterfassung — Zeiten Berechnen

Windows-Programm für die eigene Arbeitszeit: Stundenlohn, Wochen- und
Tagesmaximum sowie eine automatische Pausenregel eintragen, dann für jeden
Wochentag Beginn und Ende erfassen. Fehlt an einem Tag das Ende, schlägt das
Programm die Feierabend-Zeit vor, ab der Wochen- oder Tagesmaximum erreicht
ist — und rechnet den Verdienst der Woche aus.

![Logo](icon.png)

## Wie es rechnet

Die Pausenregel ist frei einstellbar (Standard: **6 Stunden**). Bis zu dieser
Grenze zählt alles als Arbeit. Danach sind die nächsten **45 Minuten**
automatisch Pause statt Arbeit, die Zeit danach wieder Arbeit. Beispiel bei
Beginn 08:00 und Ende 16:30: 8,5 Stunden Anwesenheit, davon 45 Minuten Pause
→ 7 Stunden 45 Minuten Arbeitszeit.

Für einen Tag ohne eingetragenes Ende berechnet das Programm die
Feierabend-Zeit aus dem, was von Wochen- und Tagesmaximum noch übrig ist
(je nachdem, was zuerst erreicht wird) — inklusive der Pause, die auf dem Weg
dahin noch anfällt.

## Bedienung

1. Einstellungen einmalig ausfüllen: Stundenlohn, Wochen- und
   Tagesmaximum, Pausenregel. Werden lokal gespeichert.
2. Für jeden Tag Beginn und Ende eintragen (Format `HH:MM`).
3. **Berechnen** klicken (oder das Fenster einfach schließen — es wird
   beim Schließen automatisch gespeichert).
4. Häufigster Ablauf: Montag bis Donnerstag komplett eintragen, am Freitag
   nur den Beginn — die App schlägt die Feierabend-Zeit vor.
5. Am Ende der Woche **„Woche abschließen & neu beginnen"**: die Woche
   wandert mit Gesamtstunden und Verdienst in den Verlauf, die Felder werden
   für die neue Woche geleert.

## Lokal starten (ohne EXE)

```bash
pip install -r requirements.txt
python ru_zeiterfassung.py
```

## EXE selbst bauen (Windows)

Doppelklick auf `build_exe.bat`, oder manuell:

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onedir --windowed --noupx --name "Ru-Zeiterfassung" --icon "icon.ico" --version-file "version.txt" --add-data "icon.ico;." ru_zeiterfassung.py
```

Das Ergebnis liegt danach unter `dist\Ru-Zeiterfassung\` (und als
`dist\Ru-Zeiterfassung.zip` zum Weitergeben). Ordner-Modus statt einer
einzelnen Datei, weil das bei Virenscannern deutlich seltener Fehlalarme
auslöst.

## Projektstruktur

```
Ru-Zeiterfassung/
├── ru_zeiterfassung.py    Hauptprogramm (CustomTkinter-Oberfläche)
├── berechnung.py           Rechenlogik (Pause/Arbeit/Feierabend/Lohn), ohne UI
├── storage.py / config.py  Lokale JSON-Speicherung neben der exe
├── theme.py / widgets.py   Designsystem, 1:1 aus Ru-Design
├── make_icon.py            erzeugt icon.png / icon.ico (nur Pillow)
├── icon.ico / icon.png     App-Logo
├── requirements.txt
├── build_exe.bat           Windows-Build per Doppelklick
├── version.txt             Versionsinfo fürs EXE (gegen Fehlalarme)
└── README.md
```

## Design

Nach dem gemeinsamen Regelwerk in
[FinnRu007/Ru-Design](https://github.com/FinnRu007/Ru-Design):
weißer Hintergrund, ein Akzent `#2A4CE0`, Pill-Buttons, Manrope/Inter
(Fallback Segoe UI).

## Lizenz

Frei nutzbar für private und interne Zwecke.
