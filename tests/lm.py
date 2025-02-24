import grwiki as wiki
from .secrets import OPENAI_API_KEY, OPEN_ROUTER_API_KEY

def get_lm(
        model='google/gemini-2.0-flash-001',
        max_input_tokens=250_000,
        accepts_images=True,
        api_key=OPEN_ROUTER_API_KEY,
        fail_on_overflow=False,
        base_url="https://openrouter.ai/api/v1"
    ):

    lm = wiki.OpenAILM(model=model, max_input_tokens=max_input_tokens, accepts_images=accepts_images, api_key=api_key, fail_on_overflow=fail_on_overflow, base_url=base_url)
    
    return lm
