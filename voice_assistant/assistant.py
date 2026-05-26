import threading
from speech import SpeechEngine
from ai_engine import AIEngine
from commands import handle_command

class Assistant:
    def __init__(self, gemini_api_key: str):
        self.speech = SpeechEngine()
        self.ai = AIEngine(api_key=gemini_api_key)
        self.listening = False

        # These will be set by the UI later
        self.on_user_text = None
        self.on_assistant_text = None
        self.on_status = None
        self.on_listening_change = None

    # ---Internal Helpers----------------

    def _emit_status(self, msg: str):
        if self.on_status:
            self.on_status(msg)
        
    def _emit_user(self, text: str):
        if self.on_user_text:
            self.on_user_text(text)
    
    def _emit_assistant(self, text: str):
        if self.on_assistant_text:
            self.on_assistant_text(text)
    
    def _set_listening(self, state: bool):
        self.listening = state
        if self.on_listening_change:
            self.on_listening_change(state)

    # ---Public API----------------

    def process_text(self, text: str):
        self._emit_user(text)

        # 1. Try Local commands first
        result = handle_command(text)
        if result:
            self._emit_assistant(result)
            self.speech.speak(result)
            return
        
        # 2. Fall back to Gemini AI
        self._emit_status("Thinking...")
        reply = self.ai.ask(text)
        self._emit_assistant(reply)
        self.speech.speak(reply, on_done=lambda: self._emit_status("Ready"))

    def listen_once(self):
        def _run():
            self._set_listening(True)
            self._emit_status("Listening...")
            try:
                text = self.speech.listen()
                if text:
                    self._emit_status("Processing...")
                    self.process_text(text)
                else:
                    self._emit_status("Didn't catch that. Try again.")
            except ConnectionError as e:
                self._emit_status(str(e))
            finally:
                self._set_listening(False)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def reset_conversation(self):
        self.ai.reset()
        self._emit_status("Conversation reset.")