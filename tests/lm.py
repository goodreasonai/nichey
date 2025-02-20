import wiki
from .secrets import OPENAI_API_KEY

def get_lm(model='gpt-4o-mini', max_input_tokens=128_000, accepts_images=True, api_key=OPENAI_API_KEY, fail_on_overflow=False):
    lm = wiki.OpenAILM(model=model, max_input_tokens=max_input_tokens, accepts_images=accepts_images, api_key=api_key, fail_on_overflow=fail_on_overflow)
    return lm
