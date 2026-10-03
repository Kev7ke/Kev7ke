"""Der komplette Ablauf: Daten holen → auswerten → Text → HTML-Datei."""
import json
import secrets
from pathlib import Path

from . import analyse, bericht, config, gsc, wordpress

BERICHTE = config.PROJEKT / "berichte"


def erstelle_bericht(csv: str | None = None, csv_vergleich: str | None = None,
                     mit_wp: bool = True, mit_ki: bool = True, dateiname: str | None = None) -> dict:
    start, ende = gsc.monat(1)
    monat = bericht.monatsname(start)

    if csv:
        daten = gsc.von_csv(csv)
        vorher = gsc.von_csv(csv_vergleich) if csv_vergleich else None
    else:
        prop = config.get("GSC_PROPERTY", pflicht=True)
        schluessel = config.get("GOOGLE_SERVICE_ACCOUNT_JSON", pflicht=True)
        daten = gsc.von_api(prop, schluessel, start, ende)
        vorher = gsc.von_api(prop, schluessel, *gsc.monat(2))

    inhalte = None
    if mit_wp and config.get("WP_SITE"):
        inhalte = wordpress.hole_inhalte(config.get("WP_SITE"), config.get("WP_USER"),
                                         config.get("WP_APP_PASSWORD"))

    auswertung = analyse.auswerten(daten, vorher, inhalte)
    texte = (bericht.texte_mit_claude(auswertung, monat, config.get("ANREDE", "Sie-Form"))
             if mit_ki else bericht.texte_ohne_ki(auswertung, monat))
    seite = bericht.html_bericht(texte, auswertung, start, config.get("PRAXIS_NAME", ""),
                                 config.get("GRUSS", "Viele Grüße"))

    BERICHTE.mkdir(exist_ok=True)
    # Zufälliger Dateiname = nicht erratbarer Link, wenn der Server ihn ausliefert
    name = dateiname or f"{start:%Y-%m}-{secrets.token_urlsafe(12)}"
    pfad = BERICHTE / f"{name}.html"
    pfad.write_text(seite, encoding="utf-8")
    (BERICHTE / f"{name}.json").write_text(
        json.dumps({"auswertung": auswertung, "texte": texte}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    return {"name": name, "pfad": pfad, "monat": monat, "todos": len(texte["todos"]),
            "klicks": auswertung["gesamt"]["klicks"]}


OFFEN = BERICHTE / "offen.json"


def merke_offen(b: dict) -> None:
    """Merkt sich den Bericht, der auf dein "ja" wartet."""
    BERICHTE.mkdir(exist_ok=True)
    OFFEN.write_text(json.dumps({"name": b["name"], "monat": b["monat"]}))


def offen() -> dict | None:
    return json.loads(OFFEN.read_text()) if OFFEN.exists() else None


def freigabe_nachricht(b: dict) -> str:
    return (f"✅ SEO-Bericht {b['monat']} ist fertig ({b['klicks']} Klicks, "
            f"{b['todos']} To-dos für die Kundin):\n{link(b['name'])}\n\n"
            "Antworte *ja* zum Senden an die Kundin oder *nein* zum Verwerfen.")


def link(name: str) -> str:
    return f"{config.get('OEFFENTLICHE_URL', 'http://localhost:8000').rstrip('/')}/b/{name}"
