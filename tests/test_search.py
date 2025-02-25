import nichey as wiki
from .secrets import BING_API_KEY

def test_bing():
    search_engine = wiki.Bing(BING_API_KEY)
    MAX_N = 15
    res, tot = search_engine.search("Napoleon", max_n=MAX_N)
    assert(tot > MAX_N)  # There should be plenty of results
    assert(len(res) == MAX_N)
    for result in res:
        result: wiki.WebLink
        assert(type(result.url) == str)
