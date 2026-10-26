# WebUntis-Kursliste-Drucken

Für die PDF-Ausgabe werden neben den WebUntis- und Tabulate-Abhängigkeiten auch die Pakete von ReportLab benötigt:

```text
pip install webuntis tabulate reportlab pywin32
```

Unter Windows wird die erzeugte PDF automatisch über den Standarddrucker gedruckt. Dafür muss eine Anwendung für PDF-Dateien eingerichtet sein (z.B. Adobe Acrobat oder ein Browser).

Um den genauen Namen des Druckers herauszufinden, diesen Befehl in der Powershell ausführen und dann den gewünschten Druckernamen kopieren und in login.py eintragen: 

```text
Get-Printer | Select-Object -ExpandProperty Name
```

Layout der login.py:

```python
SERVER = "https://beste-schule.webuntis.com"
SCHOOL = "beste-schule"
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
USERAGENT = "Evakuierungstool"

DRUCKER = "Hier Druckername einfuegen"
```
Die Werte müssen hierbei noch angepasst werden. Die Datei muss im selben Verzeichnis liegen, wie die Hauptdatei. Dabei kann login.py auch "versteckt" sein. In diesem Verzeichnis werden auch die Ausgabedateien gespeichert.
