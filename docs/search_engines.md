# Search Engines

This library supports the Bing API. If you would like to add more search engines, please feel free to contribute!

## WebLink

WebLink objects are returned from a search engine. These objects look like:

```python
class WebLink():
    def __init__(self, url, name="", language="", snippet="", query="", search_engine="") -> None:
        self.url = url
        self.name = name
        self.language = language
        self.snippet = snippet
        self.query = query
        self.search_engine = search_engine
```

## Bing

Accepts:

- `api_key`: A Bing API key you've received from Azure
- `market`: defaults to `en-US`

Functions:

- `search(self, query, max_n=10, offset=0)`: Given a search engine query as a string, return at most `max_n` WebLink objects with an offset of `offset`
- `search_many(self, queries, max_per=10, offset_for_each=0)`: Given a list of query as strings, return a tuple like (results, total) where results is a deduplicated list of WebLink objects
- `gen_queries(self, lm: LM, topic, n=5)`: Given a language model object and a topic, return a list of `n` strings which can be used as queries for find information about the topic. 

