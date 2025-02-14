from openai import OpenAI 

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
            api_key=api_key,
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


"""

Percentage of context length that should be used for retrieval in various places in the code base.
Can / should be changed based on typical model behavior and speed.

Sample outputs:
- 5_000 -> 2_500
- 10_000 -> 7_000
- 32_000 -> 23_500
- 100_000 -> 57_500
- 200_000 -> 107_500

"""
def get_safe_context_length(model: LM):
    # Works like tax brackets
    brackets = [
        (5_000, .5),  # 50% of the first 5000 tokens
        (10_000, .9),  # 90% of tokens 5000-10000
        (32_000, .75),  # etc
        (100_000, .5)
    ]
    cl_remaining = model.max_input_tokens
    safety_cl = 0
    prev = 0
    for bracket in brackets:
        overlap = min(cl_remaining, bracket[0] - prev)
        contribution = overlap * bracket[1]
        safety_cl += contribution
        cl_remaining -= bracket[0] - prev
        prev = bracket[0]
        if cl_remaining <= 0:
            break
    
    if cl_remaining > 0:
        safety_cl += cl_remaining * brackets[-1][1]

    return round(safety_cl)
