# SEO-Bericht per WhatsApp – Lernprojekt

Monatlicher SEO-Zwischenstand für eine Kunden-Website, automatisiert:

```
Du schreibst "seo" per WhatsApp
   ↓
Search Console + WordPress abfragen  →  feste Regeln werten aus  →  Claude formuliert
   ↓
WhatsApp an dich: "Bericht fertig, Link … – ja/nein?"
   ↓
"ja"  →  Kundin bekommt den Link per WhatsApp-Vorlage
```

Die Kundin bekommt eine Seite mit: Zahlen im Vergleich zum Vormonat, was gut lief,
**max. 5 To-dos mit fertigen Formulierungsvorschlägen und Zeitangabe**, und dem Hinweis,
was die Agentur selbst erledigt. Ziel: so wenig Arbeit wie möglich – für sie und für dich.

## Aufbau (eine Datei pro Schritt)

| Datei | Was sie macht | Phase |
|---|---|---|
| `seo_bericht/gsc.py` | Search-Console-Daten: aus CSV-Export **oder** über die API | 1 + 2 |
| `seo_bericht/wordpress.py` | Beiträge lesen: Wortzahl, Alter, Meta-Beschreibung, Alt-Texte | 2 |
| `seo_bericht/analyse.py` | **Die Regeln**: was ist ein To-do, was ein Highlight (ohne KI) | 1 |
| `seo_bericht/bericht.py` | Claude schreibt die Texte, Python baut die HTML-Seite | 3 |
| `seo_bericht/whatsapp.py` | Nachrichten senden über die WhatsApp Cloud API | 4 |
| `seo_bericht/server.py` | Empfängt deine WhatsApp-Befehle, liefert Berichte aus | 4 + 5 |
| `seo_bericht/ablauf.py` | Verbindet alles zu einem Ablauf | – |

## Einrichten

```bash
cd seo-bericht
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Zugangsdaten kommen NUR hier rein
python -m seo_bericht demo --ohne-ki   # → berichte/demo.html im Browser öffnen
```

---

## Phase 1 – Von Hand verstehen  ☐

**Lernen:** Was bedeuten Klicks, Impressionen, CTR (Klickrate) und Position?

- *Impressionen* = wie oft die Seite in Google angezeigt wurde
- *Klicks* = wie oft jemand draufgeklickt hat
- *CTR* = Klicks ÷ Impressionen. Niedrig bei vielen Impressionen → Überschrift überzeugt nicht
- *Position* = durchschnittlicher Platz. 1–10 = Seite 1. **8–20 = der größte schnelle Hebel**

**Machen:**
1. ☐ `python -m seo_bericht demo --ohne-ki` ausführen, `berichte/demo.html` ansehen
2. ☐ `seo_bericht/analyse.py` lesen – die Regeln stehen oben im Kommentar. Passen sie für dich?
3. ☐ Search Console → Leistung → Zeitraum „Letzter Monat“ (bzw. benutzerdefiniert) → **Exportieren → CSV**.
   ZIP entpacken nach `daten/2026-09/`. Dasselbe für den Monat davor nach `daten/2026-08/`
4. ☐ `python -m seo_bericht bericht --csv daten/2026-09 --vergleich daten/2026-08 --ohne-ki --ohne-wp`
   → erster echter Bericht (ohne Texte von Claude)

## Phase 2 – Daten automatisch holen  ☐

**Lernen:** API = eine Schnittstelle, über die Programme Daten abfragen. Statt Passwort
gibt es *Schlüssel* (Token), die man einzeln widerrufen kann.

