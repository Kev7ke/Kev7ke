# -*- coding: utf-8 -*-
"""Erzeugt unterschriftsfertige selbstschuldnerische Mietbuergschaften
zum befristeten Untermietvertrag vom 10.08.2026 (Ehrenfeldstr. 25, 44789 Bochum)."""

import os

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Daten aus dem Untermietvertrag -----------------------------------------
GLAEUBIGER = "Sebastian Tigges, Ehrenfeldstr. 25, 44789 Bochum"
HAUPTSCHULDNER = "Kevin Radtke, Taubestr. 7, 04347 Leipzig"
MIETSACHE = ("Wohnung Ehrenfeldstr. 25, 44789 Bochum, 1. OG rechts "
             "(2 Zimmer, 1 Bad, 1 Flur, 1 Küche, ca. 47,5 m², möbliert)")
VERTRAGSDATUM = "10.08.2026"
MIETZEIT = "01.09.2026 bis 30.04.2027"
BETRAG_ZAHL = "960,00 €"
BETRAG_WORT = "neunhundertsechzig Euro"

BUERGEN = [
    {
        "datei": "Buergschaftserklaerung_Alexandra_Wiehe.pdf",
        "name": "Alexandra Wiehe",
        "strasse": "Fleggestr. 16",
        "ort": "32339 Espelkamp",
        "mitbuerge": "Volker Radtke, Leipziger Str. 40, 32339 Espelkamp",
    },
    {
        "datei": "Buergschaftserklaerung_Volker_Radtke.pdf",
        "name": "Volker Radtke",
        "strasse": "Leipziger Str. 40",
        "ort": "32339 Espelkamp",
        "mitbuerge": "Alexandra Wiehe, Fleggestr. 16, 32339 Espelkamp",
    },
]

# --- Stile -------------------------------------------------------------------
S_TITLE = ParagraphStyle("title", fontName="Times-Bold", fontSize=15, leading=19,
                         spaceAfter=2 * mm, alignment=1)
S_SUB = ParagraphStyle("sub", fontName="Times-Roman", fontSize=10.5, leading=14,
                       alignment=1, spaceAfter=7 * mm)
S_H = ParagraphStyle("h", fontName="Times-Bold", fontSize=11, leading=15,
                     spaceBefore=4 * mm, spaceAfter=1.5 * mm)
S_P = ParagraphStyle("p", fontName="Times-Roman", fontSize=10.5, leading=14.5,
                     alignment=TA_JUSTIFY, spaceAfter=2.5 * mm)
S_LI = ParagraphStyle("li", parent=S_P, leftIndent=6 * mm, bulletIndent=1.5 * mm,
                      spaceAfter=1.5 * mm)
S_SMALL = ParagraphStyle("small", fontName="Times-Roman", fontSize=8.5, leading=11.5)
S_LABEL = ParagraphStyle("label", fontName="Times-Roman", fontSize=9, leading=12)


