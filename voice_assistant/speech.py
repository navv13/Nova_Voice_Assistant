import speech_recognition as sr
import pyttsx3
import threading

class SpeechEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
    def _configure_tts(self):
        self.tts_engine.setProperty("rate",170)
        self.tts_engine.setProperty("volume", 1.0)

        voices = self.tts_engine.getProperty("voices")
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.name.lower():
                self.tts_engine.setProperty("voice", voice.id)
                break
    def speak(self, text: str, on_done=None):
        def _run():
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            if on_done:
                on_done()
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    def listen(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=12)
            except sr.WaitTimeoutError:
                return None
            
        
        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            raise ConnectionError(f"Google Speech API error: {e}")



# Testing
# if __name__ == "__main__":
#     engine = SpeechEngine()
#     engine.speak("Hello, I am Nova. Say something!")
#     import time; time.sleep(2)
#     result = engine.listen()
#     print("You said:", result)