import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
from ui import MainWindow

def main():
    load_dotenv() #loads .env file if it exists

    app = QApplication(sys.argv)
    app.setApplicationName("Nova Voice Assistant")

    #Try to get ket from .env first
    api_key = os.getenv("GEMINI_API_KEY")

    #IF not in .env, ask the user manually
    if not api_key:
        api_key, ok = QInputDialog.getText(
            None,
            "Gemini API Key",
            "Enter your Google Gemini API Key:"
        )
        if not ok or not api_key.strip():
            QMessageBox.warning(
                None,
                "No API Key"
                "A Gemini API Key is required to use Nova."
            )
            sys.exit(1)

    window = MainWindow(api_key=api_key.strip())
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()