**Search Console API:**
1. ☐ [console.cloud.google.com](https://console.cloud.google.com) → neues Projekt
2. ☐ „APIs & Dienste“ → **Google Search Console API** aktivieren
3. ☐ „IAM → Dienstkonten“ → Dienstkonto anlegen → Schlüssel → JSON herunterladen →
   speichern als `geheim/service-account.json`
4. ☐ In der Search Console der Kunden-Property: Einstellungen → Nutzer → die
   E-Mail des Dienstkontos (…@….iam.gserviceaccount.com) mit Berechtigung **Eingeschränkt** hinzufügen
5. ☐ In `.env`: `GSC_PROPERTY` (z. B. `sc-domain:example.de`) und `GOOGLE_SERVICE_ACCOUNT_JSON`

**WordPress:**
1. ☐ WP-Admin → Benutzer → **eigenen Benutzer** für die Agentur anlegen (Rolle: Redakteur reicht)
2. ☐ Profil → **Anwendungspasswörter** → Name „SEO-Bericht“ → erzeugen
3. ☐ In `.env`: `WP_SITE`, `WP_USER`, `WP_APP_PASSWORD`

**Testen:** `python -m seo_bericht bericht --ohne-ki` (jetzt ohne `--csv`)

## Phase 3 – Claude schreibt den Bericht  ☐

**Lernen:** Die KI bekommt nur die fertige Auswertung als JSON und muss in einem festen
Schema antworten (`SCHEMA` in `bericht.py`). Darum stimmen die Zahlen immer, und der
Bericht sieht jeden Monat gleich aus. Den Ton steuerst du in `SYSTEM` – dort steht auch:
keine Heilversprechen, Berufsrecht beachten.

1. ☐ API-Schlüssel auf [console.anthropic.com](https://console.anthropic.com) erstellen → `ANTHROPIC_API_KEY` in `.env`
2. ☐ `python -m seo_bericht demo` (jetzt mit KI) – Formulierungsvorschläge ansehen
3. ☐ `SYSTEM` in `bericht.py` anpassen, bis dir der Ton gefällt (Du/Sie über `ANREDE`)

Kosten: ein Bericht kostet wenige Cent.

## Phase 4 – WhatsApp anbinden  ☐

**Lernen:**
- *Webhook* = Meta ruft deinen Server auf, sobald eine Nachricht ankommt
- *24-Stunden-Fenster*: Hat dir jemand geschrieben, darfst du 24 h frei antworten.
  Schreibst du zuerst (an die Kundin), brauchst du eine **freigegebene Vorlage**

**Einrichten:**
1. ☐ [developers.facebook.com](https://developers.facebook.com) → App erstellen (Typ „Business“) → Produkt **WhatsApp** hinzufügen
2. ☐ Eine **eigene Nummer** für den Bot hinterlegen (nicht deine private WhatsApp-Nummer – die
   kann danach nicht mehr normal genutzt werden). Für erste Tests reicht die Testnummer von Meta
3. ☐ Dauerhaften Token erstellen (Business-Einstellungen → Systemnutzer) → `WHATSAPP_TOKEN`;
   Telefonnummer-ID → `WHATSAPP_PHONE_NUMBER_ID`; App-Geheimnis (App-Einstellungen → Allgemein) → `WHATSAPP_APP_SECRET`
4. ☐ `MEINE_WHATSAPP` in `.env` eintragen, dann `python -m seo_bericht whatsapp-test`
   (vorher selbst einmal an die Bot-Nummer schreiben, wegen des 24-h-Fensters)
5. ☐ Vorlage anlegen (WhatsApp Manager → Nachrichtenvorlagen), Name `seo_zwischenstand`, Kategorie *Utility*, Deutsch:
   > Hallo, Ihr SEO-Zwischenstand für {{1}} ist fertig: {{2}} – Viele Grüße
6. ☐ Server erreichbar machen:
   - zum Lernen am eigenen Rechner: `python -m seo_bericht server` + `cloudflared tunnel --url http://localhost:8000`
   - dauerhaft: kleiner Server (z. B. Hetzner, ca. 4 €/Monat) oder Render/Railway
7. ☐ Bei Meta → WhatsApp → Konfiguration: Webhook-URL `https://…/webhook`, Verify-Token = `WHATSAPP_VERIFY_TOKEN`,
   Feld **messages** abonnieren. `OEFFENTLICHE_URL` in `.env` setzen

**Testen:** „seo“ an die Bot-Nummer schreiben → Link kommt → „nein“.

## Phase 5 – Freigabe & Kundin  ☐

- ☐ Kundin fragen, ob WhatsApp für sie okay ist (sonst E-Mail) und `KUNDIN_WHATSAPP` setzen
- ☐ Einmal komplett: „seo“ → Bericht prüfen → „ja“
- ☐ Optional später: automatisch am 2. jedes Monats (Cronjob), dann brauchst du auch für dich eine Vorlage

## Sicherheit & Datenschutz

- `.env`, `geheim/`, `daten/` und `berichte/` stehen in `.gitignore` – **nie committen**.
  Dieses Repo ist evtl. öffentlich (GitHub-Profil-Repo)!
- Der Server reagiert nur auf **deine** Nummer und prüft die Meta-Signatur jeder Nachricht.
- Berichte haben einen zufälligen, nicht erratbaren Link. Sie enthalten nur
  SEO-Zahlen – **keine Patientendaten**. Trotzdem: Auftragsverarbeitung mit der Kundin klären.
- Zugangsdaten nie per Chat verschicken; geteilte Passwörter danach ändern.
