"""WhatsApp Business Cloud API (Meta) – Nachrichten senden.

Lernpunkte:
  - Innerhalb von 24 h, nachdem jemand DIR geschrieben hat, darfst du freien Text senden.
  - Schreibst du zuerst (z. B. an die Kundin), brauchst du eine von Meta freigegebene
    Nachrichtenvorlage ("Template") mit Platzhaltern {{1}}, {{2}} …
"""
import hashlib
import hmac

import requests

from . import config


def _url() -> str:
    version = config.get("WHATSAPP_API_VERSION", "v22.0")
    nummer_id = config.get("WHATSAPP_PHONE_NUMBER_ID", pflicht=True)
    return f"https://graph.facebook.com/{version}/{nummer_id}/messages"


def _senden(nutzlast: dict) -> dict:
    r = requests.post(_url(), json={"messaging_product": "whatsapp", **nutzlast},
                      headers={"Authorization": f"Bearer {config.get('WHATSAPP_TOKEN', pflicht=True)}"},
                      timeout=30)
    if not r.ok:
        raise RuntimeError(f"WhatsApp-Fehler {r.status_code}: {r.text}")
    return r.json()


def text(an: str, nachricht: str) -> dict:
    """Freier Text – nur innerhalb des 24-h-Fensters."""
    return _senden({"to": an, "type": "text", "text": {"body": nachricht, "preview_url": True}})


def vorlage(an: str, name: str, parameter: list[str], sprache: str = "de") -> dict:
    """Freigegebene Vorlage – funktioniert immer, auch als erste Nachricht."""
    return _senden({"to": an, "type": "template", "template": {
        "name": name, "language": {"code": sprache},
        "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parameter]}],
    }})


def signatur_ok(rohdaten: bytes, signatur_header: str | None) -> bool:
    """Prüft, dass ein Webhook wirklich von Meta kommt (X-Hub-Signature-256)."""
    geheimnis = config.get("WHATSAPP_APP_SECRET", pflicht=True)
    erwartet = "sha256=" + hmac.new(geheimnis.encode(), rohdaten, hashlib.sha256).hexdigest()
    return hmac.compare_digest(erwartet, signatur_header or "")


def eingehende_texte(daten: dict):
    """Zieht (absender, text) aus dem Webhook-JSON von Meta."""
    for eintrag in daten.get("entry", []):
        for aenderung in eintrag.get("changes", []):
            for msg in aenderung.get("value", {}).get("messages", []):
                if msg.get("type") == "text":
                    yield msg["from"], msg["text"]["body"].strip()
                elif msg.get("type") == "button":  # Antwort-Button einer Vorlage
                    yield msg["from"], msg["button"]["text"].strip()
