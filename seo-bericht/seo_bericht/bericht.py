"""Bericht schreiben: Claude formuliert, Python baut die HTML-Seite.

Lernpunkt: Claude bekommt NUR die fertige Auswertung (Zahlen + Regeln) und gibt
strukturiertes JSON zurück (output_config.format). Dadurch ist der Bericht
jeden Monat gleich aufgebaut und die Zahlen stammen nie aus der KI.
"""
import datetime as dt
import html
import json

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

def _e(x) -> str:
    return html.escape(str(x))


def _trend(s: dict) -> str:
    if s.get("trend") is None:
        return ""
    pfeil = "▲" if s["trend"] >= 0 else "▼"
    klasse = "plus" if s["trend"] >= 0 else "minus"
    return f'<span class="{klasse}">{pfeil} {abs(s["trend"]):.0%}</span>'


def _kpi(titel: str, jetzt: int, vorher: int | None) -> str:
    delta = ""
    if vorher:
        d = (jetzt - vorher) / vorher
        delta = f'<div class="{"plus" if d >= 0 else "minus"}">{"▲" if d >= 0 else "▼"} {abs(d):.0%} zum Vormonat</div>'
    return f'<div class="kpi"><div class="label">{titel}</div><div class="wert">{jetzt:,}</div>{delta}</div>'.replace(",", ".")


def html_bericht(texte: dict, auswertung: dict, monat: str, praxis: str) -> str:
    g = auswertung["gesamt"]
    zeilen = "".join(
        f"<tr><td><a href='{_e(s['url'])}'>{_e(s['titel'])}</a></td>"
        f"<td class='zahl'>{s['klicks']} {_trend(s)}</td><td class='zahl'>{s['impressionen']}</td>"
        f"<td class='zahl'>{str(s['position']).replace('.', ',')}</td></tr>" for s in auswertung["top_seiten"])
    anfragen = "".join(f"<li>{_e(a['key'])} <span class='leise'>({int(a['clicks'])} Klicks)</span></li>"
                       for a in auswertung["top_anfragen"][:6])
    todos = "".join(
        f"""<li class="todo"><label><input type="checkbox"> <strong>{_e(t['was_tun'])}</strong></label>
        <div class="leise"><a href="{_e(t['url'])}">{_e(t['titel'])}</a> · ca. {t['minuten']} Min.</div>
        <p>{_e(t['warum'])}</p><div class="vorschlag"><b>Vorschlag:</b> {_e(t['vorschlag'])}</div></li>"""
        for t in texte["todos"]) or "<li>Diesen Monat nichts zu tun – alles läuft. 🎉</li>"
    highlights = "".join(f"<li>{_e(h)}</li>" for h in texte["highlights"])
    agentur = len(auswertung["agentur_todos"])

    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO-Zwischenstand {_e(monat)}</title>
<style>
:root{{--bg:#faf8f5;--karte:#fff;--text:#2b2b2b;--leise:#6b6b6b;--akzent:#4a7c74;--plus:#2e7d4f;--minus:#b4543a;--linie:#e8e3dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1c1d1f;--karte:#26282b;--text:#eee;--leise:#a5a5a5;--akzent:#7fb5ab;--plus:#6fcf97;--minus:#f2a08a;--linie:#3a3d41}}}}
body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:760px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:1.6rem;margin:0}} h2{{font-size:1.15rem;margin:2rem 0 .75rem;color:var(--akzent)}}
.leise{{color:var(--leise);font-size:.9rem}} a{{color:var(--akzent)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:1.5rem}}
.kpi,.karte{{background:var(--karte);border:1px solid var(--linie);border-radius:12px;padding:16px}}
.kpi .wert{{font-size:1.8rem;font-weight:650}} .plus{{color:var(--plus)}} .minus{{color:var(--minus)}}
table{{width:100%;border-collapse:collapse;font-size:.95rem}} td,th{{padding:8px 6px;border-bottom:1px solid var(--linie);text-align:left}}
.zahl{{text-align:right;white-space:nowrap}} th.zahl{{text-align:right}}
.todos{{list-style:none;padding:0;margin:0;display:grid;gap:12px}}
.todo{{background:var(--karte);border:1px solid var(--linie);border-left:4px solid var(--akzent);border-radius:12px;padding:14px 16px}}
.todo p{{margin:.4rem 0}} .vorschlag{{background:var(--bg);border-radius:8px;padding:10px 12px;font-size:.95rem}}
@media print{{.todo input{{display:none}}}}
</style></head><body><main>
<div class="leise">{_e(praxis)}</div>
<h1>SEO-Zwischenstand {_e(monat)}</h1>
<p>{_e(texte['zusammenfassung'])}</p>
<div class="kpis">{_kpi("Besuche über Google", g['klicks'], g.get('klicks_vorher'))}
{_kpi("Einblendungen bei Google", g['impressionen'], g.get('impressionen_vorher'))}</div>

<h2>Was gut funktioniert hat</h2><ul>{highlights}</ul>

<h2>Ihre To-dos ({len(texte['todos'])})</h2>
<p class="leise">Nach Wirkung sortiert – wenn nur Zeit für eins ist: das erste.</p>
<ul class="todos">{todos}</ul>

<h2>Die stärksten Seiten</h2>
<div class="karte"><table><tr><th>Seite</th><th class="zahl">Klicks</th><th class="zahl">Einblendungen</th><th class="zahl">Ø Position</th></tr>{zeilen}</table></div>

<h2>Wonach gesucht wurde</h2><ul>{anfragen}</ul>

<h2>Das übernehmen wir</h2>
<p>{agentur} technische Kleinigkeit(en) (z. B. Bildbeschreibungen, Suchmaschinen-Texte) erledigen wir im Hintergrund.
{_e(texte['naechster_monat'])}</p>
</main></body></html>"""
