from .secrets import OPENAI_API_KEY
import wiki

def test_openai_lm():
    lm = wiki.OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, accepts_images=True, api_key=OPENAI_API_KEY)
    res: wiki.LMResponse = lm.run("Hello!", system="If the user says hello, say 'Electronics'. Otherwise say, 'Peas'.")
    assert(res.text.find('Electronics') != 1)
