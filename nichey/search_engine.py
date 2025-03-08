import requests
import sys
from .lm import LM, LMResponse
from pydantic import BaseModel
from .logger import logger


class WebLink():
    def __init__(self, url, name="", language="", snippet="", query="", search_engine="") -> None:
        self.url = url
        self.name = name
        self.language = language
        self.snippet = snippet
        self.query = query
        self.search_engine = search_engine


class SearchEngine():
    def __init__(self, code):
        self.code = code
    
    # Returns tuple (list[WebLink], total: int)
    # The total includes hits not returned (so, it could be like 1 million or something)
    def search(self, query, max_n=10, offset=0):
        raise NotImplementedError("Search not implemented")

    # Returns deduplicated results from many queries
    def search_many(self, queries, max_per=10, offset_for_each=0) -> tuple[list[WebLink], int]:
        all_results = []
        all_urls = {}
        sum_total = 0
        for q in queries:
            results, total = self.search(q, max_n=max_per, offset=offset_for_each)
            results: list[WebLink]
            dedup = [x for x in results if x.url not in all_urls]
            for new_res in dedup:
                all_urls[new_res.url] = True
            all_results.extend(dedup)
            if total is None:
                sum_total = None
            elif sum_total is not None:
                sum_total += total
        return all_results, sum_total

    def gen_queries(self, lm: LM, topic, n=5):

        class Queries(BaseModel):
            queries: list[str]

        intro = f"Your task is to write about {n} search queries such as those that might appear in Google or Bing. Queries might also be put into a special search engine like Reddit or arXiv."
        body = "The queries you write must be in service of a research goal, which will be provided by the user. You should be creative. You might, for example, write queries that could accomplish subgoals within the research topic or lead to surprising new paths. You should use your background knowledge to determine what you might mention in the query."
        formatting = "You must write your queries in the proper JSON schema."
        system = " ".join([intro, body, formatting])

        res: LMResponse = lm.run(topic, system=system, json_schema=Queries)
        parsed: Queries = res.parsed
        return parsed.queries


class Bing(SearchEngine):
    def __init__(self, api_key, market='en-US'):
        self.api_key = api_key
        self.market = market
        super().__init__('bing')

    def search(self, query, max_n=10, offset=0):
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        # Refer here for bing market codes:  https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/market-codes
        mkt = self.market
        params = { 'q': query, 'mkt': mkt, 'count': max_n, 'offset': offset }  # count defaults to 10, can be up to 50
        headers = { 'Ocp-Apim-Subscription-Key': self.api_key }
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()  # will throw an error if the request isn't good
        my_json = response.json()
        try:
            total = my_json['webPages']['totalEstimatedMatches']
            raw_results = my_json['webPages']['value']
        except:
            logger.error(f"Could not get web pages from search engine. Here was the response: {my_json}")
            return [], 0
        
        results = []
        for i, x in enumerate(raw_results):
            if i >= max_n:
                break
            results.append(WebLink(
                x['url'],
                x['name'],
                language=x['language'],
                snippet=x['snippet'],
                query=query,
                search_engine=self.code
            ))
        return results, total
