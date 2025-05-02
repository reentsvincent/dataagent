# tools/database_query.py
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from google.cloud import bigquery
import os
import logging
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool("database_query")
def database_query(enriched_query: str) -> str:
    """
    Executes a BigQuery query.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    TOOL_PROMPT = f"""
    You are a SQL expert. Generate a SQL query for the COVID-19 Italy dataset.
   
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
- !Only return the rawSQL query, no other formatting or markdown or comments – just the raw SQL query

    Input: {enriched_query}
    """

    llm = ChatOpenAI(temperature=0)
    retry_llm = ChatOpenAI(temperature=0)  # Secondary LLM for retry logic

    def retry_query(original_query, original_sql, error_message):
        retry_prompt = f"""
        An error occurred while executing the following SQL query:
        SQL: {original_sql}
        Error: {error_message}

        Please adjust the SQL query to fix the error. Consider the original intent:
        {original_query}
        
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
- ! Only return the SQL query, no other formatting or markdown or comments – just the SQL query

        """
        logging.info(f"Retrying with adjusted query prompt: {retry_prompt}")
        retry_response = retry_llm.invoke(retry_prompt)
        return retry_response.content.strip()

    max_retries = 2
    attempt = 0

    while attempt <= max_retries:
        try:
            logging.info(f"Attempt {attempt + 1}: Sending request to OpenAI API with payload: {TOOL_PROMPT}")

            response = llm.invoke(TOOL_PROMPT)
            logging.info(f"Received response from OpenAI API: {response}")

            if hasattr(response, 'content'):
                sql = response.content.strip()
                logger.info(f"Generated SQL: {sql}")
            else:
                logging.error("Unexpected response type from OpenAI API")
                return "Fehler bei der Abfrage: Unerwarteter Antworttyp vom OpenAI API"

            forbidden = ["drop", "delete", "alter", "insert", "update"]
            if any(keyword in sql.lower() for keyword in forbidden):
                logging.warning("SQL query contains forbidden operations.")
                return "Die Abfrage wurde aus Sicherheitsgründen blockiert."

            client = bigquery.Client()
            logging.info(f"Executing SQL query: {sql}")
            df = client.query(sql).to_dataframe()

            if df.empty:
                logging.info("Query returned no data.")
                return "Keine Daten gefunden."

            # Extract and format data for response
            data_summary = df.to_dict(orient='records')  # Example: show first 5 records
            logging.info(f"Query executed successfully. Number of records: {len(df)}")
            logging.debug(f"Data summary: {data_summary}")

            return {
                "message": f"Abfrage erfolgreich ausgeführt. Anzahl der Datensätze: {len(df)}",
                "data": data_summary
            }

        except Exception as e:
            logging.error(f"Error processing query on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                adjusted_sql = retry_query(enriched_query, sql, str(e))
                logging.info(f"Adjusted SQL: {adjusted_sql}")
                attempt += 1
            else:
                logging.error("Failed to process query after multiple attempts.")
                return "Fehler bei der Verarbeitung der Abfrage nach mehreren Versuchen."
