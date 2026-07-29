from datetime import datetime

def curent_time() -> str:
    """Gibt die aktuelle Systemzeit und das Datum zurück."""
    # Zeit direkt als lesbaren Text formatieren
    return datetime.now().strftime("%H:%M:%S Uhr")

# 2. Das Tool manuell in das von Ollama erwartete JSON-Schema übersetzen
curent_time_tool = {
    "type": "function",
    "function": {
        "name": "curent_time",
        "description": "Gibt die aktuelle Systemzeit und das Datum zurück.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}