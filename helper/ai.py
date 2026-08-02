import json
import ollama
import logging
from helper.skills import *

# Instanz der Skills-Klasse erstellen
skills = Skills()

class AI:

    # Initialisiere AI Agent
    def __init__(self, config_path="config.json"):
        self.model = "llama3"  # Fallback-Standardwerte
        self.temperature = 0.7
        self.top_p = 0.9
        self.num_predict = 128
        self.num_ctx = 1024
        self.seed = 42
        self.system_prompt = "Du bist ein hilfreicher Assistent."

        with open(config_path, "r", encoding="utf-8") as file:
            try:
                config = json.load(file)
                self.model = config["ai_settings"]["model_name"]
                self.temperature = config["ai_settings"]["temperature"]
                self.top_p = config["ai_settings"]["top_p"]
                self.num_predict = config["ai_settings"]["num_predict"]
                self.num_ctx = config["ai_settings"]["num_ctx"]
                self.seed = config["ai_settings"]["seed"]
                self.system_prompt = config["ai_settings"]["system_prompt"]
                logging.info("ai.py initialized successfully.")
            except Exception:
                logging.exception("Error while initializing ai.py, using defaults.")

        self.history = [{"role": "system", "content": self.system_prompt}]

        # Mapping der echten Python-Funktionen
        self.available_skills = {
            "current_time": skills.current_time,
            "list_all_notes": skills.list_all_notes,
            "read_note_content": skills.read_note_content,
            "search_notes": skills.search_notes,
            "search_web": skills.search_web,
            "get_weather": skills.get_weather
        }

        # Alle verfügbaren Tool-Schemata für Ollama
        self.tools = [
            current_time_tool, 
            list_all_notes_tool, 
            read_note_content_tool, 
            search_notes_tool,
            search_web_tool,
            get_weather_tool
        ]

    # Dynamischer Chataufruf mit automatischem Tool-Calling-Loop
    def call_model_chat(self, message):
        # 1. Neue User-Nachricht an den Verlauf anhängen
        self.history.append({"role": "user", "content": message})

        # Standard-Konfiguration für alle Aufrufe definieren
        chat_options = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "num_predict": self.num_predict,
            "num_ctx": self.num_ctx,
            "seed": self.seed,
        }

        # Schleife läuft, solange das Modell Tools aufrufen möchte (max. 5 Iterationen als Schutz)
        max_loops = 5
        loop_count = 0

        while loop_count < max_loops:
            logging.debug(f"Sende an Modell (Loop {loop_count}): {json.dumps(self.history, ensure_ascii=False, indent=2)}")
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                options=chat_options,
                tools=self.tools,
                stream=False,
            )

            # WICHTIG: Jede Modell-Antwort (egal ob Text oder Tool-Anforderung) MUSS sofort in den Verlauf
            self.history.append(response["message"])

            # Prüfen, ob ein Tool-Aufruf angefordert wurde
            if "tool_calls" in response["message"] and response["message"]["tool_calls"]:
                logging.info(f"Modell fordert Tool-Aufruf an (Loop {loop_count + 1}).")

                for tool in response["message"]["tool_calls"]:
                    tool_name = tool.function.name if hasattr(tool, 'function') else tool['function']['name']
                    tool_args = tool.function.arguments if hasattr(tool, 'function') else tool['function']['arguments']
                    
                    function_to_call = self.available_skills.get(tool_name)
                    if function_to_call:
                        try:
                            # Funktion ausführen
                            skill_output = function_to_call(**tool_args)
                        except Exception as e:
                            logging.error(f"Fehler bei Ausführung von Tool {tool_name}: {e}")
                            skill_output = f"Fehler bei der Ausführung des Tools: {str(e)}"
                        
                        # Ergebnis des Tools zwingend als Rolle 'tool' anhängen
                        self.history.append({
                            "role": "tool",
                            "content": str(skill_output),
                            "name": tool_name,
                            "tool_call_id": tool.get("id") if isinstance(tool, dict) else getattr(tool, "id", None)
                        })
                
                loop_count += 1
                # Schleife läuft weiter, falls das Modell die Tool-Antworten auswerten und ein weiteres Tool rufen will
                continue 
            
            else:
                # Keine Tool-Aufrufe mehr -> Das ist die finale Textantwort für den User
                return response["message"]["content"]

        logging.warning("Tool-Calling-Schleife wegen Maximal-Limit abgebrochen.")
        return "Ich konnte die Anfrage aufgrund zu vieler verschachtelter Tool-Aufrufe nicht abschließen."

    def save_assistant_response(self, full_content):
        """Manuelles Hinzufügen (nur nötig, falls außerhalb Text injiziert wird)."""
        self.history.append({"role": "assistant", "content": full_content})

    def reset_history(self):
        """Löscht den Chatverlauf und setzt das Gedächtnis zurück."""
        self.history = [{"role": "system", "content": self.system_prompt}]
