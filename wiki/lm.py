from openai import OpenAI 
import os

class LMResponse():
    def __init__(self, text):
        self.text = text

class LM():
    def __init__(self, model, api_key=None, base_url=None):
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        )

    def _make_messages(self, prompt, system, context: list):
        return [
            {
                'role': 'developer',
                'content': system
            },
            *context,
            {
                'role': 'user',
                'content': prompt,
            }
        ]

    def run(self, prompt, system, context: list):
        messages = self._make_messages(prompt, system, context)
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o",
        )
        return LMResponse(chat_completion.choices[0].message.content)
