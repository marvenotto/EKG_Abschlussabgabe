# 🫀 Interaktives EKG-Analyse-Dashboard mit Streamlit

Ein modularer, datenschutzkonformer Prototyp zur biosignalanalytischen Auswertung, Visualisierung und Verwaltung von Elektrokardiogramm-Zeitreihen (EKG). Das System bietet rollenbasierte Zugänge für Patienten und Administratoren, automatisierte Anomalie-Erkennung sowie einen automatischen PDF-Report-Export.

---

## 👥 Autoren
* **Cedric Rissi**
* **Marven Otto**

---

## 🎯 Hauptfunktionen (Features)

### 👤 Patienten-Bereich
* **Automatisches Onboarding:** Erstregistrierung inklusive vollständiger Erfassung demografischer und anthropometrischer Parameter (Gewicht, Größe, Aktivitätslevel, BMI-Berechnung).
* **Interaktive Signal-Visualisierung:** Dynamische EKG-Kurvenanzeige mittels Plotly inklusive performantem Downsampling zur flüssigen UX und einem integrierten Range-Slider.
* **Self-Service & Upload:** Eigenständiges Hochladen von neuen EKG-Messdaten (CSV/TXT) und Aktualisierung des Profilbilds direkt über das Webinterface.
* **Anonymer Gruppenvergleich:** Datenschutzkonformer Vergleich der eigenen durchschnittlichen Herzfrequenz mit aggregierten Referenzwerten anderer Altersgruppen.
* **PDF-Export:** Generierung eines standardisierten klinischen EKG-Untersuchungsberichts.

### 🛡️ Admin-Bereich (CRUD)
* **Patientenverwaltung:** Vollständige Einsicht in die zentrale Patientendatenbank (person_db.json).
* **Datenmanipulation (CRUD):** Erstellen neuer Patientenakten, tiefgreifendes Bearbeiten bestehender Stammdaten und restloses Löschen von Profilen.
* **Systemstatistiken:** Aggregierte, anonymisierte Systemauswertung (z. B. Anomalie-Häufigkeiten und demografische Verteilungen).

---

## 🔑 Zugangsdaten für die Präsentation (Demo-Credentials)

Für die Demonstration und Überprüfung der Anwendung durch die Gutachter können folgende vorkonfigurierte Test-Accounts genutzt werden:

### 1. Administrator-Zugang
* **Reiter im Interface:** 🛡️ Admin Zugang
* **Benutzername:** admin
* **Passwort:** admin123

### 2. Patienten-Zugänge (Vorkonfiguriert)
* **Reiter im Interface:** 🔑 Patienten Login
* **Test-Account 1 (Denis Undav):**
  * **E-Mail:** undav.dfb@gmail.com
  * **Passwort:** (Über den Registrierungs-/Verifizierungsprozess neu anlegbar oder direkt in users.json hinterlegt)
* **Test-Account 2 (Cedi Blake):**
  * **E-Mail:** Cedi@gmail.com

*Hinweis zum Self-Service:* Jederzeit können über den Reiter "📝 Registrieren" neue, vollwertige Patienten-Accounts inklusive automatisiertem Profil-Onboarding erstellt werden.

---

## 🏗️ Systemarchitektur & Dateistruktur

Das Projekt folgt einer strikten Schichtentrennung (Modularisierung), um Wartbarkeit und Erweiterbarkeit für die Medizintechnik-Software zu garantieren:

EKG_Abschlussabgabe/
│
├── app.py                  # Zentraler Einstiegspunkt (Streamlit-UI & Routing)
├── requirements.txt        # Externe Abhängigkeiten und Bibliotheken
├── pyproject.toml          # Projekt-Metadaten und Konfiguration
│
├── data/                   # Dateibasierte NoSQL-Datenbanken (JSON/CSV)
│   ├── person_db.json      # Medizinische Patientenakten & EKG-Verknüpfungen
│   ├── users.json          # Verschlüsselte Login-Credentials & Verifizierungsstatus
│   ├── ekg_data/           # EKG-Rohdatensätze (.txt / .csv)
│   └── pictures/           # Profilbilder der Patienten
│
└── src/                    # Anwendungslogik (Backend-Module)
    ├── __init__.py         # Initialisierung des Quellcode-Pakets
    ├── auth.py             # Authentifizierung, SHA-256-Hashing & SMTP-Mail-Logik
    ├── models.py           # Objektorientierte Datenmodelle (Person, EKG)
    ├── processing.py       # Biosignalanalyse & Peak-Detektion mittels NeuroKit2
    ├── visualization.py    # Generierung interaktiver Plotly-Diagramme
    └── pdf_generator.py    # PDF-Generierung und Binärdaten-Verarbeitung (fpdf)

---

## ⚙️ Installation und Inbetriebnahme

### Vorraussetzungen
* Python 3.8 oder höher
* Ein eingerichteter SMTP-Server (z. B. Gmail) in den Streamlit-Secrets (secrets.toml) für die Mail-Verifizierung.

### Schritt-für-Schritt-Anleitung

1. Repository klonen oder Projektordner öffnen:
   cd EKG_Abschlussabgabe

2. Virtuelle Umgebung erstellen und aktivieren (Mac/Linux):
   python3 -m venv .venv
   source .venv/bin/activate

3. Abhängigkeiten installieren:
   pip install -r requirements.txt

4. Streamlit-Anwendung starten:
   streamlit run app.py

---

## 🛠️ Verwendete Kern-Bibliotheken

* **Streamlit:** Framework für das Webinterface und die reaktive UI-Steuerung.
* **NeuroKit2:** Fortschrittliche Biosignalanalyse zur präzisen Detektion von R-Zacken und Herzratenberechnung.
* **Plotly Express:** Erstellung interaktiver, explorativer Zeitreihen-Diagramme.
* **FPDF:** Programmatische Generierung valider PDF/A-Konformer Untersuchungsberichte.
* **Pandas & NumPy:** Hochperformante Verarbeitung und Filterung tabellarischer Messdatenstrukturen.