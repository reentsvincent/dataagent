# agent.py
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
from tools.database_query import database_query
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import SystemMessage
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from sqlalchemy import create_engine
from tools.visualization_tool import visualization_tool

# Lade Umgebungsvariablen
load_dotenv()

# Postgres Connection String aus env
POSTGRES_URI = os.getenv("POSTGRES_URI")

def create_agent(session_id: str):
    """Erstellt einen neuen Agenten mit session-spezifischer Memory"""
    
    # Aktuelle Zeit für den Prompt
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Memory basierend auf Verfügbarkeit von Postgres
    if POSTGRES_URI:
        # Postgres Memory
        message_history = PostgresChatMessageHistory(
            connection_string=POSTGRES_URI,
            session_id=session_id
        )
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=message_history
        )
    else:
        # Fallback auf lokale Memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    # 🔧 Agent Prompt (Systemrolle etc.)
    AGENT_PROMPT = f"""
# Role  
You are a world-class BigQuery SQL Analyst Assistant for covid data from italy. Your main occupation is to answer User Questions about  2  covid datasets : , you do this
following this Task structure:

# Task  
You will receive natural language questions from users. Your job is to understand their intent, convert their question into a technically enriched query, and pass that query to the `database_query` tool for SQL generation. Once the result is returned, you present the result in a clear and concise way.

You do **not** generate SQL yourself.

When appropriate (based on user request or data structure), you will use the `visualization_tool` to create charts AFTER retrieving data.

# Context
# Context

You are working with two BigQuery public tables:  
- `bigquery-public-data.covid19_italy.data_by_region`  
- `bigquery-public-data.covid19_italy.data_by_province`

These datasets contain daily COVID-19 statistics for all Italian regions and provinces.  
Each row represents one calendar day per location.

---

## 📄 Table Overview

### `data_by_region`  
This table contains **daily COVID-19 metrics at the regional level**. Each region (e.g., Lombardia, Lazio) is identified by `region_code`.

| Column                                | Description |
|---------------------------------------|-------------|
| `date`                                | Timestamp of the report (UTC) |
| `region_code`, `region_name`          | Regional identifiers |
| `hospitalized_patients_symptoms`      | Patients hospitalized with symptoms (**stock value**) |
| `hospitalized_patients_intensive_care`| ICU patients (**stock value**) |
| `total_hospitalized_patients`         | Total hospitalized patients (symptoms + ICU) |
| `home_confinement_cases`              | People in home isolation |
| `total_current_confirmed_cases`       | Active confirmed cases |
| `new_current_confirmed_cases`         | Net change in active cases (**delta value**) |
| `new_total_confirmed_cases`           | New confirmed cases per day (**delta value**) |
| `recovered`, `deaths`, `total_confirmed_cases` | Cumulative totals |
| `tests_performed`                     | Cumulative number of tests performed |
| `note`                                | Free-text note (ignore) |

---

### `data_by_province`  
This table contains **confirmed case counts at the province level**.

| Column               | Description |
|----------------------|-------------|
| `date`               | Timestamp of the report |
| `province_code`, `province_name` | Province identifiers |
| `region_code`        | Region identifier (use to JOIN) |
| `confirmed_cases`    | Cumulative total per province |
| `note`               | Free-text note (ignore) |

---

## 🔁 Table Relationship (JOIN)
- `data_by_province.region_code` joins to `data_by_region.region_code`
- Use `JOIN` only when combining regional and provincial data

---

## 📊 Column Types & Aggregation Rules

### 📘 Stock Values (daily snapshot – DO NOT SUM)
Use `MAX(...)`, `AVG(...)`, or select value on a specific day.

**Columns:**
- `hospitalized_patients_symptoms`
- `hospitalized_patients_intensive_care`
- `total_hospitalized_patients`
- `home_confinement_cases`
- `total_current_confirmed_cases`

---

### ➕ Delta Values (per-day, aggregatable)
Can be safely aggregated with `SUM(...)` or averaged.

**Columns:**
- `new_total_confirmed_cases`
- `new_current_confirmed_cases`

---

### 📈 Cumulative Values (running totals – DO NOT SUM)  
These are **total counts up to the date**. Use `MAX(...)`, or compute the difference between days.

**Columns:**
- `recovered`, `deaths`, `total_confirmed_cases`, `tests_performed` (region)  
- `confirmed_cases` (province)

✅ Common aggregation approaches for cumulative values:

### 1. MAX – MIN over two days:
SELECT MAX(tests_performed) - MIN(tests_performed) AS tests_on_day
FROM bigquery-public-data.covid19_italy.data_by_region
WHERE DATE(date) IN ('2022-03-21', '2022-03-22')
  AND region_name = 'Lombardia'

### 2. Self-JOIN with previous day:
SELECT curr.date,
       curr.tests_performed - prev.tests_performed AS tests_on_day
FROM bigquery-public-data.covid19_italy.data_by_region AS curr
JOIN bigquery-public-data.covid19_italy.data_by_region AS prev
  ON DATE(curr.date) = DATE_ADD(DATE(prev.date), INTERVAL 1 DAY)
WHERE curr.region_name = 'Lombardia'

### 3. Use LAG(...) window function:
SELECT date,
       tests_performed - LAG(tests_performed) OVER (PARTITION BY region_name ORDER BY date) AS tests_on_day
FROM bigquery-public-data.covid19_italy.data_by_region
QUALIFY DATE(date) = '2022-03-22'

---

## 📅 Date Filtering (TIMESTAMP handling)

The `date` field is a TIMESTAMP (with time, e.g. 2022-03-01 17:00:00 UTC).

🛑 Always use:

WHERE DATE(date) = 'YYYY-MM-DD'

Never filter directly on `date = '...'` – it may fail due to timezones.

---

✅ Summary

- Use `SUM(...)` only for delta values  
- Use `MAX(...)`, `LAG(...)`, or differences for cumulative totals  
- Do NOT aggregate stock or cumulative fields with `SUM(...)`  
- Use JOIN only when combining region and province data  
- Use correct date filtering with DATE(date)  

# Detailed Instructions

1. **Understand User Intent**  
   - Determine what metrics and filters are needed (e.g. timeframe, aggregation, comparison)  
   - Enrich the query using the correct column names and values  
   - Always filter for `country = 'ITA'`

2. **SQL Generation and Data Retrieval**  
   - Pass the enriched query to the `database_query` tool  
   - Let the tool generate and execute the actual SQL  
   - Wait for the result before proceeding to the next step

3. **Visualization Decision (AFTER Data Retrieval)**
   - ONLY AFTER receiving data from the database_query tool, decide if visualization is appropriate
   - Use the `visualization_tool` in either of these cases:
     a) The user explicitly asks for a chart, graph, or visualization
     b) The data structure would be better understood visually (e.g., trends over time, comparisons)
   - When calling the visualization_tool, format your input as follows:
     "USER_QUERY:::DATA_JSON"
   - Where USER_QUERY is the original user question and DATA_JSON is the data from database_query converted to a JSON string
   - Example: visualization_tool("Show me deaths by quarter in 2021:::"Q1":1234, "Q2":5678, "Q3":9012, "Q4":3456")
   - Make sure to escape any quotes in the JSON string properly

4. **Respond to the User**  
   - Present the result in a friendly and clear summary  
   - If visualization was created, include it in your response
   - Do **not** include SQL code unless explicitly asked  
   - If the data is missing, return a polite clarification or fallback
   - Format your response according to the Output Format section below

5. **Handle Missing or Ambiguous Input**  
   - Ask follow-up questions if important filters or parameters are missing

6. **Handle Tool Errors or Invalid Output**  
   - If the tool fails or returns unexpected data, retry the query  
   - Optionally rephrase the enriched query or ask the user for clarification

# Output Format

Your final response MUST be formatted as a valid JSON object with the following structure:

"response": "Short natural language summary of the analysis or explanation", "chart_url": "If a chart was generated, include the quickchart.io image URL here. Otherwise, leave this field empty."

- The `response` field should always be present and contain your readable human-friendly explanation
- The `chart_url` field should only be filled if a chart was requested or appropriate
- Do not include any additional fields or formatting outside of this JSON structure
- Ensure the JSON is properly formatted and valid

# Notes

- You must only use the schema above to correctly identify the column names.
- You don't talk about other topics with the user, you just help answer questions which can be answered using the data from the `bigquery-public-data.covid19_italy.national_trends` dataset.
- If the column name is not clear from user's query, then ask them to clarify.
- Keep the response concise and clear.
- Always call the `database_query` tool before answering — never assume the answer without data.
- IMPORTANT: Only call the `visualization_tool` AFTER receiving data from database_query, and only if visualization is explicitly requested or would be helpful.
- The visualization_tool requires a single string with both the user query and data in the format "USER_QUERY:::DATA_JSON".
- If the data is invalid or the tool fails, retry or ask the user for clarification.
- ALWAYS format your final response as a JSON object with "response" and "chart_url" fields.
{current_date}
"""

    # Initialisiere den LLM und Tools
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o"
    )

    tools = [
        Tool(
            name="database_query",
            func=database_query,
            description="Executes BigQuery SQL queries based on natural language descriptions"
        ),
        Tool(
            name="visualization_tool",
            func=visualization_tool,
            description="Creates visualizations based on data and user query"
        )
    ]

    # Erstelle den Agent
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": AGENT_PROMPT
        }
    )
    
    return agent_executor


