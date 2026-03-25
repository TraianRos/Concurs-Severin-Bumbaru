import sys
from pathlib import Path

# Adaugam radacina proiectului in sys.path ca pytest sa poata importa pachetul local `app`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
