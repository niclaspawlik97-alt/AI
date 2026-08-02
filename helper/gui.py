import json
import threading
import customtkinter as ctk

from helper.ai import AI


class gui:

    def __init__(self, config_path="config.json"):
        # Config einlesen
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            self.gui_config = config["gui_settings"]
            self.ai_name = config["ai_appearance"]["ai_name"]

        self.ai = AI(config_path)
        self.window = None

    def create_window(self, title: str, width: int, height: int):
        ctk.set_appearance_mode(self.gui_config["appearance"])
        ctk.set_default_color_theme(self.gui_config["default_color_theme"])

        # Fenster konfigurieren
        self.window = ctk.CTk()
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")

        # Layout Raster festlegen
        self.window.grid_rowconfigure(0, weight=1)
        # KORREKTUR: Spalten-Gewichtung für flüssige Breitenanpassung hinzugefügt
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=0)
        self.window.grid_columnconfigure(2, weight=0)

        # Chat-Verlauf
        self.chat_history = ctk.CTkTextbox(
            self.window, state="disabled", wrap="word"
        )
        self.chat_history.grid(
            row=0, column=0, columnspan=3, padx=20, pady=20, sticky="nsew"
        )

        # Eingabefeld
        self.entry_message = ctk.CTkEntry(
            self.window, placeholder_text="Schreibe eine Nachricht..."
        )
        self.entry_message.grid(
            row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="ew"
        )
        self.entry_message.bind(
            "<Return>", lambda event: self.start_chat_thread()
        )

        # Senden-Button
        self.btn_send = ctk.CTkButton(
            self.window, text="Senden", command=self.start_chat_thread
        )
        self.btn_send.grid(
            row=1, column=1, padx=(10, 10), pady=(0, 20), sticky="e"
        )

        # Reset-Button
        self.btn_reset = ctk.CTkButton(
            self.window,
            text="Reset",
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self.clear_chat,
        )
        self.btn_reset.grid(
            row=1, column=2, padx=(10, 20), pady=(0, 20), sticky="e"
        )

    # KORREKTUR: Einrückung auf Klassenebene angepasst
    def clear_chat(self):
        """Löscht die Anzeige und setzt das KI-Modell zurück."""
        self.ai.reset_history()
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.configure(state="disabled")

    def append_to_chat(self, sender, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"{sender}: {text}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def start_chat_thread(self):
        user_text = self.entry_message.get().strip()
        if not user_text:
            return

        self.entry_message.delete(0, "end")
        self.btn_send.configure(state="disabled")
        self.append_to_chat("Du", user_text)

        threading.Thread(
            target=self.get_ai_response, args=(user_text,), daemon=True
        ).start()

    def get_ai_response(self, message):
        try:
            ai_text = self.ai.call_model_chat(message)

            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"{self.ai_name}: {ai_text}\n\n")
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")

            self.ai.save_assistant_response(ai_text)

        except Exception as e:
            self.append_to_chat(self.ai_name, f"Fehler: {str(e)}")

        self.btn_send.configure(state="normal")

    def append_stream_to_chat(self, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text)
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def run(self):
        if self.window:
            self.window.mainloop()