def party_table(rows):
    t = Table(rows, colWidths=[38 * mm, 122 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Times-Bold", 10.5),
        ("FONT", (1, 0), (1, -1), "Times-Roman", 10.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def signature_block():
    line = "_" * 34
    rows = [
        [Paragraph(line, S_LABEL), "", Paragraph(line, S_LABEL)],
        [Paragraph("Ort, Datum", S_LABEL), "",
         Paragraph("Unterschrift des Bürgen / der Bürgin", S_LABEL)],
    ]
    t = Table(rows, colWidths=[72 * mm, 16 * mm, 72 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
    ]))
    return t


def build(b):
    path = os.path.join(OUT_DIR, b["datei"])
    doc = BaseDocTemplate(path, pagesize=A4,
                          leftMargin=25 * mm, rightMargin=25 * mm,
                          topMargin=20 * mm, bottomMargin=18 * mm,
                          title="Bürgschaftserklärung " + b["name"],
                          author=b["name"],
                          subject="Selbstschuldnerische Mietbürgschaft")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")

    def footer(canvas, docu):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.drawCentredString(A4[0] / 2.0, 11 * mm,
                                 "Bürgschaftserklärung – %s – Seite %d"
                                 % (b["name"], docu.page))
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])

    st = []
    st.append(Paragraph("Bürgschaftserklärung", S_TITLE))
    st.append(Paragraph("Unbedingte, unbefristete, unwiderrufliche und selbstschuldnerische "
                        "Höchstbetragsbürgschaft (Mietbürgschaft) "
                        "gemäß §§ 765 ff. BGB", S_SUB))

    st.append(party_table([
        ["Bürge/Bürgin:", Paragraph("<b>%s</b><br/>%s<br/>%s"
                                              % (b["name"], b["strasse"], b["ort"]), S_P)],
        ["Gläubiger:", Paragraph("%s<br/><font size=9>– Vermieter "
                                      "(Hauptmieter) –</font>" % GLAEUBIGER, S_P)],
        ["Hauptschuldner:", Paragraph("%s<br/><font size=9>– Untermieter –</font>"
                                      % HAUPTSCHULDNER, S_P)],
    ]))
    st.append(Spacer(1, 5 * mm))

    st.append(Paragraph("1. Gesichertes Mietverhältnis", S_H))
    st.append(Paragraph(
        "Zwischen dem Gläubiger und dem Hauptschuldner besteht der befristete "
        "Untermietvertrag vom %s über die %s. Das Mietverhältnis läuft vom %s. "
        "Nach § 4 des Untermietvertrages hat der Untermieter eine Bürgschaft als "
        "Sicherheit zu stellen." % (VERTRAGSDATUM, MIETSACHE, MIETZEIT), S_P))

    st.append(Paragraph("2. Bürgschaftserklärung", S_H))
    st.append(Paragraph(
        "Hiermit übernehme ich, %s, gegenüber dem Gläubiger die "
        "<b>selbstschuldnerische Bürgschaft</b> für alle gegenwärtigen und "
        "künftigen Verbindlichkeiten des Hauptschuldners aus dem vorgenannten "
        "Untermietverhältnis, insbesondere für" % b["name"], S_P))
    for txt in ["rückständige Mieten, Betriebskostenpauschalen und "
                "Vorauszahlungen für Gas und Strom,",
                "Nachforderungen aus der Abrechnung der Energiekosten nach § 3 Abs. 4 "
                "des Untermietvertrages,",
                "Schadensersatz- und Nutzungsentschädigungsansprüche, "
                "einschließlich Ansprüchen wegen nicht zurückgegebener "
                "Schlüssel oder nicht vertragsgemäßer Rückgabe der Mietsache."]:
        st.append(Paragraph(txt, S_LI, bulletText="–"))

    st.append(Paragraph("3. Umfang und Höchstbetrag der Haftung", S_H))
    st.append(Paragraph(
        "Meine Haftung ist der Höhe nach begrenzt auf einen <b>Höchstbetrag von "
        "%s (in Worten: %s)</b>. Dieser Betrag entspricht der in § 4 Abs. 3 des "
        "Untermietvertrages vereinbarten Bürgschaftssumme und umfasst auch Zinsen "
        "sowie Kosten der Rechtsverfolgung." % (BETRAG_ZAHL, BETRAG_WORT), S_P))
    st.append(Paragraph(
        "Diese Bürgschaft wird zeitlich unbefristet, unbedingt und unwiderruflich "
        "übernommen. Ich verzichte auf die <b>Einrede der Vorausklage</b> "
        "(§ 771 BGB) sowie auf die Einreden der <b>Anfechtbarkeit und der "
        "Aufrechenbarkeit</b> (§ 770 BGB); der Verzicht auf die Einrede der "
        "Aufrechenbarkeit gilt nicht für unbestrittene oder rechtskräftig "
        "festgestellte Gegenforderungen des Hauptschuldners.", S_P))

    st.append(Paragraph("4. Mitbürgschaft", S_H))
    st.append(Paragraph(
        "Diese Bürgschaft wird neben einer gleichlautenden Bürgschaft von "
        "<b>%s</b> übernommen. Beide Bürgen haften dem Gläubiger als "
        "Gesamtschuldner (§ 769 BGB). Der Gläubiger kann aus beiden "
        "Bürgschaften zusammen jedoch insgesamt höchstens %s verlangen; "
        "Leistungen des einen Bürgen wirken in gleicher Höhe "
        "haftungsbefreiend für den anderen." % (b["mitbuerge"], BETRAG_ZAHL), S_P))

    st.append(Paragraph("5. Inanspruchnahme", S_H))
    st.append(Paragraph(
        "Der Gläubiger wird den Bürgen erst in Anspruch nehmen, nachdem er den "
        "Hauptschuldner in Textform erfolglos zur Zahlung aufgefordert hat. Die "
        "Inanspruchnahme aus dieser Bürgschaft bedarf der Textform unter Angabe der "
        "geltend gemachten Forderung.", S_P))

    st.append(Paragraph("6. Beendigung und Rückgabe der Urkunde", S_H))
    st.append(Paragraph(
        "Die Bürgschaft erlischt, sobald sämtliche gesicherten Ansprüche des "
        "Gläubigers aus dem Untermietverhältnis erfüllt sind, spätestens "
        "mit vollständiger Abwicklung des Mietverhältnisses einschließlich der "
        "Abrechnung der Gas- und Stromkosten. Der Gläubiger ist verpflichtet, dem "
        "Bürgen die Bürgschaftsurkunde nach Erlöschen unverzüglich im "
        "Original zurückzugeben.", S_P))

    st.append(Paragraph("7. Sonstiges", S_H))
    st.append(Paragraph(
        "Ich übernehme diese Bürgschaft nicht im Rahmen einer gewerblichen oder "
        "selbständigen beruflichen Tätigkeit. Eine Kopie des Untermietvertrages "
        "vom %s liegt mir vor; sein Inhalt ist mir bekannt. Änderungen und "
        "Ergänzungen dieser Erklärung bedürfen der Schriftform. Sollte eine "
        "Bestimmung dieser Erklärung unwirksam sein, bleibt die Bürgschaft im "
        "Übrigen wirksam. Es gilt deutsches Recht." % VERTRAGSDATUM, S_P))

    st.append(Spacer(1, 12 * mm))
    st.append(signature_block())
    st.append(Spacer(1, 6 * mm))
    st.append(Paragraph(
        "Name in Druckbuchstaben: <b>%s</b>, %s, %s"
        % (b["name"], b["strasse"], b["ort"]), S_SMALL))
    st.append(Spacer(1, 4 * mm))
    st.append(Paragraph(
        "<i>Hinweis: Diese Bürgschaftserklärung ist gemäß § 766 BGB "
        "eigenhändig zu unterschreiben und dem Vermieter nach § 4 Abs. 4 des "
        "Untermietvertrages spätestens bei der Schlüsselübergabe im Original "
        "auszuhändigen. Eine Unterschrift per Fax, Scan oder E-Mail genügt "
        "nicht.</i>", S_SMALL))

    doc.build(st)
    return path


if __name__ == "__main__":
    for buerge in BUERGEN:
        print("erstellt:", build(buerge))
