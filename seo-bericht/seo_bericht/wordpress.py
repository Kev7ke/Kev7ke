"""WordPress: Beiträge und Seiten über die REST-API lesen (nur lesen, nichts ändern).

Lernpunkt: Statt des Admin-Passworts nutzen wir ein *Anwendungspasswort*
(WordPress → Benutzer → Profil → Anwendungspasswörter). Das kann man jederzeit
widerrufen, ohne das echte Login zu ändern.
"""
import datetime as dt
import html
import re

import requests

FELDER = "id,link,title,date,modified,content,yoast_head_json"


def _alle(site: str, typ: str, auth) -> list[dict]:
    eintraege, seite = [], 1
    while True:
        r = requests.get(f"{site.rstrip('/')}/wp-json/wp/v2/{typ}",
                         params={"per_page": 100, "page": seite, "_fields": FELDER},
                         auth=auth, timeout=30)
        if r.status_code == 400 and seite > 1:  # keine weiteren Seiten
            break
        r.raise_for_status()
        eintraege += r.json()
        if seite >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        seite += 1
    return eintraege


def _text(html_inhalt: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", html_inhalt or ""))


def _bilder_ohne_alt(html_inhalt: str) -> int:
    bilder = re.findall(r"<img\b[^>]*>", html_inhalt or "", flags=re.I)
    return sum(1 for b in bilder if not re.search(r'\balt\s*=\s*"[^"]+"', b, flags=re.I))


def hole_inhalte(site: str, user: str | None, app_passwort: str | None) -> list[dict]:
    auth = (user, app_passwort) if user and app_passwort else None
    inhalte = []
    for typ in ("posts", "pages"):
        for e in _alle(site, typ, auth):
            inhalt = e.get("content", {}).get("rendered", "")
            yoast = e.get("yoast_head_json") or {}
            inhalte.append({
                "typ": "Beitrag" if typ == "posts" else "Seite",
                "titel": html.unescape(e["title"]["rendered"]),
                "url": e["link"],
                "veroeffentlicht": e["date"][:10],
                "geaendert": e["modified"][:10],
                "woerter": len(_text(inhalt).split()),
                "bilder_ohne_alt": _bilder_ohne_alt(inhalt),
                # None = unbekannt (kein Yoast), "" = fehlt
                "meta_beschreibung": yoast.get("description") if yoast else None,
                "seo_titel": yoast.get("title") if yoast else None,
            })
    return inhalte


def monate_seit(datum: str, heute: dt.date | None = None) -> int:
    heute = heute or dt.date.today()
    d = dt.date.fromisoformat(datum)
    return (heute.year - d.year) * 12 + heute.month - d.month
