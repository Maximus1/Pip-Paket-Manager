# 🚀 Pip Paket-Manager – Die ultimative GUI für Ihre Python-Pakete 🚀

Haben Sie es satt, mit `pip` in der Kommandozeile zu jonglieren? Vergessen Sie kryptische Befehle und unübersichtliche Listen! Der **Pip Paket-Manager** ist Ihr neues, visuelles Kontrollzentrum für das gesamte Python-Paket-Ökosystem.

Dieses Tool wurde von Grund auf entwickelt, um die Verwaltung von Python-Paketen nicht nur einfacher, sondern auch intelligenter und schneller zu machen. Egal, ob Sie ein erfahrener Entwickler oder ein Python-Neuling sind – mit dieser Anwendung haben Sie die volle Kontrolle, verpackt in einer sauberen und intuitiven grafischen Oberfläche.

**Starten Sie das Tool, und erleben Sie eine neue Ära der Paketverwaltung!**

---

## ✨ Hauptfunktionen – Was dieses Tool so besonders macht

Dieses Tool ist weit mehr als nur eine grafische Hülle für `pip`. Es ist ein intelligentes System, das Ihnen leistungsstarke Funktionen an die Hand gibt, die weit über das Standard-Terminal hinausgehen.

### 📦 Umfassende Paketverwaltung auf einen Blick
- **Vollständige Kontrolle:** Installieren, deinstallieren, aktualisieren und reinstallieren Sie jedes Paket mit nur einem Klick.
- **Automatische Admin-Rechte:** Das Tool erkennt automatisch, wenn Administratorrechte benötigt werden (z.B. für systemweite Installationen) und fordert diese an. Kein "Permission denied"-Rätselraten mehr!
- **Detaillierte lokale Informationen:** Sehen Sie auf einen Blick alles, was Sie über ein installiertes Paket wissen müssen:
  - Genaue Version, Autor und Lizenz (mit intelligenter Erkennung von `License-Expression` und Lizenzdateien).
  - Installationspfad, Homepage und Abhängigkeiten.
  - **Reverse-Dependency-Check:** Finden Sie heraus, welche anderen Pakete von einem ausgewählten Paket abhängen!

### ⚡ Intelligente & blitzschnelle PyPI-Suche
- **Intelligenter Index-Cache:** Beim ersten Start wird der riesige PyPI-Paketindex (über 700.000 Pakete!) heruntergeladen und lokal gespeichert.
- **Delta-Updates:** Bei allen weiteren Starts lädt die Anwendung nur noch die winzigen Änderungen seit dem letzten Mal herunter. Das Ergebnis: Die Suche ist **sofort** und ohne spürbare Ladezeit verfügbar, während der Netzwerkverkehr auf ein Minimum reduziert wird.
- **Offline-Suche:** Durchsuchen Sie den gesamten PyPI-Index, auch wenn Sie gerade keine Internetverbindung haben.

### 🔬 Tiefgehende Paket-Analyse
- **Kompatibilitäts-Check:** Finden Sie heraus, welche Versionen eines Pakets wirklich mit Ihrem System (Python-Version, Betriebssystem) kompatibel sind. Das Tool analysiert die "Wheel-Tags" für Sie.
- **Vollständige Release-Details:** Sehen Sie sich für jede einzelne Datei eines Releases alle verfügbaren Informationen an:
  - Dateiname, Größe, MD5- und SHA256-Hashes.
  - Benötigte Python-Version.
  - Upload-Datum und Download-URL.
- **"Yanked"-Warnungen:** Die Anwendung warnt Sie deutlich, wenn eine Version von den Entwicklern zurückgezogen wurde und nicht mehr verwendet werden sollte.

### 🌐 Benutzerfreundlichkeit auf höchstem Niveau
- **Mehrsprachige Oberfläche:** Wechseln Sie die Sprache der Anwendung zur Laufzeit (Deutsch, Englisch, Französisch, Spanisch, Chinesisch, Japanisch).
- **Visuelles Feedback:** Ein animierter Fortschrittsbalken und eine detaillierte Statusanzeige zeigen Ihnen jederzeit, was die Anwendung gerade tut. Kein Rätselraten, ob das Programm noch arbeitet oder abgestürzt ist.
- **Live-Log:** Verfolgen Sie jeden einzelnen `pip`-Befehl und jede Systemmeldung in einem übersichtlichen, separaten Log-Fenster. Perfekt für die Fehlersuche und Nachverfolgung!
- **Klickbare Links:** Alle URLs in den Detailansichten sind klickbar und öffnen sich direkt in Ihrem Browser.

---

## 🖼️ Screenshots

*(Hier könnten Sie Screenshots Ihrer Anwendung einfügen, um die Features visuell zu präsentieren.)*

**Tab 1: Paketverwaltung**
Kommt noch

**Tab 2: Paketsuche**
Kommt noch

---

## 🛠️ Anforderungen

Das Skript wurde mit Python 3 entwickelt. Die folgenden Bibliotheken werden benötigt und können einfach über `pip` installiert werden:

```bash
pip install requests Pillow packaging
```

---

## 🚀 Anwendung

1.  Stellen Sie sicher, dass alle oben genannten Anforderungen installiert sind.
2.  Führen Sie das Skript über die Kommandozeile aus:
    ```bash
    python "Pip_Paket_Manager copy.py"
    ```
3.  **Das war's!** Die Anwendung startet und ist sofort einsatzbereit.

### Erstellen einer eigenständigen .exe-Datei (Optional)

Mit einem Tool wie **PyInstaller** können Sie eine eigenständige `.exe`-Datei erstellen, die ohne eine installierte Python-Umgebung auf anderen Windows-Rechnern läuft.

1.  Installieren Sie PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Führen Sie den folgenden Befehl im Verzeichnis des Skripts aus, um die `.exe`-Datei zu erstellen:
    ```bash
    pyinstaller --onefile --windowed --icon=PyPi-128px.ico "Pip_Paket_Manager copy.py"
    ```

---

## 🤝 Mitwirken

Haben Sie eine Idee für eine neue Funktion oder möchten Sie eine weitere Sprache hinzufügen? Beiträge sind herzlich willkommen!

Das Hinzufügen einer neuen Sprache ist denkbar einfach:
1.  Fügen Sie einen neuen Eintrag mit den übersetzten Texten zum `LANG_TEXTS`-Dictionary in der Hauptdatei hinzu.
2.  Ergänzen Sie den Anzeigenamen der neuen Sprache im `lang_display_names`-Dictionary.

---

## 📜 Lizenz

Dieses Projekt steht unter der **GNU General Public License v3.0**. Die Details finden Sie in der `LICENSE`-Datei.

```
Copyright (C) 2024 [Ihr Name]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
