import os
from pathlib import Path

# Basis-Verzeichnis des Projekts
BASE_DIR = Path(__file__).resolve().parent

# Umgebungsvariable für die Entwicklungsumgebung
ENV = os.getenv("ENVIRONMENT", "local")  # 'local' ist der Standardwert

# Relativer Pfad zur credentials Datei im aktuellen Projektverzeichnis
CREDENTIALS_PATH = os.path.join(BASE_DIR, "google-credentials.json")

# Konfiguration je nach Umgebungs
config = {
    "local": {
        "credentials_path": CREDENTIALS_PATH,
        "fastapi_url": "http://localhost:8000"
    },
    "docker": {
        "credentials_path": "/app/google-credentials.json",
        "fastapi_url": "http://localhost:8000"
    },
    "production": {
        "credentials_path": "/app/google-credentials.json",
        "fastapi_url": "https://your-production-url.com"
    }
}

# Aktuelle Konfiguration basierend auf der Umgebung
current_config = config[ENV]

# Setze Google Credentials Pfad und prüfe ob die Datei existiert
credentials_path = current_config["credentials_path"]
if not os.path.exists(credentials_path):
    raise FileNotFoundError(f"Google credentials file not found at: {credentials_path}")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
print(f"Using Google credentials from: {credentials_path}") 