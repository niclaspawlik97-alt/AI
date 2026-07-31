import re
import json
import logging
from datetime import datetime
from pathlib import Path

class Skills:

    def __init__(self, secrets_path="secrets.json"):
        with open(secrets_path, "r", encoding="utf-8") as file:
            secrets = json.load(file)
            self.obsidian_vault = Path(secrets["folders"]["obsidian_vault"])
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
                
        return results

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
