# Wiki

The wiki object is the heart of this project. A wiki stores its data in a sqlite database specified by `path`. The database contains the sources and the articles. There are two general approaches: use the functions that automate the writing/extracting/searching/scraping process, or do it manually using a variety of the functions below.

## Initialization and Attributes

A wiki object is intitialized and used like:

```python
from nichey import wiki

wiki = Wiki(topic="I'm researching...", title="", path=None, replace=False, entity_types=None)
```

- `topic` (mandatory): A string with a full explanation of your research goals with this wiki. This text will be passed to the language model when it writes articles and extracts entities. It's good to be detailed here, and don't afraid to make this long.
- `title` (optional): An optional title to give your wiki
- `path` (optional, defaults to `wiki.sqlite`): where to store the wiki
- `replace` (optional, defaults to `False`): whether the database in `path` should be added to or replaced (dangerous!)
- `entity_types` (optional): Determines the types of entities the LM will be prompted to create in `make_entities`. If `None`, defaults to: `["person", "place", "organization", "event", "publication", "law", "product", "object", "concept"]`.

## Functions

The wiki class exposes functions to create the wiki.

### Adding Sources

- `scrape_web_results(self, scraper: Scraper, results: list[WebLink], max_n: int=None) -> list[tuple[WebLink, Source | None]]`: Scrapes a maximum of `max_n` (infinity if None) `results` (given as `WebLink` objects) using a `scraper` of type `Scraper` (like a RequestsScraper) and stores them in the database. URLs that are already scraped will be skipped.
- `load_local_sources(self, paths: list[str]) -> list[Source]`: Loads local files as sources
-  `add_source(self, title: str, text: str, author: str=None, desc: str=None, url: str=None, snippet: str=None, query: str=None, search_engine: str=None, are_entities_extracted=False) -> Source`: Manually lets you add a source; you must provide a `title` and `text`, where `text` is the actual content of the source. All other arguments are optional metadata.

### Creating Entities / Pages

The pages in the wiki are referred to as entities.

- `make_entities(self, lm: LM, max_sources=None) -> list[tuple[Source, list[Entity]]]`: Processes up to `max_sources` unprocessed sources (or all if `max_sources` is `None`), extracting from them entities (of type person, place, thing, etc.). Takes an LM object (like an OpenAILM) and uses a json schema. The entities created will not have the same title or slug as any other, but there may still be conceptual duplicates.
- `add_entity(self, title: str, type: str=None, desc: str=None, markdown: str=None) -> Entity`: Manually adds a new entity and returns it as a dataclass object, which will include its unique slug and ID. The `markdown` argument is its corresponding article, which can be left as `None` if it's unwritten.

### Writing Articles

The articles are stored as markdown associated with each entity (1 to 1). Note that links to different pages in the wiki use Wikilink format, and references to sources are written like: `[[@25]]` where 25 is the ID of a source.

- `write_articles(self, lm: LM, max_n=None, rewrite=False) -> list[Entity]`: Will write up to `max_n` articles (or all unwritten articles if None) using a language model `lm`. If `rewrite` is `True`, it will rewrite already written articles; otherwise, they will be skipped. Calls `write_article` for each entity.
- `write_article(self, lm: LM, entity_slug: str) -> Entity | None`: Writes an article for a specific entity from its slug, returning an Entity dataclass object, or `None` if an error occurred. To see debugging info, [configure logging](./logging.md). This function uses references and full text search to find relevant sources (references are made when extracting entities, or when using `add_reference`).
- `heal_markdown(self, markdown: str) -> str`: Fixes common mistakes in the Markdown (such as not specifying cross links or references properly). It is automatically called inside `write_article`.

### Editing

- `update_entity_by_slug(self, slug, title: str = None, type: str = None, desc: str = None, markdown: str=None) -> None`: Updates an entity based on the slug to match the provided arguments. Any options that are left as `None` won't be touched.
- `update_source_by_id(self, id, title: str = None, author: str = None, desc: str = None, url: str=None, snippet: str = None, query: str = None) -> None`: SAA except for sources identified by their ID
- `delete_source_by_id(self, id) -> None`: Self explanatory
- `delete_entity_by_slug(self, slug) -> None:`: Self explanatory
- `add_reference(self, entity_id, source_id)`: Adds a reference betwen an entity and a source. If using `write_article` or `write_articles`, this guarantees that a particular source will be used when writing the article for a given entity.
- `deduplicate_entities(self, lm: LM, max_groups=None, group_size=100) -> int`: Uses a language model to deduplicate entities based on their titles. Note that it works by first ordering the sources alphabetically and going `group_size` entities at a time, so it may fail if the entities are far from each other alphabetically. It will process at most `max_groups` times `group_size` entities. Returns the number of removed entities.

### Inspecting

- `get_all_entities(self, limit=5000, offset=0) -> list[Entity]`: Returns all entities as a list of Entity dataclass objects (subject to the limit and offset)
- `get_all_sources(self, limit=5000, offset=0) -> list[Source]:`: SAA but for sources
- `get_entity_by_slug(self, slug) -> Entity`: SAA but for entities based on slug
- `get_entities_by_type(self, type) -> list[Entity]`: Returns a list of entities based on their type (which would be strings like `person`, `event`, `concept`, etc.)
- `get_referenced_sources(self, entity_id, limit=1000, offset=0) -> list[Source]`: Returns all sources that are associated with a particular entity. It may return more sources than were explicitly referenced in the Entity's written page, since the references are created during extraction, not writing.
- `get_source_by_id(self, id) -> Source:`: Returns an existing Source as a dataclass object from its ID
- `search_sources_by_text(self, query) -> list[Source]`: Returns a list of Sources as dataclass objects using FTS5 full-text search. The search includes the title, author, description, and text of the source.

### Using

- `export(self, dir="output", remove_cross_refs=True, remove_source_refs=True)`: Exports each entity as a markdown file into a new folder (by default, "output"). If `remove_cross_refs` is `True`, then links to other wiki pages will be replaced with plain text. If `remove_source_refs` is `True`, then source references (like `[[@1]]`) will be removed.
- `serve(self, port=5000)`: Makes a single threaded development server available on localhost at `port`. **You should not use this server in production.**
