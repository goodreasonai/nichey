from .db import Source, Entity, PrimarySourceData, ScreenshotData, Reference, obj_factory, migrate_db, DATACLASS_TO_TABLE, create_db
from .scraper import Scraper, ScrapeResponse
from .search_engine import WebLink
from .file_loaders import get_loader, FileLoader, RawChunk, TextSplitter
from .utils import get_ext_from_mime_type, get_token_estimate, get_ext_from_path, get_filename_from_path, get_mime_type_from_ext
import os
from pydantic import BaseModel
from .lm import LM, make_retrieval_prompt, LMResponse
from slugify import slugify
import traceback
import sqlite3
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import cross_origin
import re
from .logger import logger
from tqdm import tqdm
import logging
from typing import Match
from .exceptions import EntityNotExists, SourceNotExists


class Wiki():
    title: str
    topic: str
    path: str
    conn: sqlite3.Connection
    def __init__(self, topic: str, title=None, path=None, replace=False, entity_types=None):
        self.title = title
        self.topic = topic
        
        if entity_types is None:
            self.entity_types = ["person", "place", "organization", "event", "publication", "law", "product", "object", "concept"]
        else:
            self.entity_types = list(entity_types)

        if path is None:
            self.path = 'wiki.sqlite'
        else:
            # TODO: auto populate title / topic, other things
            self.path = path
        
        if replace and os.path.exists(self.path):
            os.remove(self.path)

        if not os.path.exists(self.path):
            create_db(self.path)

        conn: sqlite3.Connection = sqlite3.connect(self.path)
        conn.row_factory = obj_factory
        self.conn = conn
        self._migrate_db()
    

    def _migrate_db(self):
        # Only actually does the migration if necessary
        path, conn = migrate_db(self.path, self.conn)
        self.path = path
        self.conn = conn


    # Just pass the object with the appropriate dataclass, and it will naturally just work
    def _insert_row(self, item):
        dataclass = type(item)
        if dataclass not in DATACLASS_TO_TABLE:
            raise ValueError("Unrecognized dataclass")
        table = DATACLASS_TO_TABLE[dataclass]
        
        fields = [f for f, v in item.__dict__.items() if v is not None]
        placeholders = ", ".join(["?"] * len(fields))
        columns = ", ".join(fields)

        sql = f"""
            INSERT INTO {table} ({columns}) VALUES ({placeholders})
        """
        values = tuple(getattr(item, field) for field in fields)

        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            cursor.execute(sql, values)
            sql = f"""
                SELECT * FROM {table} WHERE `id`=?
            """
            cursor.execute(sql, (cursor.lastrowid,))
            new_row = cursor.fetchone()
            self.conn.commit()
            return new_row
        finally:
            cursor.close()

    # Updates based on ID (item.id must be set)
    def _update_row(self, item):
        dataclass = type(item)
        if dataclass not in DATACLASS_TO_TABLE:
            raise ValueError("Unrecognized dataclass")
        table = DATACLASS_TO_TABLE[dataclass]
        assert(item.id is not None)

        items = [(k, v) for k, v in item.__dict__.items() if v is not None]  # Extract and force an order
        placeholders = ", ".join([f"{k}=?" for k, _ in items])
        sql = f"""
            UPDATE {table} SET {placeholders} WHERE `id`=?
        """
        values = [v for _, v in items] + [getattr(item, 'id')]

        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            cursor.execute(sql, values)
            self.conn.commit()
        finally:
            cursor.close()

    # Select all rows with the same column values as item (where item's col value is not None)
    def _match_rows(self, item, limit: int=None, offset: int=None, order_by: list = None):
        dataclass = type(item)
        if dataclass not in DATACLASS_TO_TABLE:
            raise ValueError("Unrecognized dataclass")
        table = DATACLASS_TO_TABLE[dataclass]
        items = [(k, v) for k, v in item.__dict__.items() if v is not None]  # Extract and force an order
        filters = " AND ".join([f"{k}=?" for k, _ in items])
        values = [v for _, v in items]
        sql = f"SELECT * FROM {table}"
        
        if order_by is not None and len(order_by):
            order_by_fields = ", ".join(order_by)
            sql += f" ORDER BY {order_by_fields}"
        if len(filters):
            sql += f" WHERE {filters}"
        if limit is not None:
            sql += "\nLIMIT ?"
            values.append(limit)
        if offset is not None:
            sql += "\nOFFSET ?"
            values.append(offset)

        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            cursor.execute(sql, values)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def _match_row(self, item):
        rows = self._match_rows(item)
        if not rows or not len(rows):
            return None
        return rows[0]
    
    def _get_rows_by_ids(self, cls, ids, limit=None, offset=0):
        if cls not in DATACLASS_TO_TABLE:
            raise ValueError("Unrecognized dataclass")
        table = DATACLASS_TO_TABLE[cls]
        cursor: sqlite3.Cursor = self.conn.cursor()
        if not len(ids):
            return []
        try:
            placeholders = ','.join(['?' for _ in ids])
            sql = f"""
            SELECT * FROM {table} WHERE `id` IN ({placeholders})
            """
            cursor.execute(sql, ids)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _delete_matching_rows(self, item):
        dataclass = type(item)
        if dataclass not in DATACLASS_TO_TABLE:
            raise ValueError("Unrecognized dataclass")
        table = DATACLASS_TO_TABLE[dataclass]
        items = [(k, v) for k, v in item.__dict__.items() if v is not None]  # Extract and force an order
        filters = " AND ".join([f"{k}=?" for k, _ in items])
        values = [v for _, v in items]
        sql = f"""
            DELETE FROM {table} WHERE {filters}
        """
        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            cursor.execute(sql, values)
            self.conn.commit()
        finally:
            cursor.close()

    
    def search_sources_by_text(self, query) -> list[Source]:
        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            # See specification of an "fts5 string" here: https://www.sqlite.org/fts5.html#full_text_query_syntax
            escaped_query = query.replace('"', '""')
            quoted_query = f'"{escaped_query}"'
            sql = """
                SELECT * FROM sources
                WHERE rowid IN (SELECT source_id FROM sources_fts5 WHERE sources_fts5 MATCH ?)
            """
            cursor.execute(sql, (quoted_query,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_referenced_sources(self, entity_id, limit=1000, offset=0) -> list[Source]:
        ref = Reference(entity_id=entity_id)
        refs: list[Reference] = self._match_rows(ref, limit=limit, offset=offset)
        sources = self._get_rows_by_ids(Source, [ref.source_id for ref in refs])
        return sources
    
    def add_reference(self, entity_id, source_id):
        ent = self._match_row(Entity(id=entity_id))
        if not ent:
            raise EntityNotExists(f"Couldn't find entity with ID {entity_id}; make sure you're passing the ID and not the slug!")
        src = self.get_source_by_id(source_id)
        if not src:
            raise SourceNotExists(f"Couldn't find source with id {source_id}")
        ref = Reference(entity_id=entity_id, source_id=source_id)
        new_ref: Reference = self._insert_row(ref)
        return new_ref

    def get_all_sources(self, limit=5000, offset=0) -> list[Source]:
        return self._match_rows(Source(), limit=limit, offset=offset, order_by=['title'])

    def get_all_entities(self, limit=5000, offset=0) -> list[Entity]:
        return self._match_rows(Entity(), limit=limit, offset=offset, order_by=['title'])

    def get_entity_by_slug(self, slug) -> Entity:
        return self._match_row(Entity(slug=slug))
    
    def get_entities_by_type(self, type) -> list[Entity]:
        return self._match_rows(Entity(type=type))
    
    def get_source_by_id(self, id) -> Source:
        return self._match_row(Source(id=id))
    
    def delete_source_by_id(self, id) -> None:
        self._delete_matching_rows(Source(id=id))

    def delete_entity_by_slug(self, slug) -> None:
        self._delete_matching_rows(Entity(slug=slug))

    def add_entity(self, title: str, type: str=None, desc: str=None, markdown: str=None) -> Entity:
        slug = slugify(title)
        is_written = markdown is not None and len(markdown)
        entity = Entity(slug=slug, title=title, type=type, desc=desc, markdown=markdown, is_written=is_written)
        entity = self._insert_row(entity)
        return entity
    
    def update_entity_by_slug(self, slug, title: str = None, type: str = None, desc: str = None, markdown: str=None) -> None:
        existing = self.get_entity_by_slug(slug)
        is_written = existing.is_written or (markdown is not None and len(markdown))
        entity = Entity(
            slug=slug,
            title=title,
            type=type,
            desc=desc,
            markdown=markdown,
            is_written=is_written,
            id=existing.id
        )
        self._update_row(entity)  # updates by id, so need to retrieve ID with the get call first

    def update_source_by_id(self, id, title: str = None, author: str = None, desc: str = None, url: str=None, snippet: str = None, query: str = None) -> None:
        entity = Source(
            id=id,
            title=title,
            desc=desc,
            author=author,
            url=url,
            snippet=snippet,
            query=query
        )
        self._update_row(entity)
    
    def add_source(self, title: str, text: str, author: str=None, desc: str=None, url: str=None, snippet: str=None, query: str=None, search_engine: str=None, are_entities_extracted=False) -> Source:
        source = Source(title=title, text=text, author=author, desc=desc, url=url, snippet=snippet, query=query, search_engine=search_engine, are_entities_extracted=are_entities_extracted)
        source = self._insert_row(source)
        return source

    # TODO: allow breaking up by pages when supported
    def load_local_sources(self, paths: list[str]) -> list[Source]:
        for i in tqdm(range(len(paths)), desc="Loading", total=len(paths)):
            path = paths[i]
            ext = get_ext_from_path(path)
            loader = get_loader(ext, path)
            if not loader:
                logger.warning(f"Couldn't process {path}; skipping.")
            text = ""
            for raw_chunk in loader.load_and_split(TextSplitter()):
                raw_chunk: RawChunk
                text += raw_chunk.page_content
            src: Source = self.add_source(
                title=get_filename_from_path(path),
                text=text
            )

            data = None
            with open(path, 'rb') as fhand:
                data = fhand.read()

            psd = PrimarySourceData(
                source_id=src.id,
                mimetype=get_mime_type_from_ext(ext),
                data=data
            )
            self._insert_row(psd)
        

    # Scrapes and stores info in the db
    def scrape_web_results(self, scraper: Scraper, results: list[WebLink], max_n=None) -> list[tuple[WebLink, Source | None]]:
        scraped = []
        total = min(len(results), max_n) if max_n is not None else len(results)
        for i in tqdm(range(total), desc="Scraping", total=total):
            res = results[i]
            new_source = None
            existing = self._match_rows(Source(url=res.url))
            if existing and len(existing):
                # Duplicate!
                logger.info(f"Skipping duplicate URL {res.url}")
            else:
                resp: ScrapeResponse = scraper.scrape(res.url)
                if not resp.success:
                    logger.warning(f"Failed to scrape {res.url}; moving on.")
                else:
                    with resp.consume_data() as path:
                        with resp.consume_screenshots() as (ss_paths, ss_mimetypes):
                            ext = get_ext_from_mime_type(resp.metadata.content_type)
                            loader: FileLoader = get_loader(ext, path)
                            if not loader:
                                logger.warning(f"Filetype '{resp.metadata.content_type}' cannot be parsed; moving along.")
                            else:
                                txt = ""
                                splitter = TextSplitter()
                                for chunk in loader.load_and_split(splitter):
                                    chunk: RawChunk
                                    txt += chunk.page_content

                                with open(path, 'rb') as f:
                                    file_data = f.read()

                                new_source = Source(
                                    title=resp.metadata.title,
                                    text=txt,
                                    url=resp.url,
                                    snippet=res.snippet,
                                    query=res.query,
                                    search_engine=res.search_engine
                                )
                                new_source: Source = self._insert_row(new_source)

                                primary_data = PrimarySourceData(
                                    mimetype=resp.metadata.content_type,
                                    data=file_data,
                                    source_id=new_source.id,
                                )
                                self._insert_row(primary_data)

                                ss_paths: list[str]
                                ss_mimetypes: list[str]
                                for i, (ss_path, ss_mimetype) in enumerate(zip(ss_paths, ss_mimetypes)):
                                    with open(ss_path, 'rb') as f:
                                        ss_data = f.read()
                                    
                                    screenshot = ScreenshotData(
                                        mimetype=ss_mimetype,
                                        data=ss_data,
                                        source_id=new_source.id,
                                        place=i
                                    )
                                    self._insert_row(screenshot)
            
            scraped.append((res, new_source))
        return scraped
                    

    def make_entities(self, lm: LM, max_sources=None) -> list[tuple[Source, list[Entity]]]:
        # Go through sources
        sources = self._match_rows(Source(are_entities_extracted=False))
        if not len(sources):
            logger.warning("No sources found to make entities from.")
        
        total = min(len(sources), max_sources) if max_sources is not None else len(sources)
        processed = []
        for i in tqdm(range(total), total=total, desc="Extracting"):
            src: Source = sources[i]
            made_entities = []
            try:
                text = src.text
                if text:
                    not_entities = ["Countries", "Nouns unrelated to the research topic", "Very common nouns or words", "Well-known cities not especially significant to the research topic"]
                    class EntityData(BaseModel):
                        type: str
                        title: str
                        desc: str

                    class Entities(BaseModel):
                        entities: list[EntityData]

                    intro = "You are tasked with extracting relevant entities from the given source material into JSON. Here is the text extracted from the source material:"
                    prompt_src_text = make_retrieval_prompt(lm, [text])
                    wiki = "Each entity will become a custom Wiki article that the user is constructing based on his research topic."
                    type_req = f"The entities/pages can be the following types: {', '.join(self.entity_types)}"
                    neg_req = f"You should not make entities for the following categories, which don't count: {', '.join(not_entities)}"
                    rel_req = "The user will provide the research topic. THE ENTITIES YOU EXTRACT MUST BE RELEVANT TO THE USER'S RESEARCH GOALS."
                    format_req = "Use the appropriate JSON schema. Here is an example for an extraction for research involving the history of Bell Labs. In this case, we're assuming that the source material mentioned John Bardeen."
                    example = '{"entities": [{"type": "person", "title": "John Bardeen", "desc": "John Bardeen, along with Walter Brattain and Bill Shockley, co-invented the transistor during his time as a physicist at Bell Labs."}, ...]}'
                    example_cont = "For this example, you may also want to have included the transistor (object), The Invention of the Transistor (event), Walter Brattain (person), and Bill Shockley (person), assuming that all of these were actually mentioned in the source material."
                    conclusion = "Now, read the user's research topic and extract the relevant entites from the source given above. Include only entities that were mentioned in the source material. Try to limit the number of entities you extract to only those most relevant (there may be as few as 0 or at most 10)."
                    system_prompt = "\n\n".join([intro, prompt_src_text, wiki, type_req, neg_req, rel_req, format_req, example, example_cont, conclusion])
                    user_prompt = self.topic

                    logger.debug(f"Make Entity User Prompt Length: {get_token_estimate(user_prompt)}")
                    logger.debug(f"Make Entity System Prompt Length: {get_token_estimate(system_prompt)}")

                    resp: LMResponse = lm.run(user_prompt, system_prompt, [], json_schema=Entities)
                    entities: Entities = resp.parsed

                    for ent in entities.entities:
                        ent: EntityData

                        if ent.type not in self.entity_types:
                            logger.warning(f"Extracted type '{ent.type}' not recognized (title was '{ent.title}', source was '{src.title}')")

                        slug = slugify(ent.title, max_length=255)  # 255 is the max length of the slug text in the database... may want to standardize this somewhere.
                        # Check for duplicate
                        existing = self.get_entity_by_slug(slug)
                        if existing:
                            logger.debug(f"Duplicate entity found for {slug}; not re-adding.")
                            new_reference = Reference(
                                source_id=src.id,
                                entity_id=existing.id
                            )
                            self._insert_row(new_reference)
                        else:
                            new_entity: Entity = self.add_entity(ent.title, type=ent.type, desc=ent.desc)
                            made_entities.append(new_entity)
                            new_reference = Reference(
                                source_id=src.id,
                                entity_id=new_entity.id
                            )
                            self._insert_row(new_reference)
                src.are_entities_extracted = True
                self._update_row(src)
                processed.append((src, made_entities))

            except:
                logger.debug(traceback.format_exc())
                logger.warning(f"An exception occurred trying to parse entities of source with id {src.id}. Moving on.")

        return processed


    def heal_markdown(self, markdown: str) -> str:
        """
        Tries to fix various malformed or inconsistent markdown link patterns to match:
        - [[slug | Entity Title]]
        - [[@ID]] for sources
        Removes or downgrades links if corresponding entity/source doesn't exist.
        """

        # --- Helper functions ---
        def is_numeric(s: str) -> bool:
            return s.isdigit()

        def source_exists(num_str: str) -> bool:
            src = self.get_source_by_id(num_str)
            return src is not None

        def entity_exists(slug_or_title: str) -> bool:
            slug_or_title = slugify(slug_or_title)
            entity = self.get_entity_by_slug(slug_or_title)
            return entity is not None

        # For whatever reason, remove weird bracket lookalikes
        markdown = markdown.replace("【", "[").replace("】", "]")

        # ------------------------------------------------------------------------
        # 1) Transform [text](link) => [[link | text]] or [[@ID]]
        # ------------------------------------------------------------------------
        def replace_square_paren(m: Match) -> str:
            text = m.group(1).strip()
            link = m.group(2).strip()

            # Case: [1](1) => [[@1]]
            if is_numeric(text) and is_numeric(link) and text == link:
                if source_exists(text):
                    return f"[[@{text}]]"
                else:
                    return text

            # Case: [1](foo) => possibly [[@1]] if 1 is a source
            if is_numeric(text):
                if source_exists(text):
                    return f"[[@{text}]]"
                else:
                    return text

            # Otherwise treat link as an entity slug
            if entity_exists(link):
                return f"[[{link} | {text}]]"
            else:
                # Link doesn't exist -> keep just the text
                return text

        pattern_square_paren = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        markdown = pattern_square_paren.sub(replace_square_paren, markdown)
        
        "[[@19]]"
        # ------------------------------------------------------------------------
        # 2) Transform [[text]](link) => [[link | text]] or [[@ID]] 
        # ------------------------------------------------------------------------
        def replace_double_bracket_paren(m: Match) -> str:
            text = m.group(1).strip()
            link = m.group(2).strip()

            # e.g. [[1]](1) => [[@1]]
            if is_numeric(text) and is_numeric(link) and text == link:
                if source_exists(text):
                    return f"[[@{text}]]"
                else:
                    return text

            # Otherwise treat link as an entity slug
            if entity_exists(link):
                return f"[[{link} | {text}]]"
            else:
                return text

        pattern_double_bracket_paren = re.compile(r'\[\[([^\]]+)\]\]\(([^\)]+)\)')
        markdown = pattern_double_bracket_paren.sub(replace_double_bracket_paren, markdown)

        # ------------------------------------------------------------------------
        # 3) Transform double-bracket references [[text]] 
        #    - Single references, or multiple references like [[@1], [@2], [@3]]
        # ------------------------------------------------------------------------

        # (a) Helper to handle a single reference
        def handle_single_reference(txt: str) -> str:
            txt = txt.strip()

            # Case: [[slug | Title]]
            if '|' in txt:
                left, right = [x.strip() for x in txt.split('|', maxsplit=1)]
                if is_numeric(left):
                    if source_exists(left):
                        return f"[[@{left}]]"
                    return right
                if entity_exists(left):
                    return f"[[{left} | {right}]]"
                return right  # fallback

            # Case: numeric => [[@N]] if source
            if is_numeric(txt):
                if source_exists(txt):
                    return f"[[@{txt}]]"
                else:
                    return ""

            # Case: @number => treat as source if it exists
            if len(txt) > 1 and txt[0] == '@':
                num = txt[1:]
                if source_exists(num):
                    return f"[[{txt}]]"
                else:
                    return ""

            # Otherwise treat as entity reference
            if entity_exists(txt):
                return f"[[{txt}]]"
            return txt

        # (b) Detect if the text is a comma-separated list of references (e.g. "@1], [@2]")
        # NEW: We'll use a pattern that matches e.g. `[?@?digits]` repeated with commas.
        # If it doesn't match, we treat it as a single reference.
        pattern_multiple_refs = re.compile(
            r'^\s*(?:\[?\s*@?\d+\s*\]?)(?:\s*,\s*\[?\s*@?\d+\s*\]?)+\s*$'
        )

        # (c) Replace function for the double brackets
        def replace_double_bracket(m: Match) -> str:
            text = m.group(1)  # everything inside [[...]]
            text_stripped = text.strip()

            # If it clearly looks like multiple references, split them up.
            if pattern_multiple_refs.match(text_stripped):
                parts = re.split(r'\s*,\s*', text_stripped)
                results = []
                for part in parts:
                    # remove surrounding brackets from each chunk if present
                    part = part.strip('[] ')
                    results.append(handle_single_reference(part))
                return "".join(results)

            # Otherwise, handle it as a single reference or entity
            return handle_single_reference(text_stripped)

        # Use a pattern that captures everything up to the next "]]"
        pattern_double_bracket = re.compile(r'\[\[(.*?)\]\]')
        markdown = pattern_double_bracket.sub(replace_double_bracket, markdown)

        # ------------------------------------------------------------------------
        # 4) Transform single-bracket sources [@2] 
        # ------------------------------------------------------------------------
        def replace_single_bracket_reference(m: Match) -> str:
            inside = m.group(1).strip()  # e.g. "@2" or "42"
            # If it starts with @, parse the numeric part
            if inside.startswith('@'):
                num_str = inside[1:]
                if is_numeric(num_str) and source_exists(num_str):
                    return f"[[{inside}]]"  # e.g. [[@2]]
                else:
                    return ""  # remove
            else:
                # If it's numeric, try to convert to [@N]
                if is_numeric(inside) and source_exists(inside):
                    return f"[[@{inside}]]"
                else:
                    return f"[{inside}]"  # keep the same

        # Pattern matches [@123] or [123] but not [anything else] and not [[2]]
        # We exclude ! so we don't catch image syntax ![...]
        pattern_single_bracket_ref = re.compile(r'(?<!\!)\[(?!\[)(@?\d+)\](?!\])')
        markdown = pattern_single_bracket_ref.sub(replace_single_bracket_reference, markdown)

        return markdown


    def write_article(self, lm: LM, entity_slug: str) -> Entity | None:

        all_entity_text = ""
        
        ent = self.get_entity_by_slug(entity_slug)
        if not ent:
            raise EntityNotExists(f"Cannot write an article for entity with slug '{entity_slug}' since it doesn't exist.")
        
        all_entities: list[Entity] = self.get_all_entities()
        all_entities_info = [(x.slug, x.title) for x in all_entities]
        all_entity_text = "\n".join([f"[[{x[0]} | {x[1]}]]" for x in all_entities_info])

        matching_sources = self.search_sources_by_text(ent.title)
        direct_sources = self.get_referenced_sources(entity_id=ent.id)

        logger.debug(f"Matching Sources Found: {len(matching_sources)}")
        logger.debug(f"Direct Sources Found: {len(direct_sources)}")

        # Combine the results of both queries, ensuring no duplicates
        matches_ids = {match.id for match in matching_sources}
        combined: list[Source] = matching_sources[:]
        for src in direct_sources:
            if src.id not in matches_ids:
                combined.append(src)

        logger.debug(f"Combined Sources Found: {len(combined)}")

        # Now 'sources' contains all the Source objects associated with the matched SourcePrimaryData
        if not len(combined):
            logger.warning(f"No matching sources found for entity {ent.title}; moving on.")
        else:
            try:
                intro = "You are tasked with writing a full wiki entry for some entity. This wiki is not a general wiki; it is meant to fulfill the research goals set by the user. The user will specify the page you are writing. You **must** write in well-formatted markdown."
                links = "You can specify a link to another wiki entry in Wikilink format like: [[slug | Custom Text]] or [[ Title ]]. Whenever you mention some other entity, you should probably use a link. Here are all the entries in the wiki for your reference:"
                all_entity_text = all_entity_text
                source_instruct = "Below are sources from which you can draw material for your wiki entry. **Use only these sources for the information in your entry. You may not draw from any other outside information you may have.** You'll use the sources' ID numbers to write your citations."
                source_text = make_retrieval_prompt(lm, [data.text for data in combined], prefixes=[f"<START OF SOURCE WITH ID={data.id}>\n{data.title} {'| URL: ' + data.url if data.url else ''}" for data in combined], suffixes=[f"</END OF SOURCE WITH ID={data.id}>" for data in combined])
                references = "In order to cite a source using a footnote, use the syntax '[[@SOURCE_ID]]', with the @ sign. For example, a footnote to source with ID 15 would be [[@15]]. WHENEVER YOU CITE A SOURCE (as opposed to another article) YOU MUST USE THE AT (@) SIGN. **Please include inline references whenever possible!** But do not write them in a separate section."
                
                example_instruct = "Here is an example of what some content might look like in a hypothetical page:"
                example = "## Early Victories\nAmong Napoleon's most important early victories was at the [[Siege of Toulon]], which took place during the [[federalist revolts]]. Napoleon instantly won fame when his plan was credited as being the decisive factor in the battle.[[@14]] He would later parlay his fame into commanding an army to lead an invasion of Italy.[[@19]][[@3]]"

                conclusion = "Now the user will specify the actual wiki page you are tasked with writing."
                system = "\n\n".join([intro, links, all_entity_text, source_instruct, source_text, references, example_instruct, example, conclusion])

                user_prompt_intro = f"You are writing the wiki entry for {ent.title}."
                user_prompt_disambiguation = f"A brief description of this entity for disambiguation: {ent.desc}"
                user_prompt_topic = f"The goal of the wiki is to fulfill this research goal: {self.topic}"
                prompt = "\n".join([user_prompt_intro, user_prompt_disambiguation, user_prompt_topic])
                
                logger.debug(f"Write System Prompt:\n\n{system}")
                logger.debug(f"Write User Prompt:\n\n{prompt}")
                logger.debug(f"Write User Prompt Length: {get_token_estimate(prompt)}")
                logger.debug(f"Write System Prompt Length: {get_token_estimate(system)}")

                lm_resp: LMResponse = lm.run(prompt, system, [])

                new_markdown = lm_resp.text

                logger.debug(f"Raw Markdown:\n\n{new_markdown}")
                # Run a fix of common formatting issues
                new_markdown = self.heal_markdown(new_markdown)
                logger.debug(f"Fixed Markdown:\n\n{new_markdown}")

                ent.markdown = new_markdown
                ent.is_written = True
                self._update_row(ent)
                return ent

            except:
                logger.debug(traceback.format_exc())
                logger.error(f"An exception occurred trying to write entry for {ent.slug}. Moving on.")


    def write_articles(self, lm: LM, max_n=None, rewrite=False) -> list[Entity]:
        all_entities: list[Entity] = self.get_all_entities()
        if rewrite:
            entities = list(all_entities)
        else:
            entities = self._match_rows(Entity(is_written=False))
        written = []
        total = min(len(entities), max_n) if max_n is not None else len(entities)
        for i in tqdm(range(total), desc="Writing", disable=logger.level > logging.INFO):
            ent: Entity = entities[i]
            new_entity = self.write_article(lm, ent.slug)
            if new_entity:
                written.append(new_entity)

        return written


    def deduplicate_entities(self, lm: LM, max_groups=None, group_size=100) -> int:
        all_entities = self.get_all_entities()
        # Bunch them 100 at a time (give or take)
        groups: list[list[Entity]] = []
        i = 0
        while True:
            new_group = all_entities[i:i+group_size]
            if len(new_group) < 3:
                groups[-1].extend(new_group)
                break
            elif len(new_group):
                groups.append(new_group)
            else:
                break
            i += group_size

        total = min(len(groups), max_groups) if max_groups is not None else len(groups)
        n = 0
        for i in tqdm(range(total), desc="Culling", disable=logger.level > logging.INFO):
            this_group = groups[i]
            system = "You are tasked with deduplicating a group of entity titles. Given a list of titles, return a well-formatted JSON object consisting of deduplicated titles. You should combine titles that refer to the same thing or concept. If a title is the plural of another, combine them, leaving only the singular form. You must give a complete list of all the titles that remain. The user will provide the list of titles."
            user = "\n".join([x.title for x in this_group])

            class Deduplicated(BaseModel):
                deduplicated_titles: list[str]

            resp: LMResponse = lm.run(user, system, [], json_schema=Deduplicated)
            parsed: Deduplicated = resp.parsed
            deduped_table = {slugify(k): True for k in parsed.deduplicated_titles}
            for ent in this_group:
                ent: Entity
                if ent.slug not in deduped_table:
                    self.delete_entity_by_slug(ent.slug)
                    n += 1
        return n


    def export(self, dir="output", remove_cross_refs=True, remove_source_refs=True):
        all_written_entities: list[Entity] = self._match_rows(Entity(is_written=True))
        if not os.path.exists(dir):
            os.mkdir(dir)
        for ent in all_written_entities:
            fname = f"{ent.slug}.md"
            with open(os.path.join(dir, fname), 'w') as fhand:
                markdown = ent.markdown

                # Remove references / links if desired
                pattern = r'\[\[\s*(.*?)\s*\]\]'
                def replacer(match):
                    content = match.group(1).strip()
                    if content.startswith('@'):  # Case 1: References like [[ @25 ]]
                        return '' if remove_source_refs else f'[[{content}]]'
                    if '|' in content:  # Case 2: Cross links with [[ | ]] form
                        if remove_cross_refs:
                            # Keep only the right side (alias).
                            parts = content.split('|', 1)
                            return parts[1].strip()
                        return f'[[{content}]]'
                    else:
                        return content if remove_cross_refs else f'[[{content}]]'

                markdown = re.sub(pattern, replacer, markdown)

                fhand.write(markdown)


    def serve(self, port=5000):
        app = Flask(__name__, static_folder='static')

        # Route to serve static files
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_static_files(path):
            if path != "" and not os.path.splitext(path)[1]:
                path += '.html'
            if path != "" and os.path.exists(app.static_folder + '/' + path):
                return send_from_directory(app.static_folder, path)
            else:
                return send_from_directory(app.static_folder, 'index.html')

        @app.route('/api/index', methods=('GET',))
        @cross_origin()
        def api_index():
            entities = self.get_all_entities()
            data = {
                'entities': [{
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'is_written': ent.is_written
                } for ent in entities]
            }
            return jsonify(data)
        
        @app.route('/api/sources', methods=('GET',))
        @cross_origin()
        def api_sources():
            sources = self.get_all_sources()
            data = {
                'sources': [{
                    'title': src.title,
                    'id': src.id,
                } for src in sources]
            }
            return jsonify(data)
        
        @app.route('/api/page', methods=('GET',))
        @cross_origin()
        def api_page():
            entity_slug = request.args.get('slug')
            entity_slug = slugify(entity_slug, max_length=255)
            ent = self.get_entity_by_slug(entity_slug)
            if not ent: 
                return jsonify({'message': f'Entity with slug {entity_slug} not found'}), 404
            data = {
                'entity': {
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'markdown': ent.markdown
                }
            }
            return jsonify(data)
        
        @app.route('/api/source', methods=('GET',))
        @cross_origin()
        def api_source():
            source_id = request.args.get('id')
            src = self.get_source_by_id(id=source_id)
            if not src:
                return jsonify({'message': f'Source with id {source_id} not found'}), 404
            data = {
                'source': {
                    'title': src.title,
                    'id': src.id,
                    'url': src.url,
                    'search_engine': src.search_engine,
                    'query': src.query,
                    'snippet': src.snippet
                }
            }
            return jsonify(data)
        
        @app.route('/api/update-entity', methods=('POST',))
        @cross_origin()
        def api_update_entity():
            slug = request.json.get('slug')
            ent = self.get_entity_by_slug(slug=slug)
            if not ent:
                return jsonify({'message': f'Entity with slug {slug} not found'}), 404
            title = request.json.get('title')
            type = request.json.get('type')
            desc = request.json.get('desc')
            markdown = request.json.get('markdown')
            self.update_entity_by_slug(
                slug,
                title=title,
                type=type,
                desc=desc,
                markdown=markdown
            )
            return jsonify({'message': 'success'})
        
        @app.route('/api/delete-entity', methods=('POST',))
        @cross_origin()
        def api_delete_entity():
            slug = request.json.get('slug')
            ent = self.get_entity_by_slug(slug=slug)
            if not ent:
                return jsonify({'message': f'Entity with slug {slug} not found'}), 404
            self.delete_entity_by_slug(slug)
            return jsonify({'message': 'success'})
        
        @app.route('/api/delete-source', methods=('POST',))
        @cross_origin()
        def api_delete_source():
            id = request.json.get('id')
            src = self.get_source_by_id(id=id)
            if not src:
                return jsonify({'message': f'Source with id {id} not found'}), 404
            self.delete_source_by_id(src.id)
            return jsonify({'message': 'success'})
        
        app.run(port=port, threaded=False)
