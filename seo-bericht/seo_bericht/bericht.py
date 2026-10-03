"""Bericht schreiben: Claude formuliert, Python baut die HTML-Seite.

Lernpunkt: Claude bekommt NUR die fertige Auswertung (Zahlen + Regeln) und gibt
strukturiertes JSON zurück (output_config.format). Dadurch ist der Bericht
jeden Monat gleich aufgebaut und die Zahlen stammen nie aus der KI.
"""
import datetime as dt
import html
import json
from pathlib import Path
from string import Template

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]

SCHEMA = {
    "type": "object",
    "properties": {
        "zusammenfassung": {"type": "string"},
        "highlights": {"type": "array", "items": {"type": "string"}},
        "todos": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "titel": {"type": "string"},
                "url": {"type": "string"},
                "was_tun": {"type": "string"},
                "warum": {"type": "string"},
                "vorschlag": {"type": "string"},
                "minuten": {"type": "integer"},
            },
            "required": ["titel", "url", "was_tun", "warum", "vorschlag", "minuten"],
            "additionalProperties": False,
        }},
        "naechster_monat": {"type": "string"},
    },
    "required": ["zusammenfassung", "highlights", "todos", "naechster_monat"],
    "additionalProperties": False,
}

SYSTEM = """Du schreibst den monatlichen SEO-Zwischenstand einer Agentur für ihre Kundin,
eine Psychotherapeutin mit eigener Praxis-Website. Die Kundin ist keine SEO-Expertin
und hat wenig Zeit.

Regeln:
- Deutsch, {anrede}, warm und klar, keine Fachbegriffe ohne kurze Erklärung.
- Verwende ausschließlich die Zahlen aus den Daten. Erfinde nichts.
- highlights: 2–4 positive, konkrete Punkte (was gut funktioniert hat und warum).
- todos: genau die übergebenen kunden_todos, in derselben Reihenfolge. Pro To-do:
  was_tun = eine konkrete Handlung in einem Satz;
  vorschlag = ein fertiger Formulierungsvorschlag (z. B. neue Überschrift oder 2–3 Stichpunkte,
  welche Fragen ergänzt werden könnten), damit sie möglichst wenig selbst schreiben muss;
  minuten = realistische Zeit (10–45).
- Fachlich/ethisch: keine Heilversprechen, keine reißerischen Formulierungen,
  Berufsrecht für Psychotherapeut:innen beachten (sachlich, keine Werbung mit Erfolgsgarantien).
- Technische Aufgaben (Meta-Beschreibungen, Alt-Texte) erledigt die Agentur – nicht als To-do der Kundin.
- naechster_monat: 1–2 Sätze, was die Agentur als Nächstes beobachtet/tut.
"""


def monatsname(start: dt.date) -> str:
    return f"{MONATE[start.month - 1]} {start.year}"


def texte_mit_claude(auswertung: dict, monat: str, anrede: str = "Sie-Form") -> dict:
    import anthropic

    client = anthropic.Anthropic()  # liest ANTHROPIC_API_KEY aus der Umgebung
    with client.beta.messages.stream(
        model="claude-opus-5-5",
        max_tokens=16000,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        # Falls ein Sicherheitsfilter ablehnt, übernimmt automatisch ein anderes Modell
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM.format(anrede=anrede),
        messages=[{"role": "user", "content":
                   f"Berichtsmonat: {monat}\n\nAuswertung (JSON):\n"
                   + json.dumps(auswertung, ensure_ascii=False, default=str)}],
    ) as stream:
        antwort = stream.get_final_message()

    if antwort.stop_reason == "refusal":
        raise RuntimeError("Claude hat die Anfrage abgelehnt – bitte Daten prüfen.")
    if antwort.stop_reason == "max_tokens":
        raise RuntimeError("Antwort wurde abgeschnitten (max_tokens).")
    text = next(b.text for b in antwort.content if b.type == "text")
    return json.loads(text)


def texte_ohne_ki(auswertung: dict, monat: str) -> dict:
    """Einfache Fassung ohne API – zum Lernen und Testen."""
    g = auswertung["gesamt"]
    todos = [{
        "titel": t["seite"]["titel"], "url": t["seite"]["url"],
        "was_tun": {"ergänzen": "Beitrag um 2–3 Absätze ergänzen",
                    "wording": "Überschrift und ersten Absatz überarbeiten",
                    "aktualisieren": "Beitrag durchlesen und aktualisieren"}[t["art"]],
        "warum": t["grund"], "vorschlag": "(Formulierungsvorschlag kommt mit KI-Modus)", "minuten": 20,
    } for t in auswertung["kunden_todos"]]
    return {
        "zusammenfassung": f"Im {monat} kamen {g['klicks']} Besuche über Google "
                           f"bei {g['impressionen']} Einblendungen in den Suchergebnissen.",
        "highlights": [f"„{s['titel']}“: {s['klicks']} Klicks" for s in auswertung["top_seiten"][:3]],
        "todos": todos,
        "naechster_monat": "Wir beobachten die Entwicklung und melden uns zum nächsten Zwischenstand.",
    }


