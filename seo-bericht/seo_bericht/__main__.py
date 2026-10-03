"""Aufruf:  python -m seo_bericht <befehl>

  demo                         Beispielbericht aus Testdaten (ohne Zugangsdaten)
  bericht [--csv ORDNER]       echter Bericht für den Vormonat
          [--vergleich ORDNER] CSV des Monats davor (für Trends)
          [--ohne-ki]          ohne Claude (nur Zahlen)
          [--ohne-wp]          ohne WordPress-Daten
  whatsapp-test                schickt dir "Hallo" per WhatsApp
  server                       startet den Webhook-Server für WhatsApp
"""
import argparse

from . import ablauf, config


def main() -> None:
    p = argparse.ArgumentParser(prog="seo_bericht", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("befehl", choices=["demo", "bericht", "whatsapp-test", "server"])
    p.add_argument("--csv")
    p.add_argument("--vergleich")
    p.add_argument("--ohne-ki", action="store_true")
    p.add_argument("--ohne-wp", action="store_true")
    a = p.parse_args()

    if a.befehl == "demo":
        beispiel = config.PROJEKT / "beispiel"
        b = ablauf.erstelle_bericht(csv=beispiel / "september", csv_vergleich=beispiel / "august",
                                    mit_wp=False, mit_ki=not a.ohne_ki, dateiname="demo")
        print(f"Fertig: {b['pfad']}  ({b['todos']} To-dos)")
    elif a.befehl == "bericht":
        b = ablauf.erstelle_bericht(csv=a.csv, csv_vergleich=a.vergleich,
                                    mit_wp=not a.ohne_wp, mit_ki=not a.ohne_ki)
        print(f"Fertig: {b['pfad']}  ({b['todos']} To-dos)")
    elif a.befehl == "whatsapp-test":
        from . import whatsapp
        print(whatsapp.text(config.get("MEINE_WHATSAPP", pflicht=True), "Hallo 👋 – der SEO-Bot funktioniert."))
    elif a.befehl == "server":
        from . import server
        server.starten()


if __name__ == "__main__":
    main()
