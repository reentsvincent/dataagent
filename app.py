import streamlit as st
import requests
import uuid

st.set_page_config(page_title="n8n Chat Agent", page_icon="🤖", layout="wide")
st.title("Data Analysis AI Agent")

# Session & Verlauf initialisieren
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Liste aus dicts: {"role": "user"/"assistant", "message": "..."}

# Bestehende Nachrichten anzeigen
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["message"])

# Eingabefeld
chat_input = st.chat_input("Frag etwas zu deinen BigQuery-Daten...")

# Neue Nachricht senden
if chat_input:
    st.chat_message("user").write(chat_input)
    st.session_state.chat_history.append({"role": "user", "message": chat_input})

    payload = {
        "body": {
            "session_id": st.session_state["session_id"],
            "message": chat_input
        }
    }

    response = requests.post(
         "https://vincentreents.app.n8n.cloud/webhook/bigquery-db-agent",
        json=payload,
        headers={
            "Content-Type": "application/json",
            # "Authorization": "Bearer DEIN_TOKEN",  # falls nötig
        }
    )

    if response.status_code == 200:
        data = response.json()
        reply = data.get("response", "Keine Antwort erhalten.")
        chart_url = data.get("chart_url")  # Assuming the chart URL is in this field
    else:
        reply = f"Fehler: {response.status_code}"
        chart_url = None

    st.chat_message("assistant").write(reply)
    st.session_state.chat_history.append({"role": "assistant", "message": reply})

    # Display the chart as an image if the URL is available
    if chart_url:
        st.image(chart_url, use_container_width=True)
