"""Erzeugt INV000010 und INV000011."""

import os
from make_invoice import build, wrap, BOLD

OUT = os.path.dirname(os.path.abspath(__file__))
DATE = "25.08.2026"

INV000010 = {
    "invoice_no": "INV000010",
    "date": DATE,
    "recipient": ["Jenny Dressel", "Nonnenstraße 5e", "04229 Leipzig"],
    "salutation": "Liebe Jenny Dressel,",
    "intro": [
        "wie besprochen sende ich dir hiermit die Abrechnung für meine erbrachten Leistungen im Rahmen der Wartung der Websites",
        '"https://frauenmitoptionen.com/fem-zone" und  "https://aktienfuerfrauen.de/fem-zone/".',
        "Ich stelle die Leistungen wie folgt gemäß Beauftragung in Rechnung:",
    ],
    "items": [
        {
            "no": "1.",
            "lines": [
                ("Basis-Paket – Laufende Wartung & Sicherheit", True),
                ("Grundwartung beider Websites (WordPress + Elemen-", True),
                ("tor):", True),
                ("• Regelmäßige Plugin- und Systemupdates", True),
                ("• Sicherheits- & Backup-Kontrolle (Funktionstest nach", True),
                ("Updates)", True),
                ("• Überprüfung von defekten Links, Formularen und", True),
                ("Ladezeiten", True),
                ("• Kleinere Content- oder Designanpassungen (nach Ab-", True),
                ("sprache + ggfls Aufpreis)", True),
                ("• Technische Unterstützung per E-Mail oder WhatsApp", True),
            ],
            "kosten": "60", "stueck": "2", "gesamt": "120",
        },
    ],
    "closing": "Ich bedanke mich vielmals für die Möglichkeit zur Zusammenarbeit und freue mich auf weitere gemeinsame Projekte.",
    "total": "120 €",
}




def _b(text, bold=True):
    """Umgebrochene Zeilen mit einheitlicher Fett-/Normal-Auszeichnung."""
    from make_invoice import BOLD, REG
    return [(line, bold) for line in wrap(text, font=BOLD if bold else REG)]


INV000011 = {
    "invoice_no": "INV000011",
    "date": DATE,
    "recipient": ["Conny Jakober", "Im Hausgrün 12", "79312 Emmendingen"],
    "salutation": "Liebe Conny Jakober,",
    "intro": [
        "wie besprochen sende ich dir hiermit die Abrechnung für meine erbrachten Leistungen im Rahmen der Domain- und",
        'SEO-Betreuung deiner Website "https://jakober-psychotherapie.de".',
        "Ich stelle die Leistungen wie folgt gemäß Beauftragung in Rechnung:",
    ],
    "items": [
        {
            "no": "1.",
            "lines": (
                _b("Domain- & SEO-Betreuung – Laufzeit 12 Monate")
                + _b("(August 2026 bis Juli 2027) für die Website")
                + _b('"https://jakober-psychotherapie.de":')
                + _b("• Domainverwaltung inkl. jährlicher Verlängerung")
                + _b("• Laufende SEO-Betreuung und Optimierung der Inhalte, Meta-Angaben und Seitenstruktur")
                + _b("• Einrichtung und Anbindung der Google-Dienste (Google Search Console, Google Analytics, Google Unternehmensprofil)")
                + _b("• Überwachung von Indexierung, Rankings und Ladezeiten")
                + _b("• Technische Unterstützung per E-Mail oder WhatsApp")
            ),
            "kosten": "250", "stueck": "1", "gesamt": "250",
        },
    ],
    "closing": "Ich bedanke mich vielmals für die Möglichkeit zur Zusammenarbeit und freue mich auf weitere gemeinsame Projekte.",
    "total": "250 €",
}

if __name__ == "__main__":
    for spec in (INV000010, INV000011):
        path = build(spec, os.path.join(OUT, spec["invoice_no"] + ".pdf"))
        print("erzeugt:", path)
