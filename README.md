
# GRWiki

**Generate a wiki for your research topic, sourcing from the web and your docs**

GRWiki is a python package that helps create and manage targeted wikis for a research topic you specify. After building a wiki, you can serve it locally on `localhost` or export the pages to markdown files. To developers, feel free to create GUI wrappers around GRWiki and let us know about them!

## Installation

Install GRWiki using pip:

```
python3 -m pip install grwiki
```

And import it into your project like:

```
import grwiki
```

## Usage

See a complete [example](#example) below or refer to the [docs](./docs/). Broadly, the steps to create a wiki are as follows:

- Specify a language model
- Specify a search engine (optional)
- Generate queries based on a topic using a language model (optional)
- Use the search engine to find links to sources or specify links directly
- Create a Wiki object given a title and the topic
- Specify a scraper, and scrape the sources into the wiki, or specify local files as sources
- Extract entities from the sources to determine the pages
- Deduplicate entities (optional)
- Write the wiki entries
- Serve the wiki as a Flask app or export the pages to markdown

Afterward, you can update the wiki programatically or through the web interface. See details on the Wiki API in the docs [here](./docs/wiki.md).

### Example

```python
from grwiki import OpenAILM, Bing, WebLink, RequestsScraper, ScrapeServ, Wiki

# Choose some topic for the wiki
topic = """I'm researching the 2008 financial crisis. I want to get at the technical and in depth issues behind why it happened, the major players, and what ultimately came of it."""

# You'll need some language model from an OpenAI compatible API.
# If it's not the official OpenAI API, specify a base_url.
# Be sure to specify the model's context length using max_input_tokens.
OPENAI_API_KEY = "YOUR-API-KEY"
lm = OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, api_key=OPENAI_API_KEY, base_url=None)

# Optional: If you have a Bing API key, then you can use Bing to search for web sources (see https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
# BING_API_KEY = "18c7580112914cf3947bcc4ef5d23cc1"
# search_engine = Bing(BING_API_KEY)
# queries: str = search_engine.gen_queries(lm, topic)
# results, total = search_engine.search_many(queries)

# If you don't have access to a search engine, you can specify URLs manually.
# These are some URLs for the 2008 financial crisis topic
urls = [
    "https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath",
    "https://en.wikipedia.org/wiki/2008_financial_crisis",
    "https://www.economicsobservatory.com/why-did-the-global-financial-crisis-of-2007-09-happen"
]
results = [WebLink(url=x) for x in urls]

# Optional: To scrape the results with high quality, you can use an advanced ScrapeServ client:
# scraper = ScrapeServ()
# ... see ScrapeServ: https://github.com/goodreasonai/ScrapeServ

# Or you can use a RequestsScraper, which everyone has:
scraper = RequestsScraper()

# Now you should actually instantiate the wiki:
wiki = Wiki(topic=topic, title="Global Financial Crisis", path="gfc.db", replace=False)

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
```

## Contributing

Please do look at the open issues and consider constributing! This software is completely free and open source. You can create your own GUI wrappers or contribute core API functionality. For dev environement setup, refer below. Otherwise, see [CONTRIUBTING.md](./CONTRIBUTING.md)

Make a virtual environment and install the dev dependencies:

```
python3 -m venv venv
python3 -m pip install -r requirements-dev.txt
```

Install the package in edit mode:

```
python3 -m pip install -e .
```

For testing, see [here](tests/README.md).

If you want to work on the frontend, see [here](frontend/README.md).
