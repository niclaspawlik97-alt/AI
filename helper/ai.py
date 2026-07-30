import json
import ollama
from helper.skills import  *

# Instanz der Skills-Klasse erstellen
skills = Skills()

class AI:

    # Initialisiere AI Agent
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            self.model = config["ai_settings"]["model_name"]
            self.temperature = config["ai_settings"]["temperature"]
            self.top_p = config["ai_settings"]["top_p"]
            self.num_predict = config["ai_settings"]["num_predict"]
            self.seed = config["ai_settings"]["seed"]
            self.system_prompt = config["ai_settings"]["system_prompt"]
        self.history = [{"role": "system", "content": self.system_prompt}]

        # KORREKTUR: Hier müssen die echten Python-Funktionen der Instanz gemappt werden!
        # Der Schlüssel entspricht dem "name" im JSON-Schema.
        self.available_skills = {
            "current_time": skills.current_time,
            "list_all_notes": skills.list_all_notes,
            "read_note_content": skills.read_note_content,
            "search_notes": skills.search_notes
        }


        # Alle verfügbaren Tool-Schemata für Ollama sammeln
        self.tools = [current_time_tool, 
                      list_all_notes_tool, 
                      read_note_content_tool, 
                      search_notes_tool]


    # Einfacher Chataufruf
    def call_model_chat(self, message):
        # 1. Neue User-Nachricht an den Verlauf anhängen
        self.history.append({"role": "user", "content": message})

        # 2. Den API-Aufruf mit self.history durchführen
        response = ollama.chat(
            model=self.model,
            messages=self.history,
            options={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.num_predict,
                "seed": self.seed,
            },
            tools=self.tools,  # KORREKTUR: Saubere Liste der JSON-Schemata
            stream=False,
        )

        # Überprüfen, ob das Modell ein Tool aufrufen möchte
        if "tool_calls" in response["message"] and response["message"]["tool_calls"]:
            # WICHTIG: Die Antwort des Modells (die den Tool-Aufruf anfordert) MUSS in die History!
            self.history.append(response["message"])

            for tool in response["message"]["tool_calls"]:
                tool_name = tool.function.name if hasattr(tool, 'function') else tool['function']['name']
                tool_args = tool.function.arguments if hasattr(tool, 'function') else tool['function']['arguments']
                
                function_to_call = self.available_skills.get(tool_name)
                if function_to_call:
                    # Führt jetzt z.B. skills.list_all_notes() aus
                    skill_output = function_to_call(**tool_args)
                    
                    self.history.append({
                        "role": "tool",
                        "content": str(skill_output),
                        "name": tool_name
                    })
            
            # Finaler Aufruf, damit das Modell die Tool-Ergebnisse auswertet
            final_response = ollama.chat(
                model=self.model, 
                messages=self.history, 
                tools=self.tools
            )
            content = final_response["message"]["content"]
        else:
            content = response["message"]["content"]

        return content

    def save_assistant_response(self, full_content):
        self.history.append({"role": "assistant", "content": full_content})

    def reset_history(self):
        """Löscht den Chatverlauf und setzt das Gedächtnis zurück."""
        self.history = [{"role": "system", "content": self.system_prompt}]
