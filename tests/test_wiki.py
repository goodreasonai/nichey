import wiki
from .utils import get_tmp_path
import os
from .secrets import OPENAI_API_KEY


def test_entities():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        title = "Tom Seaver"
        type = "person"
        mywiki.add_entity(title=title, type=type)
        ents = mywiki.get_entities_by_type(type)
        assert(len(ents) == 1)
        assert(ents[0].title == title)
        assert(ents[0].type == type)

        mywiki.delete_entity_by_slug(ents[0].slug)
        ents = mywiki.get_entities_by_type(type)
        assert(len(ents) == 0)
    finally:
        os.remove(mywiki.path)


def test_sources():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        title = "The Stranger"
        author = "Albert Camus"
        text = "Aujourd'hui, maman est morte. Ou peut-être hier, je ne sais pas."
        mywiki.add_source(title=title, author=author, text=text)
        search_text = "Maman est morte"
        sources = mywiki.search_sources_by_text(search_text)
        assert(len(sources) == 1)
        assert(sources[0].title == title)
        assert(sources[0].author == author)

        mywiki.delete_source_by_id(sources[0].id)
        source = mywiki.get_source_by_id(id=sources[0].id)
        assert(source is None)
    finally:
        os.remove(mywiki.path)


def test_make_entities():
    topic = "I'm interested in baseball: everything about it - the players, the parks, the teams, I love them! I am researching them all."
    mywiki = wiki.Wiki(path=get_tmp_path(), topic=topic)
    try:
        # Add 2 sources with some obvious entities

        # Definitely should have: New York Mets, William Shea, Shea Stadium, Citi Field
        mywiki.add_source(
            title="New York Mets Media Guide",
            desc="The official 2025 media guide of the New York Mets.",
            text="""
                The New York Mets were founded in 1962.
                One figure responsible for bringing the Mets into existence was William Shea, a lawyer who was instrumental in establishing the team.
                In fact, the Mets would go on to name their stadium after him, Shea Stadium.
                The Mets currently play at Citi Field.
            """
        )
        # Definitely should have: 1986 World Series, Mookie Wilson, Bill Buckner
        mywiki.add_source(
            title="",
            desc="Mets 1986 Yearbook",
            text="""
                It was the 1986 World Series - and the whole season came down to this plate appearance.
                Mookie Wilson was the batter. He hits a little roller up the first base side - and it went through the Red Sox first baseman Bill Buckner's legs!
                The Mets would go on to win the game and the series.
            """
        )
        lm = wiki.OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, accepts_images=True, api_key=OPENAI_API_KEY)
        details = mywiki.make_entities(lm)
        entities: list[wiki.Entity] = []
        for d in details:
            entities.extend(d[1])

        assert(len(entities))

        mandatory_entities = ['New York Mets', 'Citi Field', 'Shea Stadium', 'William Shea', 'World Series', 'Bill Buckner']
        # Could also have Boston Red Sox, maybe some others.
        for tit in mandatory_entities:
            found = False
            for ent in entities:
               if tit in ent.title:
                   found = True
                   break
            assert(tit and found)  # the tit part is just so it shows up in the error message

    finally:
        os.remove(mywiki.path)


def test_scrape_web_results():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    results = [wiki.WebLink(url="https://goodreason.ai")]
    scraper = wiki.RequestsScraper()
    mywiki.scrape_web_results(scraper, results)

    sources = mywiki.get_all_sources()
    assert(len(sources) == 1)
    sources = mywiki.search_sources_by_text("Gordon Kamer")
    assert(len(sources) == 1)


def test_write_entities():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="I'm interested the history of technology of the middle of the 20th century.")
    lm = wiki.OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, accepts_images=True, api_key=OPENAI_API_KEY)
    url = "https://en.wikipedia.org/wiki/John_Bardeen"
    scraper = wiki.RequestsScraper()
    results = [wiki.WebLink(url=url)]
    mywiki.scrape_web_results(scraper, results)
    sources = mywiki.search_sources_by_text("John Bardeen")
    assert(len(sources))

    # Rather than extract (which is not being tested here, just skip to write)
    mywiki.add_entity(title="John Bardeen", type="person", desc="John Bardeen was a co-inventor of the transistor and is known for winning two Nobel Prizes.")
    entities = mywiki.write(lm)
    assert(len(entities))
    assert(entities[0].is_written)
    assert(entities[0].markdown)

