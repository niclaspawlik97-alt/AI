import logging
import json
import os
from pathlib import Path

class Logger:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            
            # Absoluten Pfad zum Projektverzeichnis ermitteln und logs-Ordner erstellen
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)

            self.logger_path = log_dir/f"{config['ai_appearance']['ai_name']}.log"

            if self.logger_path.exists():
                os.remove(self.logger_path)
            
            # Dateiname zusammensetzen und als String speichern
            self.logger_path_conect = str(self.logger_path)



            self.logger_level = config["logging"]["level"]

    def logger_init(self):
        logger_level_ = getattr(logging, self.logger_level.upper(), logging.INFO)
        
        # force=True überschreibt bestehende Logging-Konfigurationen anderer Bibliotheken
        logging.basicConfig(
            filename=self.logger_path_conect,
            filemode='a',
            level=logger_level_,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True  
        )
        
        # Test-Logeintrag, um sofort zu prüfen, ob die Datei erstellt wird
        logging.info("Logging-System erfolgreich initialisiert.")