# ---------- HTML ----------
# Das Aussehen steht in vorlage.html; hier werden nur die Platzhalter befüllt.

VORLAGE = Path(__file__).with_name("vorlage.html")
ART = {"ergänzen": "Ergänzen", "wording": "Wording", "aktualisieren": "Aktualisieren"}


def _e(x) -> str:
    return html.escape(str(x))


def _tausender(zahl: int) -> str:
    return f"{zahl:,}".replace(",", ".")


def _prozent(anteil: float) -> str:
    return f"{abs(anteil) * 100:.0f} %"


def _trend(s: dict) -> str:
    if s.get("trend") is None:
        return "<td class='n muted'>–</td>"
    hoch = s["trend"] >= 0
    return f"<td class='n {'up' if hoch else 'down'}'>{'▲' if hoch else '▼'} {_prozent(s['trend'])}</td>"


def _kpi(titel: str, jetzt: int, vorher: int | None, monat: str, vormonat: str) -> str:
    vergleich = ""
    if vorher:
        d = (jetzt - vorher) / vorher
        breite = round(100 * min(vorher, jetzt) / max(vorher, jetzt))
        b_vorher, b_jetzt = (breite, 100) if jetzt >= vorher else (100, breite)
        vergleich = (
            f"<div class='delta {'up' if d >= 0 else 'down'}'>{'▲' if d >= 0 else '▼'} {_prozent(d)} zum {_e(vormonat)}</div>"
            f"<div class='bars'><div>{_e(vormonat)} <span class='track'><i style='width:{b_vorher}%'></i></span></div>"
            f"<div>{_e(monat)} <span class='track'><i style='width:{b_jetzt}%'></i></span></div></div>")
    return (f"<div class='kpi'><div class='muted small'>{titel}</div>"
            f"<div class='num'>{_tausender(jetzt)}</div>{vergleich}</div>")


def html_bericht(texte: dict, auswertung: dict, start: dt.date, praxis: str, gruss: str = "Viele Grüße") -> str:
    g = auswertung["gesamt"]
    monat = MONATE[start.month - 1]
    vormonat = MONATE[start.month - 2]
    folgemonat = MONATE[start.month % 12]
    arten = [t["art"] for t in auswertung["kunden_todos"]]

    todos = "".join(
        f"""<li class="todo"><label><input type="checkbox" id="todo-{i}" data-todo="{i}"> {_e(t['was_tun'])}</label>
      <div class="meta"><a href="{_e(t['url'])}">{_e(t['titel'])}</a><span class="chip">ca. {int(t['minuten'])} Min.</span>"""
        + (f"<span class='chip'>{ART.get(arten[i], '')}</span>" if i < len(arten) else "")
        + f"""</div>
      <p>{_e(t['warum'])}</p>
      <div class="suggest"><b>Vorschlag</b>{_e(t['vorschlag'])}</div></li>"""
        for i, t in enumerate(texte["todos"])
    ) or "<li class='todo'>Diesen Monat gibt es nichts zu tun. Alles läuft.</li>"

    seiten = "".join(
        f"<tr><td><a href='{_e(s['url'])}'>{_e(s['titel'])}</a></td><td class='n'>{s['klicks']}</td>{_trend(s)}"
        f"<td class='n'>{_tausender(s['impressionen'])}</td><td class='n'>{str(s['position']).replace('.', ',')}</td></tr>"
        for s in auswertung["top_seiten"])

    anfragen = "".join(f"<span class='q'>{_e(a['key'])} <span>{int(a['clicks'])}</span></span>"
                       for a in auswertung["top_anfragen"][:8])

    n = len(auswertung["agentur_todos"])
    agentur = (f"{n} technische Kleinigkeit{'en' if n != 1 else ''} erledigen wir im Hintergrund, "
               "zum Beispiel Bildbeschreibungen und die Kurzbeschreibungen, die Google unter Ihren Seiten anzeigt."
               if n else "Technisch ist gerade alles in Ordnung.")

    return Template(VORLAGE.read_text(encoding="utf-8")).substitute(
        id=f"{start:%Y-%m}",
        monat=_e(f"{monat} {start.year}"),
        folgemonat=_e(folgemonat),
        praxis=_e(praxis or "Ihre Praxis"),
        zusammenfassung=_e(texte["zusammenfassung"]),
        kpis=_kpi("Besuche über Google", g["klicks"], g.get("klicks_vorher"), monat, vormonat)
        + _kpi("Einblendungen in der Google-Suche", g["impressionen"], g.get("impressionen_vorher"), monat, vormonat),
        highlights="".join(f"<li>{_e(h)}</li>" for h in texte["highlights"]),
        todos=todos,
        seiten=seiten,
        anfragen=anfragen or "<span class='muted'>Keine Daten</span>",
        agentur=_e(agentur),
        naechster_monat=_e(texte["naechster_monat"]),
        gruss=_e(gruss),
    )
