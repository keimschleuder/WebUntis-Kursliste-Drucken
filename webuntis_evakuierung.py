"""
WebUntis Evakuierungsliste
===========================

Installation:
    pip install webuntis tabulate

"""

from datetime import datetime, date
import sys

import webuntis
from tabulate import tabulate

# ---------------------------------------------------------------------
# Zugangsdaten anpassen
# ---------------------------------------------------------------------
SERVER = "https://server.webuntis.com"   # z.B. https://ajax.webuntis.com
SCHOOL = "meine-schule"
USERNAME = "benutzername"
PASSWORD = "passwort"
USERAGENT = "Evakuierungstool"

jetzt = datetime.now()
heute = date.today()

def hole_aktuelle_kurse():
    """Fragt bei WebUntis alle aktuell laufenden, nicht entfallenen Kurse ab."""
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
                continue

            for periode in stundenplan:
                # Bereits erfasste (klassenübergreifende) Kurse nicht doppelt aufnehmen
                if periode.id in gesehene_ids:
                    continue

                # Entfallene Kurse überspringen
                if periode.code == "cancelled":
                    continue

                # Nur Kurse, die JETZT laufen
                if not (periode.start <= jetzt <= periode.end):
                    continue

                gesehene_ids.add(periode.id)

                lehrer = ", ".join(l.name for l in periode.teachers) or "-"
                klassen_namen = ", ".join(k.name for k in periode.klassen) or "-"
                faecher = ", ".join(f.name for f in periode.subjects) or "-"
                raeume = ", ".join(r.name for r in periode.rooms) or "-"
                zeit = f"{periode.start.strftime('%H:%M')}-{periode.end.strftime('%H:%M')}"

                zeilen.append([lehrer, klassen_namen, faecher, raeume, zeit])

    finally:
        session.logout()

    # Nach Lehrer sortieren, damit man beim Abhaken schnell vorankommt
    zeilen.sort(key=lambda z: z[0])

    return zeilen

def main():
    zeilen = hole_aktuelle_kurse()

    if not zeilen:
        print("Keine aktuell laufenden Kurse gefunden.")
        return

    # Kopfbereich für die druckbare, zentral abzuhakende Evakuierungsliste
    stand = jetzt.strftime("%d.%m.%Y %H:%M:%S")

    print("=" * 80)
    print(" WEBUNTIS EVAKUIERUNGSLISTE")
    print("=" * 80)
    print(f" Datenstand: {stand}")
    print(" Status:     OK")
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
