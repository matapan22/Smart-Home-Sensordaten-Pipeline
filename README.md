# Smart-Home-Sensordaten-Pipeline (MVP)

Dieses Repository enthält ein End-to-End-MVP zum Importieren, Verarbeiten, Speichern und Bereitstellen von Smart-Home-Sensordaten über eine API, das als technische Aufgabe für FoodTracks entwickelt wurde.


## Architektur & Fluss

1. **Import:** Synthetische Demodaten (CSV) werden mit absichtlichen Anomalien generiert.
2. **Prozess:** Die Daten werden mit **Polars** geladen und validiert, um eine hohe Leistung zu erzielen.
3. **Persist:** Bereinigte Daten und Qualitätskennzeichnungen werden in **PostgreSQL** gespeichert.
4. **API:** Eine **FastAPI**-Anwendung liefert sowohl Rohdaten als auch abgeleitete Daten.


## Anweisungen zur lokalen Einrichtung

### Voraussetzungen
- Python 3.10+ 
- PostgreSQL lokal installiert (Standardport 5432, Benutzer: `postgres`, Passwort: `12345678`)

### Installation

1. Klonen/entpacken Sie das Repository und navigieren Sie zum Stammverzeichnis.
2. Erstellen und aktivieren Sie eine virtuelle Python-Umgebung, um Abhängigkeiten isoliert zu halten:
**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Installieren Sie die Abhängigkeiten: 
```bash
pip install -r requirements.txt
```
4. Stellen Sie sicher, dass Ihr lokaler PostgreSQL-Server läuft und eine Datenbank namens „smart_home“ erstellt wurde. (Aktualisieren Sie „DB_URI“ in „src/database.py“, wenn Ihre lokalen Anmeldedaten abweichen).

### Ausführen der Anwendung von Anfang bis Ende

1. Demo-Daten generieren:
```bash
python src/generator.py
```
(Erstellt die Datei „data/sensor_readings.csv“ mit 500 Datensätzen, einschließlich Stuck-at- und Outlier-Fehlern)

2. Starten Sie den API-Server:
```bash
python -m uvicorn src.api:app --reload
```
3. Mit der API interagieren:
Öffnen Sie Ihren Browser und navigieren Sie zur interaktiven Swagger-Benutzeroberfläche:  **http://127.0.0.1:8000/docs**
- **Schritt 1:** Führen Sie den Endpunkt `POST /api/v1/pipeline/run` aus, um den ETL-Prozess auszulösen und Daten in Postgres zu speichern.
- **Schritt 2:** Abfrage `GET /api/v1/data/raw` oder `GET /api/v1/data/derived`.

## Annahmen, Kompromisse und Entscheidungen

Entsprechend der Anforderung nach einem pragmatischen MVP wurden folgende Entscheidungen getroffen:
- **Frameworks:**  Aufgrund seiner Geschwindigkeit, strengen Typisierung und nativen Rust-basierten Leistung wurde für die Verarbeitung „Polars“ anstelle von „Pandas“ gewählt. Für die API wurde aufgrund seiner asynchronen Fähigkeiten „FastAPI“ gewählt.
- **Soft Filtering vs. Hard Deletion:** Ungültige Daten werden _nicht_ gelöscht. Stattdessen werden boolesche Flags (`is_valid`) und String-Kategorisierungen (`error_reason`) angehängt. Dadurch können nachgelagerte Systeme Sensorausfälle überprüfen, ohne den historischen Kontext zu verlieren.
- **Daten überschreiben vs. anhängen:** Die Datei „generator.py“ überschreibt die CSV-Datei bei jedem Durchlauf, um einen vorhersehbaren, reproduzierbaren Zustand für den Prüfer zu gewährleisten, der die Erkennung der Datenqualität testet.
- **Datenbankauswahl:** Anstelle von SQLite wurde natives PostgreSQL verwendet, um eine produktionsreife Architektur zu demonstrieren, aber Docker wurde aus der endgültigen Konfiguration weggelassen, um lokale Windows-Tests zu vereinfachen.

## Erkennung von Datenqualitätsproblemen

Zwei spezifische Strategien zur Datenqualität wurden in „src/processor.py“ implementiert:
1. **Erkennung von Blockierungsfehlern (Temperatur):**
- _Logik:_ Berechnet eine gleitende Standardabweichung über ein Fenster von 5 Messwerten pro Sensor. Wenn die Standardabweichung genau `0,0` beträgt, ist der Sensor eingefroren.
- _Warum:_ Hardware-/Software-Abstürze führen häufig dazu, dass Sensoren ihren letzten bekannten Wert unbegrenzt wiederholen.
2. **Ausreißererkennung (CO2 und Temperatur):**
-  Logik: Markiert physikalische Unmöglichkeiten (z. B. CO2 > 5000 ppm oder Temperatur > 50 °C / < -10 °C).
- _Warum:_ Erkennt plötzliche Hardware-Spitzen oder Einheitenumrechnungsfehler, ohne dass komplexes maschinelles Lernen erforderlich ist.

## Modernstes Konzept

Wenn dieses MVP auf eine Produktionsumgebung skaliert werden soll, die Millionen von Ereignissen verarbeitet, wären die folgenden architektonischen Upgrades erforderlich:
1. Größer als RAM-Verarbeitung
- **Streaming-Daten:** Anstatt CSV-Dateien stapelweise zu verarbeiten, sollten Sensordaten über eine Event-Streaming-Plattform wie **Apache Kafka** oder **AWS Kinesis** erfasst werden.
- **Verarbeitungs-Engine:** Polars ist hervorragend, aber für die verteilte Verarbeitung über Cluster hinweg würden wir zu **Apache Spark** migrieren oder die **Lazy API von Polars** (Streaming-Modus) verwenden, um Chunks sequenziell zu verarbeiten, ohne den gesamten Datensatz in den Speicher zu laden.
2. Skalierung und Betrieb
- **Containerisierung und Orchestrierung:** Die API- und Verarbeitungs-Worker würden vollständig über Docker containerisiert und mit **Kubernetes (K8s)** orchestriert werden, was eine horizontale automatische Skalierung der Pods basierend auf dem eingehenden Datenverkehr/Datenvolumen ermöglicht.
- **Datenbank:** Wechseln Sie von einer einzelnen PostgreSQL-Instanz zu einer für Zeitreihen optimierten Datenbank wie **TimescaleDB** oder **InfluxDB**, die große Schreibdatenmengen und Zeitfenster-Aggregationen wesentlich besser verarbeiten können.
3. Sicherheit
- **API-Sicherheit:** Implementieren Sie die OAuth2-/JWT-Authentifizierung für die Endpunkte.
- **Datenübertragung:** Alle IoT-Daten müssen über MQTT über TLS (mTLS) übertragen werden, um sicherzustellen, dass Geräte authentifiziert sind, bevor Daten in die Pipeline übertragen werden.
4. Einschränkungen und nächste Schritte
- Derzeit löst die API die Pipeline synchron aus. In der Produktion sollte dies mithilfe einer Aufgabenwarteschlange wie **Celery** oder **Airflow** entkoppelt werden, um HTTP-Timeouts bei großen Datensätzen zu vermeiden.
- Fügen Sie umfassende Unit-Tests (`pytest`) für die Logik von `processor.py` hinzu.