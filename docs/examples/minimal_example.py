

from nichey import OpenAILM, RequestsScraper, Wiki, WebLink

"""

This minimal example only requires access to an OpenAI compatible API.

"""

# Choose some topic for the wiki
topic = """I'm researching the 2008 financial crisis. I want to get at the technical and in depth issues behind why it happened, the major players, and what ultimately came of it."""

# You'll need some language model from an OpenAI compatible API.
# If it's not the official OpenAI API, specify a base_url.
# Be sure to specify the model's context length using max_input_tokens.
OPENAI_API_KEY = "YOUR-API-KEY"
lm = OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, api_key=OPENAI_API_KEY, base_url=None)

urls = [
    "https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath",
    "https://en.wikipedia.org/wiki/2008_financial_crisis",
    "https://www.economicsobservatory.com/why-did-the-global-financial-crisis-of-2007-09-happen"
]
results = [WebLink(url=x) for x in urls]
scraper = RequestsScraper()

# Now you should actually instantiate the wiki:
wiki = Wiki(topic=topic, title="Global Financial Crisis", path="gfc.db")

# Then scrape sources and store them in the wiki:
wiki.scrape_web_results(scraper, results)

# This will extract entities from your sources, which will form the pages of the wiki
wiki.make_entities(lm)

# This will write the articles (for maximum 5 pages so you can just try it out)
wiki.write_articles(lm, max_n=5)

# This will make the wiki available on localhost via a Flask server
wiki.serve()

# Optional: export to Markdown (with cross links and references removed)
# wiki.export(dir="output")
