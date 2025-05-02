import requests
import json
import logging
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def preformat_query(user_query, data_table):
    """
    Preformat the user query and data table into a structured prompt for the LLM.
    
    :param user_query: The natural language query from the user.
    :param data_table: The data table resulting from a SQL query.
    :return: A structured prompt for generating a Chart.js configuration.
    """
    prompt = (
        "You are a prompt-writing assistant for a Chart.js visualization agent. "
        "Your task is to analyze two inputs: 1. A natural language request from the user "
        "(which may or may not explicitly mention a chart or a chart type) 2. A table of data "
        "(resulting from a SQL query). Your goal is to generate a clear and well-structured instruction "
        "that another AI can use to create a valid Chart.js configuration. You must: "
        "- Determine whether a chart is appropriate based on the query and the data structure "
        "- If a chart makes sense, choose the most suitable chart type (e.g., bar, line, pie, etc.) "
        "- Clearly describe what should be visualized and how "
        "- Include which variable should be on the x-axis and which on the y-axis "
        "- Mention axis labels, chart title, and units if relevant "
        "- If the user's request lacks details (like chart type or axis info), make an educated choice "
        "based on the data and best practices for visualization. "
        "Your output should be: "
        "- A single paragraph written in clear, helpful English "
        "- Focused on giving a precise instruction for a chart generation model "
        "- Ready to be passed as-is into a model that will return a Chart.js configuration "
        "You are not generating the Chart.js config yourself. You're only writing the prompt that will be used to generate it."
    )
    logging.debug(f"Preformatting query with user query: {user_query} and data table: {data_table}")
    logging.debug(f"Generated preformat query prompt: {prompt}")
    return prompt

def call_llm_for_chart_config(prompt):
    """
    Call the LLM to generate a Chart.js configuration based on the prompt.
    """
    llm_prompt = (
        "Du bist ein Chart.js Visualisierungsexperte für COVID-19 Daten aus Italien. "
        "Deine Aufgabe ist es, gültige Chart.js-Konfigurationsobjekte zu erstellen, die direkt in einer Chart.js-Umgebung verwendet werden können.\n\n"
        "Die Daten stammen aus dem COVID-19 Italien-Datensatz und können folgende Metriken enthalten:\n"
        "- Hospitalisierte Patienten mit Symptomen\n"
        "- Patienten auf der Intensivstation\n"
        "- Gesamtzahl hospitalisierter Patienten\n"
        "- Personen in häuslicher Isolation\n"
        "- Aktive bestätigte Fälle\n"
        "- Neue bestätigte Fälle pro Tag\n"
        "- Genesene Patienten\n"
        "- Todesfälle\n"
        "- Gesamtzahl bestätigter Fälle\n"
        "- Durchgeführte Tests\n\n"
        
        "Die Daten können nach verschiedenen Zeiträumen aggregiert sein (täglich, monatlich, quartalsweise, jährlich).\n\n"
        
        "WICHTIG: Deine Antwort MUSS ein gültiges JSON-Objekt sein, das mit json.loads() geparst werden kann. "
        "Gib NUR das JSON-Objekt zurück, ohne zusätzlichen Text oder Erklärungen.\n\n"
        
        "Beispiel für eine gültige Antwort:\n"
        "{\n"
        "  \"type\": \"bar\",\n"
        "  \"data\": {\n"
        "    \"labels\": [\"Jan\", \"Feb\", \"Mär\", \"Apr\"],\n"
        "    \"datasets\": [{\n"
        "      \"label\": \"COVID-19 Fälle\",\n"
        "      \"data\": [1234, 5678, 9012, 3456],\n"
        "      \"backgroundColor\": \"rgba(54, 162, 235, 0.5)\"\n"
        "    }]\n"
        "  },\n"
        "  \"options\": {\n"
        "    \"scales\": {\n"
        "      \"y\": {\n"
        "        \"beginAtZero\": true,\n"
        "        \"title\": {\n"
        "          \"display\": true,\n"
        "          \"text\": \"Anzahl\"\n"
        "        }\n"
        "      },\n"
        "      \"x\": {\n"
        "        \"title\": {\n"
        "          \"display\": true,\n"
        "          \"text\": \"Monat\"\n"
        "        }\n"
        "      }\n"
        "    },\n"
        "    \"plugins\": {\n"
        "      \"title\": {\n"
        "        \"display\": true,\n"
        "        \"text\": \"COVID-19 Fälle in Italien 2021\"\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        
        f"Benutzeranfrage und Daten: {prompt}"
    )
    
    # Verwende gpt-4o für bessere Ergebnisse
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    logging.debug(f"Sending prompt to LLM: {llm_prompt}")
    response = llm.invoke(llm_prompt)
    
    if hasattr(response, 'content'):
        response_content = response.content.strip()
        logging.debug(f"Raw LLM response content: {response_content}")
        
        if response_content:
            try:
                # Versuche, JSON aus der Antwort zu extrahieren
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    chart_config = json.loads(json_str)
                else:
                    # Versuche, die gesamte Antwort als JSON zu parsen
                    chart_config = json.loads(response_content)
                
                logging.debug(f"Generated Chart.js configuration: {chart_config}")
                return chart_config
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e} - Response content: {response_content}")
                
                # Fallback: Erstelle ein einfaches Balkendiagramm mit den Daten
                try:
                    # Extrahiere Daten aus dem Prompt
                    import re
                    data_match = re.search(r':::(\[.*\]|\{.*\})', prompt)
                    if data_match:
                        data_json = json.loads(data_match.group(1))
                        
                        # Erstelle ein einfaches Balkendiagramm
                        labels = []
                        values = []
                        
                        # Verarbeite verschiedene Datenformate
                        if isinstance(data_json, list):
                            for item in data_json:
                                if isinstance(item, dict):
                                    # Finde Schlüssel für Datum/Zeit und Wert
                                    date_key = next((k for k in item.keys() if any(time_word in k.lower() for time_word in ["date", "month", "quarter", "year", "datum", "monat", "quartal", "jahr"])), None)
                                    value_key = next((k for k in item.keys() if k != date_key), None)
                                    
                                    if date_key and value_key:
                                        labels.append(item[date_key])
                                        values.append(item[value_key])
                        elif isinstance(data_json, dict):
                            # Wenn die Daten als Dictionary vorliegen (z.B. {"Q1": 1234, "Q2": 5678})
                            for key, value in data_json.items():
                                labels.append(key)
                                values.append(value)
                        
                        if labels and values:
                            # Extrahiere den Titel aus der Benutzeranfrage
                            title_match = re.search(r'(hospitalisier|patient|fall|tod|test|genesen)', prompt.lower())
                            title = "COVID-19 Daten Italien"
                            if title_match:
                                title_word = title_match.group(0)
                                if "hospitalisier" in title_word or "patient" in title_word:
                                    title = "Hospitalisierte Patienten in Italien"
                                elif "fall" in title_word:
                                    title = "COVID-19 Fälle in Italien"
                                elif "tod" in title_word:
                                    title = "COVID-19 Todesfälle in Italien"
                                elif "test" in title_word:
                                    title = "Durchgeführte COVID-19 Tests in Italien"
                                elif "genesen" in title_word:
                                    title = "Genesene COVID-19 Patienten in Italien"
                            
                            chart_config = {
                                "type": "bar",
                                "data": {
                                    "labels": labels,
                                    "datasets": [{
                                        "label": title,
                                        "data": values,
                                        "backgroundColor": "rgba(54, 162, 235, 0.5)",
                                        "borderColor": "rgb(54, 162, 235)",
                                        "borderWidth": 1
                                    }]
                                },
                                "options": {
                                    "scales": {
                                        "y": {
                                            "beginAtZero": True,
                                            "title": {
                                                "display": True,
                                                "text": "Anzahl"
                                            }
                                        },
                                        "x": {
                                            "title": {
                                                "display": True,
                                                "text": "Zeitraum"
                                            }
                                        }
                                    },
                                    "plugins": {
                                        "title": {
                                            "display": True,
                                            "text": title
                                        }
                                    }
                                }
                            }
                            
                            return chart_config
                except Exception as fallback_error:
                    logging.error(f"Fallback chart creation failed: {fallback_error}")
                
                return None
        else:
            logging.error("LLM response is empty")
            return None
    else:
        logging.error("Unexpected response type from LLM")
        return None

