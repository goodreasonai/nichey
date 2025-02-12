from openai import OpenAI 
import os

class LMResponse():
    def __init__(self, text, parsed=None):
        self.text = text
        self.parsed = parsed


class LM():
    def __init__(self, max_input_tokens=8096, accepts_images=False):
        self.max_input_tokens = max_input_tokens
        self.accepts_images = accepts_images

    # json_schema is a class that inherits from Pydantic BaseModel (not an object)
    def run(self, prompt, system, context: list, json_schema=None):
        raise NotImplementedError("Run is not implemented")


class OpenAILM(LM):
    def __init__(self, model, max_input_tokens=None, accepts_images=False, api_key=None, base_url=None):
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        )
        super().__init__(max_input_tokens, accepts_images)

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

    def run(self, prompt, system, context: list = [], json_schema=None):
        messages = self._make_messages(prompt, system, context)
        if json_schema is None:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
            )
            return LMResponse(chat_completion.choices[0].message.content)
        else:
            chat_completion = self.client.beta.chat.completions.parse(
                messages=messages,
                model="gpt-4o",
                response_format=json_schema
            )
            msg = chat_completion.choices[0].message
            return LMResponse(msg, parsed=msg.parsed)
