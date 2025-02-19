from openai import OpenAI 
from .utils import get_token_estimate
from .file_loaders import TextSplitter
from .exceptions import ContextExceeded


class LMResponse():
    def __init__(self, text, parsed=None):
        self.text = text
        self.parsed = parsed


class LM():
    def __init__(self, max_input_tokens=8096, accepts_images=False, fail_on_overflow=False):
        self.max_input_tokens = max_input_tokens
        self.accepts_images = accepts_images
        self.fail_on_overflow = fail_on_overflow

    # json_schema is a class that inherits from Pydantic BaseModel (not an object)
    def run(self, prompt, system, context: list, json_schema=None):
        raise NotImplementedError("Run is not implemented")


class OpenAILM(LM):
    def __init__(self, model, max_input_tokens=8096, accepts_images=False, api_key=None, base_url=None, fail_on_overflow=False):
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        super().__init__(max_input_tokens, accepts_images, fail_on_overflow)

    def _make_messages(self, prompt, system, context: list):
        messages = [
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
        if self.fail_on_overflow:
            total_tokens = sum([get_token_estimate(x['content']) for x in messages])
            if total_tokens > self.max_input_tokens:
                raise ContextExceeded(f"OpenAILM {self.model} was given {total_tokens} but only has room for {self.max_input_tokens}")
        return messages

    def run(self, prompt, system="", context: list = [], json_schema=None):
        messages = self._make_messages(prompt, system, context)
        if json_schema is None:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
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


def make_retrieval_prompt(lm: LM, texts, prefixes: list | str = "<BEGIN SOURCE>", suffixes: list | str = "</END SOURCE>", min_source_length=1000):
    room = get_safe_context_length(lm)

    n_texts = len(texts)

    per_source_token_limit = max(room // n_texts, min_source_length)

    total_tokens_used = 0
    prompt = "\n\n"

    if type(prefixes) == str:
        prefixes = [prefixes for _ in range(len(texts))]
    if type(suffixes) == str:
        suffixes = [suffixes for _ in range(len(texts))]
    
    assert(len(suffixes) == len(texts))
    assert(len(prefixes) == len(prefixes))

    for i, text in enumerate(texts):
        prompt += prefixes[i]
        tokens_used = 0

        prompt_src_text = ""
        splitter = TextSplitter()
        for chunk_txt in splitter.split_text(text):
            new_tokens = get_token_estimate(chunk_txt)
            src_exceeds_limit = new_tokens + tokens_used > per_source_token_limit
            overall_exceeds_limit = new_tokens + tokens_used + total_tokens_used > room
            if src_exceeds_limit or overall_exceeds_limit:
                break
            prompt_src_text += chunk_txt
            tokens_used += new_tokens
        total_tokens_used += tokens_used

        prompt += prompt_src_text
        prompt += f"\n{suffixes[i]}\n\n"

    return prompt
