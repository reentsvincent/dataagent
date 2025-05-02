# AI-Agent für KI-gestützte Datenanalyse

Dieses Repository enthält den vollständigen Quellcode sowie alle relevanten Evaluationsdaten zur Bachelorarbeit:

**„Entwicklung eines AI Agents für KI-gestützte Datenanalyse“**  
Vincent Reents · Universität Münster · Abgabedatum: 02.05.2025

---

## 📌 Zielsetzung

Ziel des Projekts ist die Entwicklung eines autonomen AI-Agenten, der:
- natürliche Sprache in SQL-Abfragen übersetzt,
- Fehler automatisch erkennt und behebt (dreistufiger Debugging-Prozess),
- Ergebnisse bei Bedarf automatisch visualisiert,
- über eine benutzerfreundliche Weboberfläche nutzbar ist.

Die Umsetzung erfolgte in zwei technischen Iterationen.

---

## 📁 Projektstruktur

.
├── iteration1_app.py # Streamlit-basierte UI aus Iteration 1
├── Iteration1_SQLAgent.json # n8n-Workflow (Orchestrator-Agent)
├── Iteration1_DBQuery.json # n8n-Workflow (Tool für SQL-Abfragen)
├── technische-evaluation-1.csv # Ergebnisse der technischen Evaluation Iteration 1
├── technische-evaluation-2.csv # Ergebnisse der technischen Evaluation Iteration 2
├── TAM-Auswertung.csv # Rohdaten der TAM3-Nutzerbefragung
├── agent.py # LangChain-Orchestrator-Agent (Iteration 2)
├── database_query.py # SQL-Tool mit integriertem Debugging (Iteration 2)
├── visualization_tool.py # Tool zur Chart.js-Visualisierung (Iteration 2)
├── main.py # Einstiegspunkt der FastAPI-App (Iteration 2)
├── config.py # Zentrale Konfiguration (.env-Handling)
├── docker-compose.yml # Docker Deployment Setup
├── dockerfile # Dockerfile zur App-Bereitstellung
├── google-credentials.json # BigQuery-Zugang (nicht öffentlich verwenden!)
└── requirements.txt # Python-Abhängigkeiten

yaml
Copy
Edit

---

## 🚀 Ausführen der Iteration 2 (FastAPI + LangChain)

### Voraussetzungen

- Python 3.10+
- Docker (optional für Deployment)
- BigQuery-Zugang + hinterlegte `google-credentials.json`
- alles Dateien die nicht kenntlich zur Iteration 1 gehören oder zum Evaluationsteil sollten in einem gemeinsamen Ordner liegen.

### Lokaler Start

``bash
pip install -r requirements.txt
uvicorn main:app --reload
streamlit run app.py
Die API ist dann unter http://localhost:8000 erreichbar.

🧪 Evaluation
Die Evaluation erfolgte auf zwei Ebenen:

Objective 2: Technische Leistung (accuracy + response time), dokumentiert in:

technische-evaluation-1.csv

technische-evaluation-2.csv

Objective 3: Nutzerakzeptanz nach TAM3 (Perceived Usefulness & Ease of Use), dokumentiert in:

TAM-Auswertung.csv

Zusätzliche Details zur Evaluationslogik und -durchführung finden sich in Kapitel 5 der Arbeit.

🛠 Iteration 1 (n8n + Streamlit)
Die erste Version des Systems wurde mit n8n-Workflows und einer Streamlit-UI umgesetzt. Die zugehörigen Dateien:

Iteration1_SQLAgent.json

Iteration1_DBQuery.json

iteration1_app.py

Diese Version enthält bereits einen funktionsfähigen Datenanalyse-Agenten, allerdings ohne visuelle Darstellung oder autonomes Debugging.

🔒 Sicherheitshinweis
Die Datei google-credentials.json enthält Zugangsdaten zu Google BigQuery und sollte nicht öffentlich geteilt werden. Bitte beim Deployment entfernen oder sichern.

📄 Lizenz
Diese Arbeit ist lizenziert unter der Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

📫 Kontakt
Vincent Reents
Information Systems, Universität Münster
E-Mail: vreents@uni-muenster.de

