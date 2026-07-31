from helper import ai, gui
from helper.logger import Logger

logger_instance = Logger()
logger_instance.logger_init()

ai_inst = ai.AI()
app = gui.gui()

app.create_window("Jarvis", 800, 500)
app.run()

