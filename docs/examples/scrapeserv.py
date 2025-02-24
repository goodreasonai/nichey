from grwiki import OpenAILM, ScrapeServ, Wiki, WebLink

"""

ScrapeServ (https://github.com/goodreasonai/ScrapeServ) uses a web browser to properly execute Javascript and take screenshots, which makes it more likely accurately capture the content of a page.

Both the text and screenshots collected may be used by the wiki to extract entities and write articles.

"""

wiki = Wiki(topic="")
scraper = ScrapeServ(url="http://localhost:5006", api_key=None)
wiki.scrape_web_results(scraper, [WebLink(url="https://goodreason.ai")])

# The source is now scraped and available in the wiki!