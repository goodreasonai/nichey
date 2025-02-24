from grwiki import OpenAILM, Bing, RequestsScraper, Wiki

"""

This full example requires a search engine API (here, using Bing).

If you don't have access to the Bing API, consider looking at `minimal_example.py`

"""

# Choose some topic for the wiki
topic = """I'm researching new AI products that help with coding, like Cursor (Anysphere) or Cline.
I'm a VC and would like to get a better idea of the landscape of AI coding tools.
"""

# You'll need some language model from an OpenAI compatible API.
# If it's not the official OpenAI API, specify a base_url.
# Be sure to specify the model's context length using max_input_tokens.
OPENAI_API_KEY = "YOUR-API-KEY"
lm = OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, api_key=OPENAI_API_KEY, base_url=None)

# Optional: If you have a Bing API key, then you can use Bing to search for web sources (see https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
BING_API_KEY = "YOUR-BING_API_KEY"
search_engine = Bing(BING_API_KEY)
queries: str = search_engine.gen_queries(lm, topic)
results, total = search_engine.search_many(queries)

# Optional: To scrape the results with high quality, you can use an advanced ScrapeServ client:
# scraper = ScrapeServ()
# ... see ScrapeServ: https://github.com/goodreasonai/ScrapeServ

# Or you can use a RequestsScraper, which everyone has:
scraper = RequestsScraper()

# Now you should actually instantiate the wiki:
wiki = Wiki(topic=topic, title="AI Coding Products", path="ai_coding.db", replace=False)

# Then scrape sources and store them in the wiki:
wiki.scrape_web_results(scraper, results)

# This will extract entities from your sources, which will form the pages of the wiki
wiki.make_entities(lm)

# Optional: Can help prevent duplicate entries
wiki.deduplicate_entities(lm)

# This will write the articles (for maximum 5 pages so you can just try it out)
wiki.write_articles(lm, max_n=5)

# This will make the wiki available on localhost via a Flask server
wiki.serve()

# Optional: export to Markdown (with cross links and references removed)
# wiki.export(dir="output")