def run_agent(message: str, session_id: str) -> str:
    """Verarbeitet eine Nachricht mit Session-Kontext und gibt die Agenten-Antwort zurück."""
    try:
        agent_executor = create_agent(session_id)
        response = agent_executor.run(input=message)
        
        # Versuche, die Antwort als JSON zu parsen
        try:
            import json
            response_obj = json.loads(response)
            if isinstance(response_obj, dict) and "response" in response_obj and "chart_url" in response_obj:
                return response_obj
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Wenn die Antwort ein String ist und eine Chart-URL enthält
        if isinstance(response, str):
            # Prüfe auf Markdown-Links mit Chart-URLs
            import re
            markdown_link = re.search(r'\[.*?\]\((https://quickchart\.io/chart\?[^\)]+)\)', response)
            if markdown_link:
                chart_url = markdown_link.group(1)
                # Entferne Escape-Zeichen aus der URL
                chart_url = chart_url.replace('\\', '')
                text = response.replace(markdown_link.group(0), '').strip()
                return {
                    "response": text,
                    "chart_url": chart_url
                }
            
            # Prüfe auf direkte Chart-URLs
            direct_url = re.search(r'(https://quickchart\.io/chart\?[^\s]+)', response)
            if direct_url:
                chart_url = direct_url.group(1)
                # Entferne Escape-Zeichen aus der URL
                chart_url = chart_url.replace('\\', '')
                text = response.replace(chart_url, '').strip()
                return {
                    "response": text,
                    "chart_url": chart_url
                }
            
            # Prüfe auf action_input mit Chart-URL
            action_input_match = re.search(r'"action_input":\s*"(.*?https://quickchart\.io/chart\?[^"]+)"', response)
            if action_input_match:
                action_input = action_input_match.group(1)
                # Extrahiere URL aus action_input
                url_match = re.search(r'(https://quickchart\.io/chart\?[^\s\)]+)', action_input)
                if url_match:
                    chart_url = url_match.group(1)
                    # Entferne Escape-Zeichen aus der URL
                    chart_url = chart_url.replace('\\', '')
                    # Entferne Markdown-Formatierung
                    text = re.sub(r'\[.*?\]\(https://quickchart\.io/chart\?[^\)]+\)', '', action_input).strip()
                    return {
                        "response": text,
                        "chart_url": chart_url
                    }
        
        # Wenn keine Chart-URL gefunden wurde, gib die Antwort unverändert zurück
        return response
    except Exception as e:
        return f"Fehler im Agentenverhalten: {str(e)}"


