import re
import json
from datetime import datetime
from pathlib import Path

class Skills:

    def __init__(self, secrets_path="secrets.json"):
        with open(secrets_path, "r", encoding="utf-8") as file:
            secrets = json.load(file)
            self.obsidian_vault = Path(secrets["folders"]["obsidian_vault"])

    def current_time(self) -> str:
        """Gibt die aktuelle Systemzeit und das Datum zurück."""
        # Zeit direkt als lesbaren Text formatieren
        return datetime.now().strftime("%H:%M:%S Uhr")

    # Obsidian Vault Skill
    def list_all_notes(self) -> list[str]:
        """Gibt eine Liste aller Pfade zu Markdowndatein aus."""
        return [
            str(p.relative_to(self.obsidian_vault)) 
            for p in self.obsidian_vault.glob("**/*.md")
            if ".obsidian" not in p.parts
        ]

    def read_note_content(self, relative_path: str) -> str:
        """Liest den exa´kten Inhalt einer bestimmten Notiz."""
        file_path = self.obsidian_vault / relative_path
        if not file_path.exists() or not file_path.is_file():
            return ("Fehler: Datei existiert nicht.")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def search_notes(self,keyword: str) -> list[dict]:
        """Durchsucht alle Notizen nach einem Begriff (einfache Regex-Suche)."""
        results = []
        # Ignoriert versteckte Ordner wie .obsidian
        for path in self.obsidian_vault.glob("**/*.md"):
            if ".obsidian" in path.parts:
                continue
                
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if re.search(keyword, content, re.IGNORECASE):
                    results.append({
                        "title": path.stem,
                        "path": str(path.relative_to(self.obsidian_vault))
                    })
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
        "description": "Liest den exakten Inhalt einer bestimmten Notiz anhand ihres relativen Pfads.",
        "parameters": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "Der relative Pfad zur Markdown-Datei aus der Notizliste (z.B. 'Ordner/Notiz.md')."
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
        "description": "Durchsucht den Inhalt aller Notizen in der Vault nach einem bestimmten Suchbegriff oder Schlagwort.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Das Wort oder Phrasensegment, nach dem in den Notizen gesucht werden soll."
                }
            },
            "required": ["keyword"],
        },
    },
}
