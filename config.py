import os
import sys

if getattr(sys, "frozen", False):
    # Als .exe (PyInstaller) gebaut: Daten neben der .exe ablegen, nicht im
    # fluechtigen Extraktions-Ordner.
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "zeiterfassung.json")
