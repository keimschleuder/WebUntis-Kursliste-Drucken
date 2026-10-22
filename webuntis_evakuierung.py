"""
WebUntis Evakuierungsliste
===========================

Installation:
    pip install webuntis tabulate reportlab
"""

from datetime import datetime, date
import os
import sys

import webuntis
from tabulate import tabulate
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from login import SERVER, SCHOOL, USERNAME, PASSWORD, USERAGENT

jetzt = datetime.now()
heute = date.today()
sicher = True

def hole_aktuelle_kurse():
    """Fragt bei WebUntis alle aktuell laufenden, nicht entfallenen Kurse ab."""
    global sicher

    session = webuntis.Session(
        server=SERVER,
        school=SCHOOL,
        username=USERNAME,
        password=PASSWORD,
        useragent=USERAGENT,
    ).login()

    gesehene_ids = set()
    zeilen = []

    try:
        alle_klassen = session.klassen()

        for klasse in alle_klassen:
            try:
                stundenplan = session.timetable(klasse=klasse, start=heute, end=heute)
            except Exception as e:
                print(f"Warnung: Stundenplan für Klasse {klasse.name} nicht abrufbar: {e}", file=sys.stderr)
                sicher = False
                continue

            for periode in stundenplan:
                # Bereits erfasste (klassenübergreifende) Kurse nicht doppelt aufnehmen
                if periode.id in gesehene_ids:
                    continue

                # Nur Kurse, die JETZT laufen
                if not (periode.start <= jetzt <= periode.end):
                    continue

                gesehene_ids.add(periode.id)

                try:
                    lehrer = ", ".join(l.name for l in periode.teachers) or "-"
                except:
                    lehrer = ""
                klassen_namen = ", ".join(k.name for k in periode.klassen) or "-"
                faecher = ", ".join(f.name for f in periode.subjects) or "-"
                raeume = ", ".join(r.name for r in periode.rooms) or "-"
                zeit = f"{periode.start.strftime('%H:%M')}-{periode.end.strftime('%H:%M')}"
                findet_statt = not periode.code == "cancelled"

                zeilen.append([lehrer, raeume, zeit, findet_statt, klassen_namen, faecher])
    finally:
        session.logout()

    # Nach Lehrer sortieren, damit man beim Abhaken schnell vorankommt
    zeilen.sort(key=lambda z: z[0])

    return zeilen

def main():
    zeilen = hole_aktuelle_kurse()

    print_out(zeilen)
    dateiname = pdf_out(zeilen)
    irl_print(dateiname)

    print("Runtime: {}".format(datetime.now() - jetzt))

def irl_print(dateiname):
    """Druckt die PDF über den Windows-Standarddrucker."""
    if not os.path.isfile(dateiname):
        raise FileNotFoundError(f"PDF-Datei nicht gefunden: {dateiname}")

    try:
        os.startfile(os.path.abspath(dateiname), "print")
    except OSError as e:
        raise RuntimeError(
            f"PDF konnte nicht an den Windows-Druckdienst übergeben werden: {dateiname}"
        ) from e

def pdf_out(zeilen):
    """Erzeugt eine druckfreundliche PDF-Datei und gibt deren Pfad zurück."""
    stand = jetzt.strftime("%d-%m-%Y_%H-%M-%S")
    dateiname = "evakuierungsliste_{}.pdf".format(stand)
    status = "OK" if sicher else "UNVOLLSTAENDIG"

    styles = getSampleStyleSheet()
    dokument = SimpleDocTemplate(
        dateiname,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="WebUntis Evakuierungsliste",
    )

    inhalt = [
        Paragraph("WEBUNTIS EVAKUIERUNGSLISTE", styles["Title"]),
        Paragraph(f"Datenstand: {stand} | Status: {status}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    kopf = ["Draussen", "Lehrer", "Raum", "Zeit", "Status", "Klasse(n)", "Fach"]
    tabelle = [kopf]
    for zeile in zeilen:
        if len(zeile) == 6:
            lehrer, raeume, zeit, findet_statt, klassen, faecher = zeile
        else:
            lehrer, klassen, faecher, raeume, zeit = zeile
            findet_statt = True

        tabelle.append([
            "[ ]",
            lehrer,
            raeume,
            zeit,
            "NORMAL" if findet_statt else "ENTFALL",
            klassen,
            faecher,
        ])

    if len(tabelle) == 1:
        tabelle.append(["", "Keine aktuell laufenden Kurse gefunden."] + [""] * 5)

    raster = Table(
        tabelle,
        repeatRows=1,
        colWidths=[18 * mm, 32 * mm, 25 * mm, 22 * mm, 25 * mm, 32 * mm, 32 * mm],
    )
    raster.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e2f3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (4, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
    ]))
    raster.setStyle(TableStyle([
        ("TEXTCOLOR", (4, 1), (4, -1), colors.red),
    ]))
    inhalt.extend([raster, Spacer(1, 6 * mm)])
    inhalt.append(Paragraph(f"{len(zeilen)} aktuell laufende Kurse", styles["Normal"]))

    dokument.build(inhalt)
    return dateiname

def print_out(zeilen):
    global sicher

    if not zeilen:
        print("Keine aktuell laufenden Kurse gefunden.")
        print("Status:     {}".format("OK" if sicher else "UNVOLLSTAENDIG"))
        return

    # Kopfbereich für die druckbare, zentral abzuhakende Evakuierungsliste
    stand = jetzt.strftime("%d.%m.%Y %H:%M:%S")

    print("=" * 80)
    print(" WEBUNTIS EVAKUIERUNGSLISTE")
    print("=" * 80)
    print(f" Datenstand: {stand}")
    print(" Status:     {}".format("OK" if sicher else "UNVOLLSTAENDIG"))
    print("=" * 80)
    print()

    header = ["Lehrer", "Klasse(n)", "Fach", "Raum", "Zeit"]
    print(tabulate(zeilen, headers=header, tablefmt="grid"))

    print()
    print("-" * 80)
    print(f"{len(zeilen)} aktuell laufende Kurse")
    print("=" * 80)

if __name__ == "__main__":
    main()
