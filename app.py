# app.py
from config import current_config
import streamlit as st
import requests
import uuid
import json

st.set_page_config(page_title="LangChain COVID-19 Agent", page_icon="🦠")
st.title("🦠 COVID-19 Data Assistant (LangChain)")

# Session-ID und Chatverlauf initialisieren
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Vorherige Nachrichten anzeigen
for msg in st.session_state.chat_history:
    if isinstance(msg["message"], dict) and "chart_url" in msg["message"] and msg["message"]["chart_url"]:
        # Textantwort anzeigen
        st.chat_message(msg["role"]).write(msg["message"]["response"])
        # Bild von der URL anzeigen
        st.image(msg["message"]["chart_url"], use_container_width=True)
    else:
        st.chat_message(msg["role"]).write(msg["message"])

# Eingabe des Users
user_input = st.chat_input("Stell deine Frage zur COVID-19-Situation in Italien...")

# Verwende die konfigurierte FastAPI URL
FASTAPI_URL = current_config["fastapi_url"]

# Anfrage verarbeiten
if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.chat_history.append({"role": "user", "message": user_input})

    # Anfrage an FastAPI senden
    response = requests.post(
        f"{FASTAPI_URL}/query",
        json={
            "message": user_input,
            "session_id": st.session_state["session_id"]
        },
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        result = response.json().get("response", "Keine Antwort erhalten.")
        
        # Versuche, die Antwort zu parsen, wenn sie ein String ist
        if isinstance(result, str):
            try:
                # Versuche, die Antwort als JSON zu parsen
                result_json = json.loads(result)
                if isinstance(result_json, dict):
                    result = result_json
            except json.JSONDecodeError:
                # Wenn es kein gültiges JSON ist, versuche, es zu reparieren
                try:
                    # Suche nach dem typischen Muster mit fehlendem Komma
                    fixed_json_str = result.replace('":"', '":"', 1).replace('"chart_url"', ',"chart_url"', 1)
                    result_json = json.loads(fixed_json_str)
                    if isinstance(result_json, dict):
                        result = result_json
                except (json.JSONDecodeError, ValueError):
                    # Wenn auch das nicht funktioniert, behalte das ursprüngliche Ergebnis
                    pass
        
        # Visualisierung oder Text-Antwort verarbeiten
        if isinstance(result, dict) and "chart_url" in result and result["chart_url"]:
            # Textantwort anzeigen
            st.chat_message("assistant").write(result["response"])
            # Bild von der URL anzeigen
            st.image(result["chart_url"], use_container_width=True)
            # Chat-Historie aktualisieren
            st.session_state.chat_history.append({"role": "assistant", "message": result})
        else:
            # Wenn es keine Visualisierung gibt oder das Format nicht erkannt wird
            if isinstance(result, dict) and "response" in result:
                st.chat_message("assistant").write(result["response"])
            else:
                st.chat_message("assistant").write(result)
            st.session_state.chat_history.append({"role": "assistant", "message": result})
    else:
        error = f"Fehler: {response.status_code}"
        st.chat_message("assistant").write(error)
        st.session_state.chat_history.append({"role": "assistant", "message": error})





