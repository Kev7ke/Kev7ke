"""Kleiner Webserver: empfängt WhatsApp-Nachrichten und liefert Berichte aus.

Befehle per WhatsApp (nur von DEINER Nummer, alle anderen werden ignoriert):
  seo   → Bericht für den Vormonat erstellen, du bekommst den Link
  ja    → letzten Bericht an die Kundin schicken
  nein  → letzten Bericht verwerfen
  hilfe → Befehle anzeigen
"""
import json
import threading

from flask import Flask, abort, request

from . import ablauf, config, whatsapp

app = Flask(__name__)
STATUS = ablauf.BERICHTE / "offen.json"
HILFE = "Befehle: *seo* (Bericht erstellen), *ja* (an Kundin senden), *nein* (verwerfen)."


def _offen() -> dict | None:
    return json.loads(STATUS.read_text()) if STATUS.exists() else None


def _bericht_bauen(an: str) -> None:
    try:
        b = ablauf.erstelle_bericht()
        ablauf.BERICHTE.mkdir(exist_ok=True)
        STATUS.write_text(json.dumps({"name": b["name"], "monat": b["monat"]}))
        whatsapp.text(an, f"✅ SEO-Bericht {b['monat']} ist fertig ({b['klicks']} Klicks, "
                          f"{b['todos']} To-dos für die Kundin):\n{ablauf.link(b['name'])}\n\n"
                          "Antworte *ja* zum Senden an die Kundin oder *nein* zum Verwerfen.")
    except Exception as fehler:  # Fehler per WhatsApp melden statt still abzustürzen
        whatsapp.text(an, f"❌ Bericht fehlgeschlagen: {fehler}")


def _befehl(an: str, text: str) -> None:
    befehl = text.lower()
    if befehl in ("seo", "bericht"):
        whatsapp.text(an, "⏳ Erstelle den Bericht, dauert 1–2 Minuten …")
        threading.Thread(target=_bericht_bauen, args=(an,), daemon=True).start()
    elif befehl == "ja":
        offen = _offen()
        if not offen:
            return whatsapp.text(an, "Kein offener Bericht. Schreib *seo*, um einen zu erstellen.")
        whatsapp.vorlage(config.get("KUNDIN_WHATSAPP", pflicht=True),
                         config.get("WHATSAPP_VORLAGE_KUNDIN", "seo_zwischenstand"),
                         [offen["monat"], ablauf.link(offen["name"])])
        STATUS.unlink()
        whatsapp.text(an, f"📨 Bericht {offen['monat']} an die Kundin gesendet.")
    elif befehl == "nein":
        STATUS.unlink(missing_ok=True)
        whatsapp.text(an, "🗑️ Verworfen.")
    else:
        whatsapp.text(an, HILFE)


@app.get("/webhook")
def webhook_pruefen():
    """Einmalige Prüfung durch Meta beim Einrichten des Webhooks."""
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == config.get("WHATSAPP_VERIFY_TOKEN", pflicht=True)):
        return request.args.get("hub.challenge", "")
    abort(403)


@app.post("/webhook")
def webhook_empfangen():
    if not whatsapp.signatur_ok(request.get_data(), request.headers.get("X-Hub-Signature-256")):
        abort(403)
    ich = config.get("MEINE_WHATSAPP", pflicht=True)
    for absender, text in whatsapp.eingehende_texte(request.get_json(silent=True) or {}):
        if absender == ich:
            _befehl(absender, text)
    return "ok"  # Meta erwartet schnell eine 200-Antwort


@app.get("/b/<name>")
def bericht_zeigen(name: str):
    pfad = (ablauf.BERICHTE / f"{name}.html").resolve()
    if pfad.parent != ablauf.BERICHTE.resolve() or not pfad.exists():
        abort(404)
    return pfad.read_text(encoding="utf-8")


def starten() -> None:
    app.run(host="0.0.0.0", port=int(config.get("PORT", "8000")))
