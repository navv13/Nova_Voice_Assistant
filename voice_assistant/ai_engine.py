from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are Nova, a smart and friendly voice assistant.
Keep your answers concise (2-3 sentences max) since they will be spoken aloud.
Be helpful, clear, and conversational. Never use markdown formatting."""


class AIEngine:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.history = []

    def ask(self, prompt: str) -> str:
        try:
            self.history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=self.history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                )
            )

            reply = response.text.strip()

            self.history.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=reply)]
                )
            )

            return reply

        except Exception as e:
            return f"AI error: {e}"

    def reset(self):
        self.history = []