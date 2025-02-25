import nichey as wiki
from .lm import get_lm


def test_lm_run():
    lm = get_lm()
    res: wiki.LMResponse = lm.run("Hello!", system="If the user says hello, say 'Electronics'. Otherwise say, 'Peas'.")
    assert(res.text.find('Electronics') != 1)


def test_context_controls():
    # Intentionally low max input tokens
    MAX_INPUT_TOKENS = 3000
    lm = get_lm(max_input_tokens=MAX_INPUT_TOKENS, fail_on_overflow=True)
    rep_str = "The cake is a lie. "  # This is 5-6 tokens 
    texts = [rep_str * 1_000 for _ in range(5)]
    prompt = wiki.make_retrieval_prompt(lm, texts)
    assert(wiki.get_token_estimate(prompt) < MAX_INPUT_TOKENS)
    try:
        lm.run("You're probably gonna hate this... "*400, system=rep_str*400)
        assert(1==0)
    except wiki.ContextExceeded:
        assert(1==1)
