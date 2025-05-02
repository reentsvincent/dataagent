# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent
import uuid

# Initialisiere FastAPI-Anwendung
app = FastAPI()

# Datenschema für POST-Anfragen
token = "optional_auth_token"

class QueryInput(BaseModel):
    message: str
    session_id: str = None

# Endpunkt zur Abfrageverarbeitung
@app.post("/query")
def query_endpoint(query: QueryInput):
    session_id = query.session_id or str(uuid.uuid4())
    reply = run_agent(query.message, session_id)
    return {"response": reply, "session_id": session_id}