"""Erzeugt Rechnungen im Layout von INV000009 (Webdevelopment Kevin Radtke)."""

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = 612, 792
LEFT = 41.0
RIGHT = 571.0

# Carlito ist metrisch kompatibel zu Calibri (Original-Schrift der Vorlage)
FONT_DIR = "/usr/share/fonts/truetype/crosextra"
REG, BOLD = "Calibri", "Calibri-Bold"
pdfmetrics.registerFont(TTFont(REG, f"{FONT_DIR}/Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont(BOLD, f"{FONT_DIR}/Carlito-Bold.ttf"))

BLACK = (0, 0, 0)
RED_TOTAL = (0.933, 0.177, 0.175)
RED_BANK = (0.823, 0.137, 0.164)

# Spaltenraster der Tabelle (aus der Vorlage übernommen)
COL_LINES = [41.25, 69.60, 308.40, 406.25, 489.05, 570.75]
COL_SEGS = [(41.0, 69.60), (69.60, 308.40), (308.40, 406.25),
            (406.25, 489.05), (489.05, 571.0)]
COL_TEXT = [45.25, 73.60, 312.40, 410.25, 493.05]

TABLE_TOP = 274.35          # y-Abstand von oben
ROW_FIRST_BASELINE = 11.5   # erste Textgrundlinie unter der Zeilenlinie
LEADING = 12.0
ROW_BOTTOM_PAD = 6.8

SENDER = "Webdevelopment Kevin Radtke | Taubestr. 7 | 04347 Leipzig |"
TAX_NO = "232/260/03975"
BANK_LINE_BLACK = "Bitte überweisen Sie den Rechnungsbetrag auf mein Konto der"
BANK_LINE_RED = " Sparkasse Minden Lübbecke mit der IBAN:"
IBAN = "DE31 4905 0101 0031 7874 68"
VAT_NOTE = ("(Als Kleinunternehmer im Sinne des § 19 Abs.1UstG entfällt "
            "die Berechnung & der Ausweis der Umsatzsteuer)")


def wrap(text, width=234.8 - 4.5, font=REG, size=10):
    """Bricht Text auf die Breite der Bezeichnungs-Spalte um."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and pdfmetrics.stringWidth(trial, font, size) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _txt(c, x, baseline, text, font=REG, size=10, color=BLACK):
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    c.drawString(x, baseline, text)
    return x + c.stringWidth(text, font, size)


def _txt_right(c, x_right, baseline, text, font=REG, size=10, color=BLACK):
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    c.drawRightString(x_right, baseline, text)


def _hline(c, top):
    y = PAGE_H - top
    for x0, x1 in COL_SEGS:
        c.line(x0, y, x1, y)


def _vlines(c, top, bottom):
    y0, y1 = PAGE_H - top - 0.25, PAGE_H - bottom + 0.25
    for x in COL_LINES:
        c.line(x, y0, x, y1)


def build(spec, out_path):
    c = canvas.Canvas(out_path, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(spec["invoice_no"])
    c.setAuthor("Kevin Radtke")

    # --- Kopf ---
    _txt(c, LEFT, 742.70, SENDER)
    for i, line in enumerate(spec["recipient"]):
        _txt(c, LEFT, 706.70 - i * 12.0, line)
    _txt_right(c, RIGHT, 658.70, f"Leipzig, {spec['date']}")

    x = _txt(c, LEFT, 646.70, "Rechnungsnummer:", font=BOLD)
    _txt(c, x, 646.70, " " + spec["invoice_no"])
    x = _txt(c, LEFT, 634.70, "Steuernummer:", font=BOLD)
    _txt(c, x, 634.70, " " + TAX_NO)

    # --- Anrede und Einleitung ---
    _txt(c, LEFT, 586.70, spec["salutation"], font=BOLD)
    for i, line in enumerate(spec["intro"]):
        _txt(c, LEFT, 562.70 - i * 12.0, line)

    # --- Tabelle ---
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)

    top = TABLE_TOP
    _hline(c, top)
    _vlines(c, top, top + 15.5)
    base = PAGE_H - top - ROW_FIRST_BASELINE
    for x, head in zip(COL_TEXT, ["Nr.", "Bezeichnung", "Kosten €", "Stück", "Gesamt - €"]):
        _txt(c, x, base, head, font=BOLD)
    top += 15.5

    for item in spec["items"]:
        lines = item["lines"]
        height = ROW_FIRST_BASELINE + (len(lines) - 1) * LEADING + ROW_BOTTOM_PAD
        _hline(c, top)
        _vlines(c, top, top + height)
        base = PAGE_H - top - ROW_FIRST_BASELINE
        _txt(c, COL_TEXT[0], base, item["no"], font=BOLD)
        for i, (text, bold) in enumerate(lines):
            _txt(c, COL_TEXT[1], base - i * LEADING, text, font=BOLD if bold else REG)
        for x, val in zip(COL_TEXT[2:], [item["kosten"], item["stueck"], item["gesamt"]]):
            _txt(c, x, base, val)
        top += height

    _hline(c, top)

    # --- Schlusssatz direkt unter der Tabelle ---
    _txt(c, LEFT, PAGE_H - top - 20.25, spec["closing"])

    # --- Fußbereich (feste Positionen wie in der Vorlage) ---
    _txt_right(c, RIGHT, 169.00, f"Rechnungsbetrag: {spec['total']}",
               font=BOLD, size=12, color=RED_TOTAL)
    _txt_right(c, RIGHT, 143.80, VAT_NOTE, size=9)
    _txt_right(c, RIGHT, 117.40, "Zahlungsbedingung: zahlbar sofort ohne Abzug")
    _txt(c, LEFT, 96.50, "Mit freundlichen Grüßen")
    _txt(c, LEFT, 82.10, "Kevin Radtke")
    x = _txt(c, LEFT, 53.30, BANK_LINE_BLACK, size=9)
    _txt(c, x, 53.30, BANK_LINE_RED, size=9, color=RED_BANK)
    _txt(c, LEFT, 42.50, IBAN, size=9, color=RED_BANK)

    c.showPage()
    c.save()
    return out_path
