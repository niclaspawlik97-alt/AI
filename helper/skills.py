import re
import json
import logging
import requests

from datetime import datetime
from pathlib import Path
from collections import defaultdict

class Skills:

    def __init__(self):
        with open("secrets.json", "r", encoding="utf-8") as file:
            secrets = json.load(file)
            self.obsidian_vault = Path(secrets["folders"]["obsidian_vault"])
            self.open_weather = secrets["api_key"]["open_weather"]

        with open("config.json", "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            self.searxng_ip = config["web_search"]["searxng_ip"]
            self.searxng_timeout = config["web_search"]["timeout"]
        logging.info("Skills initialised.")

    def current_time(self) -> str:
        """Gibt die aktuelle Systemzeit und das Datum zurück."""
        logging.info("Used time skill.")
        # Zeit direkt als lesbaren Text formatieren
        return datetime.now().strftime("%H:%M:%S Uhr")
        

    # Obsidian Vault Skill
    def list_all_notes(self) -> list[str]:
        """Gibt eine Liste aller Pfade zu Markdown-Dateien aus."""
        logging.info("Used list all notes skill.")
        return [
            str(p.relative_to(self.obsidian_vault)) 
            for p in self.obsidian_vault.glob("**/*.md")
            if ".obsidian" not in p.parts
        ]

    def read_note_content(self, relative_path: str) -> str:
        clean_path = re.sub(r'^[\["\'\s]+|[\]"\'\s]+$', '', relative_path)
        file_path = self.obsidian_vault / Path(clean_path)
        
        if not file_path.exists() or not file_path.is_file():
            logging.critical(f"File does not exist: {clean_path}")
            return "Fehler: Datei existiert nicht. Bitte überprüfe den Pfad mithilfe von 'list_all_notes'."

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logging.info(f"Read file: {clean_path}")
                return content if content.strip() else "Die Datei ist leer."
        except Exception as e:
            logging.critical(f"Error whil reading file {str(e)}")
            return f"Fehler beim Lesen der Datei: {str(e)}"

    def search_notes(self, keyword: str, is_regex: bool = False) -> list[dict]:
        """Durchsucht alle Notizen nach einem Begriff oder Regex-Muster."""
        results = []
        
        # Schützt vor Abstürzen bei reinen Textsuchbegriffen mit Sonderzeichen
        pattern_str = keyword if is_regex else re.escape(keyword)
        regex = re.compile(pattern_str, re.IGNORECASE)
        
        # Nutzt die bestehende Filterlogik
        for rel_path_str in self.list_all_notes():
            full_path = self.obsidian_vault / rel_path_str
            
            try:
                content = full_path.read_text(encoding="utf-8", errors="surrogateescape")
                if regex.search(content):
                    results.append({
                        "title": full_path.stem,
                        "path": rel_path_str
                    })
            except Exception:
                continue  # Überspringt nicht lesbare Dateien sicher

        logging.info("Used search notes skill.")
                
        return results


    # Internet Suche
    def search_web(self, search_key):
        logging.info(f"Start searXNG search for: {search_key}")

        searxng_url = f"http://{self.searxng_ip}/search"
        params = {
            "q": search_key,
            "format": "json"
        }

        try:
            response = requests.get(searxng_url, params=params, timeout= self.searxng_timeout)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            logging.debug(f"Results of websearch: {results}")
            if not results:
                logging.error("No data from web search.")
                return "Es konnten keine Informationen im Internet gefunden werden."

            context = ""
            for i, item in enumerate(results[:5], 1):
                titel = item.get("title", "Kein Titel")
                content = item.get("content","")
                url = item.get("url","")
                context += f"Quelle: {i}: {titel}\nURL: {url}\nInhalt: {content}\n\n"

            return context

        except Exception as e:
            logging.error(f"SearXNG-Suche fehlgeschlagen: {e}")
            return "Es konnten keine aktuellen Informationne im Internet gefunden werden."
    
    # Weather Skill
    def get_weather(self, city_name:str) ->dict:
        logging.info("Use get_weather skill.")
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city_name,
            "appid": self.open_weather,
            "units": "metric",
            "lang": "de"
        }
        response = requests.get(url, params=params)
        logging.debug(f"Response: {response}")

        if response.status_code == 404:
            logging.error(f"City {city_name} not found.")
            return f"City {city_name} not found."

        if response.status_code == 401:
            logging.error("Api key invalid.")
            return "Api Key nicht gültig."
        response.raise_for_status()

        return {"forecast": self.summarize_by_day(response.json())}

    def summarize_by_day(self, data: dict) -> list[dict]:
        days = defaultdict(list)
        for entry in data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            days[date].append(entry)

        summary = []
        for date, entries in days.items():
            temps = [e["main"]["temp"] for e in entries]
            summary.append({
                "date": date,
                "temp_min": round(min(temps), 1),
                "temp_max": round(max(temps), 1),
                "description": entries[len(entries)//2]["weather"][0]["description"]
            })
        return summary


# 2. Die Tools manuell in das von Ollama erwartete JSON-Schema übersetzen
current_time_tool = {
    "type": "function",
    "function": {
        "name": "current_time",
        "description": "Gibt die aktuelle Systemzeit und das Datum zurück.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

list_all_notes_tool = {
    "type": "function",
    "function": {
        "name": "list_all_notes",
        "description": "Gibt eine Liste aller Pfade zu vorhandenen Markdown-Notizen in der Obsidian-Vault aus.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

read_note_content_tool = {
    "type": "function",
    "function": {
        "name": "read_note_content",
        "description": "Liest den Inhalt einer Datei. WICHTIG: Verwende als 'relative_path' IMMER den exakten String, den das Tool 'list_all_notes' oder 'search_notes' zurückgegeben hat (inklusive Unterordnern und '.md' Endung).",
        "parameters": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "Exakter relativer Pfad aus der Dateiliste, z.B. 'Programmiere/Python/libs/json Library.md'"
                }
            },
            "required": ["relative_path"],
        },
    },
}

search_notes_tool = {
    "type": "function",
    "function": {
        "name": "search_notes",
        "description": "Durchsucht den INHALT (Volltext) aller Notizen nach einem bestimmten Schlüsselwort. Nutze dieses Tool, wenn der Nutzer nach Themen oder internen Texten sucht, NICHT für reine Dateinamensuche.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Das Suchwort oder die Phrase."
                }
            },
            "required": ["keyword"],
        },
    },
}

search_web_tool = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Durchsucht das Internet mit SearXNG nach aktuellen Informationen, die nicht in den Notizen vorhanden sind.",
        "parameters": {
            "type": "object",
            "properties": {
                "search_key": {
                    "type": "string",
                    "description": "Der präzise Suchbegriff oder die Suchphrase für die Websuche."
                }
            },
            "required": ["search_key"],
        },
    },
}

get_weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Gibt die Wettervorhersage für eine Stadt zurück",
        "parameters": {
            "type": "object",
            "properties": {
                "city_name": {"type": "string", "description": "Stadtname, z.B. 'München'"}
            },
            "required": ["city_name"]
        }
    }
}