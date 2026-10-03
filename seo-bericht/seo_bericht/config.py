"""Einstellungen laden.

Lernpunkt: Zugangsdaten stehen NIE im Code, sondern in einer .env-Datei,
die nicht ins Git-Repo kommt (siehe .gitignore). Vorlage: .env.example
"""
import os
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent


def lade_env(pfad: Path = PROJEKT / ".env") -> None:
    """Liest KEY=WERT-Zeilen aus .env in die Umgebungsvariablen."""
    if not pfad.exists():
        return
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        key, wert = zeile.split("=", 1)
        os.environ.setdefault(key.strip(), wert.strip().strip('"').strip("'"))


def get(key: str, default: str | None = None, pflicht: bool = False) -> str | None:
    wert = os.environ.get(key, default)
    if pflicht and not wert:
        raise SystemExit(f"Fehlt in .env: {key}  (siehe .env.example)")
    return wert


lade_env()