def generate_chart(chart_config):
    """
    Generates a chart using QuickChart based on the provided configuration.
    
    :param chart_config: A dictionary containing the chart configuration.
    :return: URL to the generated chart.
    """
    chart_json = json.dumps(chart_config)
    encoded_chart = requests.utils.quote(chart_json)
    chart_url = f"https://quickchart.io/chart?width=400&c={encoded_chart}"
    logging.debug(f"Generated QuickChart URL: {chart_url}")
    return chart_url

@tool("visualization_tool")
def visualization_tool(input_str):
    """
    Creates visualizations based on data and user query.
    
    Args:
        input_str: A string in the format "USER_QUERY:::DATA_JSON"
        
    Returns:
        A URL to the generated visualization
    """
    try:
        # Split the input string by the separator
        parts = input_str.split(":::", 1)
        if len(parts) != 2:
            return "Error: Input must be in the format 'USER_QUERY:::DATA_JSON'"
        
        user_query = parts[0].strip()
        data_json_str = parts[1].strip()
        
        # Parse the data JSON
        try:
            data_table = json.loads(data_json_str)
        except json.JSONDecodeError:
            return "Error: Could not parse data JSON"
        
        # Generate a Chart.js configuration using the LLM
        chart_config = call_llm_for_chart_config(input_str)
        if not chart_config:
            return "Error: Could not generate chart configuration"
        
        # Convert the chart configuration to a URL
        chart_url = generate_chart(chart_config)
        if not chart_url:
            return "Error: Could not generate chart URL"
        
        # Return the chart URL directly, without Markdown formatting
        return chart_url
    except Exception as e:
        logging.error(f"Error in visualization_tool: {e}")
        return f"Error creating visualization: {str(e)}"

# Example usage
user_query = "Create a bar chart representing the total deaths in Italy in 2021, with each bar showing data for one quarter."
data_table = {
    "Q1": 8354839,
    "Q2": 11126330,
    "Q3": 11851461,
    "Q4": 12262995
}

input_str = f"{user_query}:::{json.dumps(data_table)}"
chart_url = visualization_tool(input_str)
print(f"Chart URL: {chart_url}")