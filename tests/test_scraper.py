import nichey as wiki

# Need to have a ScrapeServ instance available at http://localhost:5006 (no API key)
def test_scrape_serv():
    url = 'https://goodreason.ai'
    scraper = wiki.ScrapeServ()
    response: wiki.ScrapeResponse = scraper.scrape(url)
    assert(response.status == 200)
    assert(response.metadata.content_type == 'text/html')
    with response.consume_data() as path:
        with open(path) as fhand:
            content = fhand.read()
            assert(content.find('AI') != -1)
    
    # Don't check what the screenshots look like, just that they're present
    assert(len(response.screenshot_paths) > 0)


def test_requests_scraper():
    url = 'https://goodreason.ai'
    scraper = wiki.RequestsScraper()
    response: wiki.ScrapeResponse = scraper.scrape(url)
    assert(response.status == 200)
    assert(response.metadata.content_type == 'text/html')
    with response.consume_data() as path:
        with open(path) as fhand:
            content = fhand.read()
            assert(content.find('AI') != -1)
    # Can't check screenshots beacuse there are none!
