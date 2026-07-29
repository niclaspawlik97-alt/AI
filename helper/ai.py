import json
import ollama
from helper.skills import curent_time, curent_time_tool


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

        # Mapping Wörterbuch, um Funktionen über ihren Textnamen aufzurufen. 
        self.available_skills = {
            "curent_time": curent_time,
        }

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
            # Skills übergeben
            tools=[curent_time_tool],

            stream=False,
        )
        if "tool_calls" in response["message"] and response["message"]["tool_calls"]:
            for tool in response["message"]["tool_calls"]:
                # Bei manchen Versionen ist tool ein Objekt, bei anderen ein Dict. 
                # Das fangen wir hier sicher ab:
                tool_name = tool.function.name if hasattr(tool, 'function') else tool['function']['name']
                tool_args = tool.function.arguments if hasattr(tool, 'function') else tool['function']['arguments']
                
                function_to_call = self.available_skills.get(tool_name)
                if function_to_call:
                    skill_output = function_to_call(**tool_args)
                    
                    self.history.append({
                        "role": "tool",
                        "content": str(skill_output),
                        "name": tool_name
                    })
            
            final_response = ollama.chat(
                model=self.model, 
                messages=self.history, 
                tools=[curent_time_tool]
            )
            # KORREKTUR 2: Dictionary-Zugriff auch hier anpassen
            content = final_response["message"]["content"]
        else:
            # KORREKTUR 3: Dictionary-Zugriff für normale Antworten
            content = response["message"]["content"]

        return content
    def save_assistant_response(self, full_content):
        self.history.append({"role": "assistant", "content": full_content})

    def reset_history(self):
        """Löscht den Chatverlauf und setzt das Gedächtnis zurück."""
        self.history = [{"role": "system", "content": self.system_prompt}]
