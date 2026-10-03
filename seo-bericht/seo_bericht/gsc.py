"""Google Search Console: Klicks, Impressionen, CTR, Position.

Zwei Wege:
  1. von_csv()  – Phase 1: Du exportierst die Daten von Hand (Leistung → Exportieren → CSV)
  2. von_api()  – Phase 2: automatisch über einen Google-Service-Account
"""
import csv
import datetime as dt
from pathlib import Path


def monat(versatz: int = 1, heute: dt.date | None = None) -> tuple[dt.date, dt.date]:
    """Start/Ende eines Kalendermonats. versatz=1 → Vormonat, 2 → Monat davor."""
    heute = heute or dt.date.today()
    erster = heute.replace(day=1)
    for _ in range(versatz):
        erster = (erster - dt.timedelta(days=1)).replace(day=1)
    naechster = (erster + dt.timedelta(days=32)).replace(day=1)
    return erster, naechster - dt.timedelta(days=1)


# ---------- Weg 1: CSV-Export ----------

def _zahl(text: str) -> float:
    """'1.234' / '3,5 %' / '12,3' → float (deutsche und englische Exporte)."""
    t = (text or "").replace("%", "").replace(" ", "").strip()
    if not t:
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t)


def _lies_tabelle(datei: Path) -> list[dict]:
    with datei.open(encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        kopf = [k.lower() for k in next(reader)]

        def spalte(*namen):
            return next(i for i, k in enumerate(kopf) if any(n in k for n in namen))

        i_klick = spalte("klick", "click")
        i_impr = spalte("impression")
        i_ctr = spalte("ctr")
        i_pos = spalte("position")
        zeilen = []
        for z in reader:
            if not z or not z[0]:
                continue
            zeilen.append({
                "key": z[0],
                "clicks": _zahl(z[i_klick]),
                "impressions": _zahl(z[i_impr]),
                "ctr": _zahl(z[i_ctr]) / 100,  # Export zeigt Prozent
                "position": _zahl(z[i_pos]),
            })
        return zeilen


def _finde(ordner: Path, *namen: str) -> Path | None:
    for datei in ordner.glob("*.csv"):
        if any(n in datei.stem.lower() for n in namen):
            return datei
    return None


def von_csv(ordner: str | Path) -> dict:
    """Liest einen entpackten Search-Console-Export (Seiten.csv, Suchanfragen.csv)."""
    ordner = Path(ordner)
    seiten = _finde(ordner, "seite", "page")
    anfragen = _finde(ordner, "suchanfrage", "anfrage", "quer")
    if not seiten:
        raise SystemExit(f"Keine Seiten.csv/Pages.csv in {ordner} gefunden.")
    return {
        "seiten": _lies_tabelle(seiten),
        "anfragen": _lies_tabelle(anfragen) if anfragen else [],
    }


# ---------- Weg 2: API ----------

def von_api(property_url: str, schluessel_datei: str, start: dt.date, ende: dt.date) -> dict:
    """Holt dieselben Daten direkt von Google.

    Voraussetzung (einmalig, siehe README Phase 2):
      - Service-Account in Google Cloud anlegen, JSON-Schlüssel herunterladen
      - Search Console API aktivieren
      - die Service-Account-E-Mail in der Search Console als Nutzer (Lesen) hinzufügen
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        schluessel_datei, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    dienst = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    def abfrage(dimension: str) -> list[dict]:
        antwort = dienst.searchanalytics().query(siteUrl=property_url, body={
            "startDate": start.isoformat(),
            "endDate": ende.isoformat(),
            "dimensions": [dimension],
            "rowLimit": 500,
        }).execute()
        return [{"key": r["keys"][0], **{k: r[k] for k in ("clicks", "impressions", "ctr", "position")}}
                for r in antwort.get("rows", [])]

    return {"seiten": abfrage("page"), "anfragen": abfrage("query")}
