"""Die eigentliche SEO-Auswertung – feste, nachvollziehbare Regeln.

Lernpunkt: Die Zahlen und Regeln kommen aus Code (prüfbar, jeden Monat gleich).
Claude formuliert danach nur den Text. So erfindet die KI keine Zahlen.

Die Regeln (Daumenwerte, anpassbar):
  - Schneller Gewinn: Position 8–20 + genug Impressionen → Beitrag ergänzen
  - Titel/Beschreibung: viele Impressionen, aber niedrige CTR → Wording prüfen
  - Veraltet: > 18 Monate nicht aktualisiert, aber wird gefunden
  - Zu kurz: < 500 Wörter
  - Technik (macht die Agentur, nicht die Kundin): fehlende Meta-Beschreibung, Bilder ohne Alt-Text
"""
from urllib.parse import urlsplit

from .wordpress import monate_seit

MIN_IMPRESSIONEN = 50
CTR_SCHWELLE = 0.02
MAX_KUNDEN_TODOS = 5


def norm(url: str) -> str:
    teile = urlsplit(url.strip().lower())
    return (teile.netloc.removeprefix("www.") + teile.path).rstrip("/")


def titel_aus_url(url: str) -> str:
    """'/blog/burnout-erste-anzeichen/' → 'Burnout erste anzeichen' (wenn WordPress-Daten fehlen)."""
    slug = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").capitalize() if slug else "Startseite"


def de(zahl: float, stellen: int = 1) -> str:
    return f"{zahl:.{stellen}f}".replace(".", ",")


def _veraenderung(jetzt: float, vorher: float | None) -> float | None:
    if vorher is None:
        return None
    if vorher == 0:
        return None if jetzt == 0 else 1.0
    return (jetzt - vorher) / vorher


def auswerten(gsc: dict, gsc_vorher: dict | None = None, inhalte: list[dict] | None = None) -> dict:
    vorher = {norm(s["key"]): s for s in (gsc_vorher or {}).get("seiten", [])}
    wp = {norm(i["url"]): i for i in (inhalte or [])}

    seiten = []
    for s in gsc["seiten"]:
        u = norm(s["key"])
        v = vorher.get(u)
        info = wp.pop(u, {})
        seiten.append({
            "url": s["key"],
            "titel": info.get("titel") or titel_aus_url(s["key"]),
            "typ": info.get("typ"),
            "klicks": int(s["clicks"]),
            "impressionen": int(s["impressions"]),
            "ctr": round(s["ctr"], 4),
            "position": round(s["position"], 1),
            "klicks_vorher": int(v["clicks"]) if v else None,
            "trend": _veraenderung(s["clicks"], v["clicks"] if v else None) if gsc_vorher else None,
            "woerter": info.get("woerter"),
            "geaendert": info.get("geaendert"),
            "meta_beschreibung": info.get("meta_beschreibung"),
            "bilder_ohne_alt": info.get("bilder_ohne_alt", 0),
        })
    # Beiträge, die in Google gar nicht auftauchen
    unsichtbar = [{"titel": i["titel"], "url": i["url"], "veroeffentlicht": i["veroeffentlicht"]}
                  for i in wp.values() if i["typ"] == "Beitrag"]

    seiten.sort(key=lambda s: (s["klicks"], s["impressionen"]), reverse=True)

    summe = lambda daten, k: int(sum(x[k] for x in daten))
    gesamt = {
        "klicks": summe(gsc["seiten"], "clicks"),
        "impressionen": summe(gsc["seiten"], "impressions"),
    }
    if gsc_vorher:
        gesamt["klicks_vorher"] = summe(gsc_vorher["seiten"], "clicks")
        gesamt["impressionen_vorher"] = summe(gsc_vorher["seiten"], "impressions")

    kunde, agentur = [], []
    for s in seiten:
        if s["impressionen"] >= MIN_IMPRESSIONEN and 8 <= s["position"] <= 20:
            kunde.append({"art": "ergänzen", "seite": s,
                          "grund": f"Steht auf Position {de(s['position'])} – knapp vor Seite 1 bei Google."})
        elif s["impressionen"] >= MIN_IMPRESSIONEN and s["ctr"] < CTR_SCHWELLE and s["position"] <= 10:
            kunde.append({"art": "wording", "seite": s,
                          "grund": f"{s['impressionen']}× gesehen, aber nur {de(s['ctr'] * 100)} % klicken – Überschrift/Einleitung macht zu wenig neugierig."})
        elif s["geaendert"] and monate_seit(s["geaendert"]) > 18 and s["impressionen"] >= MIN_IMPRESSIONEN:
            kunde.append({"art": "aktualisieren", "seite": s,
                          "grund": f"Seit {s['geaendert']} nicht aktualisiert, wird aber noch gefunden."})
        elif s["woerter"] is not None and s["woerter"] < 500 and s["impressionen"] >= MIN_IMPRESSIONEN:
            kunde.append({"art": "ergänzen", "seite": s,
                          "grund": f"Nur {s['woerter']} Wörter – Google bevorzugt ausführlichere Antworten."})

        if s["meta_beschreibung"] == "":
            agentur.append({"art": "meta", "seite": s["url"], "grund": "Meta-Beschreibung fehlt"})
        if s["bilder_ohne_alt"]:
            agentur.append({"art": "alt", "seite": s["url"],
                            "grund": f"{s['bilder_ohne_alt']} Bild(er) ohne Alt-Text"})

    # Wichtigste zuerst: viele Impressionen = größter Hebel
    kunde.sort(key=lambda t: t["seite"]["impressionen"], reverse=True)

    return {
        "gesamt": gesamt,
        "top_seiten": seiten[:5],
        "verlierer": sorted([s for s in seiten if s["trend"] is not None and s["trend"] < -0.2
                             and (s["klicks_vorher"] or 0) >= 5], key=lambda s: s["trend"])[:3],
        "top_anfragen": sorted(gsc.get("anfragen", []), key=lambda a: a["clicks"], reverse=True)[:10],
        "kunden_todos": kunde[:MAX_KUNDEN_TODOS],
        "agentur_todos": agentur,
        "unsichtbare_beitraege": unsichtbar,
    }
