Perfekt! Hier ist die **komplette `README.md` in reinem Markdown** – **kein HTML**, keine Sonderzeichen außerhalb der Markdown-Syntax, direkt kopierbar und GitHub-kompatibel:

---

```markdown
# AI-Agent für KI-gestützte Datenanalyse

Dieses Repository enthält den vollständigen Quellcode sowie alle Evaluationsdaten zur Bachelorarbeit:

**„Entwicklung eines AI Agents für KI-gestützte Datenanalyse“**  
Vincent Reents · Universität Münster · Abgabedatum: 02.05.2025

---

## 🎯 Ziel der Arbeit

Ziel des Projekts ist die Entwicklung eines autonomen AI-Agenten, der:

- natürliche Spracheingaben in SQL-Abfragen übersetzt,
- Fehler automatisch erkennt und behebt (dreistufiger Debugging-Prozess),
- Ergebnisse bei Bedarf visualisiert,
- über eine intuitive Weboberfläche bedient werden kann.

Die technische Umsetzung erfolgte in zwei Iterationen mit unterschiedlichen Architekturen.

---

## 📁 Projektstruktur

```

.
├── iteration1\_app.py              # Streamlit-basierte UI aus Iteration 1
├── Iteration1\_SQLAgent.json      # n8n-Workflow (Orchestrator-Agent)
├── Iteration1\_DBQuery.json       # n8n-Workflow (Tool für SQL-Abfragen)
├── technische-evaluation-1.csv   # Ergebnisse der technischen Evaluation Iteration 1
├── technische-evaluation-2.csv   # Ergebnisse der technischen Evaluation Iteration 2
├── TAM-Auswertung.csv            # Rohdaten der TAM3-Nutzerbefragung

├── agent.py                      # LangChain-Orchestrator-Agent (Iteration 2)
├── database\_query.py             # SQL-Tool mit Debugging (Iteration 2)
├── visualization\_tool.py         # Chart.js-Visualisierungstool (Iteration 2)
├── main.py                       # Einstiegspunkt der FastAPI-App (Iteration 2)
├── config.py                     # Zentrale Konfiguration (.env-Handling)

├── docker-compose.yml            # Docker Deployment Setup
├── dockerfile                    # Dockerfile zur App-Bereitstellung
├── google-credentials.json       # BigQuery-Zugang (nicht öffentlich verwenden!)
└── requirements.txt              # Python-Abhängigkeiten

````

---

## 🚀 Iteration 2: FastAPI & LangChain

Diese Version ist die finale Implementierung mit verbessertem Debugging und Visualisierung.

### Voraussetzungen

- Python 3.10+
- `.env`-Datei mit gültigem BigQuery-Zugang
- GCP Service Account JSON: `google-credentials.json`

### Starten (lokal)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
````

Die API ist dann unter [http://localhost:8000](http://localhost:8000) verfügbar.

---

## 🔁 Iteration 1: n8n & Streamlit (Prototyp)

Der erste Prototyp basiert auf n8n-Workflows und einer Streamlit-UI. Die Workflows (`*.json`) können direkt in n8n importiert werden. Die UI befindet sich in `iteration1_app.py`.

---

## 📊 Evaluation

### Objective 2: Technische Leistungsfähigkeit

* Evaluationsbasis: 52 Testfragen
* Metriken: Accuracy, Response Time
* Ergebnisse: siehe `technische-evaluation-1.csv` und `technische-evaluation-2.csv`

### Objective 3: Nutzerakzeptanz

* Befragung nach TAM3 (PU & PEOU)
* Ergebnisse: siehe `TAM-Auswertung.csv`
* Auswertung: Kapitel 5 der Bachelorarbeit

---

## 📂 Reproduzierbarkeit

Alle Rohdaten und Quellcodes zur Reproduktion der Ergebnisse finden sich im Repository. Hinweise zur Evaluierung und Setup sind in der Dokumentation der Arbeit sowie direkt in den Python-Dateien enthalten.

---

## ⚠️ Sicherheitshinweis

`google-credentials.json` enthält sensible Zugangsdaten. Bitte bei einer öffentlichen Bereitstellung entfernen oder in `.gitignore` aufnehmen.

---

## 📄 Lizenz

Diese Arbeit steht unter der Lizenz:

**Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**
[https://creativecommons.org/licenses/by-sa/4.0/](https://creativecommons.org/licenses/by-sa/4.0/)

---

## 📫 Kontakt

Vincent Reents
B.Sc. Information Systems
Universität Münster
E-Mail: [vreents@uni-muenster.de](mailto:vreents@uni-muenster.de)

```

---

Du kannst den obigen Text 1:1 als `README.md` in dein Repository einfügen.  
Möchtest du ihn auch als `.md`-Datei?
```
