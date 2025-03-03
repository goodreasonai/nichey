import nichey as wiki
from .utils import get_tmp_path
import os
from .lm import get_lm
from slugify import slugify
import shutil


def test_entities():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        title = "Tom Seaver"
        type = "person"
        mywiki.add_entity(title=title, type=type)
        ents = mywiki.get_entities_by_type(type)
        assert(len(ents) == 1)
        entity = ents[0]
        assert(entity.title == title)
        assert(entity.type == type)

        desc = "A 3 time Cy Young award winning pitcher"
        mywiki.update_entity_by_slug(entity.slug, desc=desc)
        entity = mywiki.get_entity_by_slug(entity.slug)
        assert(entity.desc == desc)

        mywiki.delete_entity_by_slug(entity.slug)
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
        src = sources[0]
        assert(src.title == title)
        assert(src.author == author)

        desc = "A great work of existentialism"
        mywiki.update_source_by_id(id=src.id, desc=desc)
        src = mywiki.get_source_by_id(src.id)
        assert(src.desc == desc)

        mywiki.delete_source_by_id(src.id)
        source = mywiki.get_source_by_id(id=src.id)
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
        lm = get_lm()
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
    try:
        results = [wiki.WebLink(url="https://goodreason.ai")]
        scraper = wiki.RequestsScraper()
        mywiki.scrape_web_results(scraper, results)

        sources = mywiki.get_all_sources()
        assert(len(sources) == 1)
        sources = mywiki.search_sources_by_text("Gordon Kamer")
        assert(len(sources) == 1)

        # Make sure duplicates aren't scraped
        mywiki.scrape_web_results(scraper, results)
        sources = mywiki.get_all_sources()
        assert(len(sources) == 1)
    finally:
        os.remove(mywiki.path)


def test_write_entities():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="I'm interested the history of technology of the middle of the 20th century.")
    lm = get_lm()
    try:
        url = "https://en.wikipedia.org/wiki/John_Bardeen"
        scraper = wiki.RequestsScraper()
        results = [wiki.WebLink(url=url)]
        mywiki.scrape_web_results(scraper, results)
        sources = mywiki.search_sources_by_text("John Bardeen")
        assert(len(sources))

        # Rather than extract (which is not being tested here, just skip to write)
        mywiki.add_entity(title="John Bardeen", type="person", desc="John Bardeen was a co-inventor of the transistor and is known for winning two Nobel Prizes.")
        entities = mywiki.write_articles(lm)
        assert(len(entities))
        assert(entities[0].is_written)
        assert(entities[0].markdown)
    finally:
        os.remove(mywiki.path)


def test_local_sources():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        paths = ['America Against America.pdf']
        mywiki.load_local_sources(paths)
        results = mywiki.search_sources_by_text("America Against America")
        assert(len(results) == 1)
        assert(results[0].title == 'America Against America.pdf')
        assert(len(results[0].text) > 1000)
    finally:
        os.remove(mywiki.path)


def test_split_pages():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        # Assuming that America Against America is 36 pages
        paths = ['America Against America.pdf']
        mywiki.load_local_sources(paths, split_pages=5)
        results = mywiki.search_sources_by_text("America Against America")
        assert(len(results) == 8)
    finally:
        os.remove(mywiki.path)


def test_heal():
    """
    Would like to:

    - Transform [Bad](link) to [[link | Bad]]
    - Transform [[Bad]](link) to [[link | Bad]]
    - Transform [1](1) to [[@1]]
    - Transform [[1]] to [[@1]]
    - Transform [1] to [[@1]]
    - Transform [[1 | source]] to [[@1]]
    - Transform [[2], [@3]] to [[@2]][[@3]]
    - Transform [@1] to [[@1]]
    - Ensure all internal links go to an existing entity
    - Ensure all source references go to an existing source

    """
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        existing_ent = mywiki.add_entity(
            title="Brunswick School",
            desc="A boys school in Greenwich, CT",
            type="organization"
        )
        assert(existing_ent.slug == 'brunswick-school')

        existing_src: wiki.Source = mywiki.add_source(
            title="GEORGE CARMICHAEL, HEADED DAY SCHOOL",
            text="WOLFEBORO, N. H., March 21—George E. Carmichael, founder of the Brunswick School, a country day school for boys in Greenwich, Conn., died at his home here yesterday. He was 88 years old.",
            author="New York Times"
        )
        assert(existing_src.id == 1)

        existing_src_2: wiki.Source = mywiki.add_source(
            title="Brunswick School Mission and History",
            text="In the words of our founder, George Carmichael, 'Brunswick School has been ably and generously preparing boys for life since 1902.'",
            url="https://admissions.brunswickschool.org/about/mission-history/"
        )
        assert(existing_src_2.id == 2)

        new_ent = mywiki.add_entity(
            title="George Carmichael",
            type="person",
            desc="Founder of Brunswick School"
        )
        assert(new_ent.slug == 'george-carmichael')

        # We'll ignore the fact that this string will technically have erroneous tabs
        bad_markdown = """
            # George Carmichael
            George Carmichael founded [[Brunswick School]] in 1902 in [[Greenwich, CT]].[1](1)
            See: [[ founding-of-wick | Founding of Brunswick School ]].
            The [[brunswick-school | school]] was founded as an all boys version of Greenwich Academy, which would go on to admit only girls.[@1][2][3]
            [Brunswick's](brunswick-school) motto is "Courage, Honor, Truth", which was selected by a vote of students shortly after the school's founding.[[@1], [@2]]
            [[Carmichael]](george-carmichael) graduated from Bowdoin College in 1897.[[@1]].
            He was also active in Greenwich Civic life.[[1]][[3]]
            Carmichael died aged 88.[[1 | source]]
            [See also: [[Bowdoin College]]]
        """
        good_markdown = """
            # George Carmichael
            George Carmichael founded [[Brunswick School]] in 1902 in Greenwich, CT.[[@1]]
            See: Founding of Brunswick School.
            The [[brunswick-school | school]] was founded as an all boys version of Greenwich Academy, which would go on to admit only girls.[[@1]][[@2]][3]
            [[brunswick-school | Brunswick's]] motto is "Courage, Honor, Truth", which was selected by a vote of students shortly after the school's founding.[[@1]][[@2]]
            [[george-carmichael | Carmichael]] graduated from Bowdoin College in 1897.[[@1]].
            He was also active in Greenwich Civic life.[[@1]]
            Carmichael died aged 88.[[@1]]
            [See also: Bowdoin College]
        """
        new_markdown = mywiki.heal_markdown(bad_markdown)
        assert(new_markdown == good_markdown)
    finally:
        os.remove(mywiki.path)


def test_deduplicate():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    try:
        mywiki.add_entity("Code Napoleon")
        mywiki.add_entity("Color")
        mywiki.add_entity("Colour")
        mywiki.add_entity("Electronics")
        mywiki.add_entity("Electricity and Magnetism")
        mywiki.add_entity("Greenwich, CT")
        mywiki.add_entity("Greenwich Mean Time")
        mywiki.add_entity("Greenwich Mean Time (GMT)")
        mywiki.add_entity("New York")
        mywiki.add_entity("The Napoleonic Code")
        mywiki.add_entity("The Napoleonic Code (Code Napoleon)")
        mywiki.add_entity("York, England")

        mywiki.deduplicate_entities(lm=get_lm(), group_size=5)

        code_napoleon = bool(mywiki.get_entity_by_slug(slugify("Code Napoleon")))
        color = bool(mywiki.get_entity_by_slug(slugify("Color")))
        colour = bool(mywiki.get_entity_by_slug(slugify("Colour")))
        electronics = bool(mywiki.get_entity_by_slug(slugify("Electronics")))
        electricity_and_magnetism = bool(mywiki.get_entity_by_slug(slugify("Electricity and Magnetism")))
        greenwich_ct = bool(mywiki.get_entity_by_slug(slugify("Greenwich, CT")))
        greenwich_mean_time = bool(mywiki.get_entity_by_slug(slugify("Greenwich Mean Time")))
        greenwich_mean_time_gmt = bool(mywiki.get_entity_by_slug(slugify("Greenwich Mean Time (GMT)")))
        new_york = bool(mywiki.get_entity_by_slug(slugify("New York")))
        the_napoleonic_code = bool(mywiki.get_entity_by_slug(slugify("The Napoleonic Code")))
        the_napoleonic_code_code_napoleon = bool(mywiki.get_entity_by_slug(slugify("The Napoleonic Code (Code Napoleon)")))
        york_england = bool(mywiki.get_entity_by_slug(slugify("York, England")))

        assert(code_napoleon)  # Because of grouping, this should still exist
        assert(sum([the_napoleonic_code, the_napoleonic_code_code_napoleon]) == 1)
        assert(sum([color, colour]) == 1)
        assert(electronics)
        assert(electricity_and_magnetism)
        assert(greenwich_ct)
        assert(sum([greenwich_mean_time_gmt, greenwich_mean_time]) == 1)
        assert(new_york)
        assert(york_england)

    finally:
        os.remove(mywiki.path)


def test_export():
    mywiki = wiki.Wiki(path=get_tmp_path(), topic="")
    output_dir = get_tmp_path()
    try:
        title = "My Entity"
        markdown = "Hello!"
        mywiki.add_entity(title, markdown=markdown)
        ent = mywiki.get_entity_by_slug(slug=slugify(title))
        assert(ent)
        assert(ent.is_written)
        mywiki.export(dir=output_dir)
        path = os.path.join(output_dir, f"{slugify(title)}.md")
        with open(path, "r") as fhand:
            assert(markdown == fhand.read())
    finally:
        os.remove(mywiki.path)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
