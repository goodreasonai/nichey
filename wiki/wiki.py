from .db import Source, Entity, PrimarySourceData, ScreenshotData, ENTITY_TYPES, Reference, obj_factory, migrate_db, DATACLASS_TO_TABLE, create_db
from .scraper import Scraper, ScrapeResponse
from .search_engine import WebLink
from .file_loaders import get_loader, FileLoader, RawChunk, TextSplitter
from .utils import get_ext_from_mime_type, get_token_estimate
import os
import sys
from pydantic import BaseModel
from .lm import LM, make_retrieval_prompt, LMResponse
from slugify import slugify
import traceback
from typing import Generator, Tuple, List
import sqlite3
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import cross_origin
import re
from .logger import logger
from tqdm import tqdm
import logging


class Wiki():
    title: str
    topic: str
    path: str
    conn: sqlite3.Connection
    def __init__(self, title=None, topic=None, path=None, replace=False):
        self.title = title
        self.topic = topic
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
    
    def _get_rows_by_id(self, cls, ids, limit=None, offset=0):
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
        sources = self._get_rows_by_id(Source, [ref.source_id for ref in refs])
        return sources

    def get_all_sources(self, limit=5000, offset=0) -> list[Source]:
        return self._match_rows(Source(), limit=limit, offset=offset, order_by=['title'])

    def get_all_entities(self, limit=5000, offset=0) -> list[Entity]:
        return self._match_rows(Entity(), limit=limit, offset=offset, order_by=['title'])

    def get_entity_by_slug(self, slug) -> Entity:
        return self._match_row(Entity(slug=slug))
    
    def get_source_by_id(self, id) -> Source:
        return self._match_row(Source(id=id))

    # Scrapes and stores info in the db
    def scrape_web_results(self, scraper: Scraper, results: list[WebLink], max_n=None) -> list[WebLink]:
        scraped = []
        total = min(len(results), max_n) if max_n is not None else len(results)
        for i in tqdm(range(total), desc="Scraping", total=total):
            res = results[i]
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
            
            scraped.append(res)
        return scraped
                    

    def make_entities(self, lm: LM) -> list[tuple[Source, list[Entity]]]:
        # Go through sources
        sources = self._match_rows(Source(are_entities_extracted=False))
        if not len(sources):
            logger.warning("No sources found to make entities from.")
        
        total = len(sources)
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
                    type_req = f"The entities/pages can be the following types: {', '.join(ENTITY_TYPES)}"
                    neg_req = f"You should not make entities for the following categories, which don't count: {', '.join(not_entities)}"
                    rel_req = "The user will provide the research topic. THE ENTITIES YOU EXTRACT MUST BE RELEVANT TO THE USER'S RESEARCH GOALS."
                    format_req = "Use the appropriate JSON schema. Here is an example for an extraction for research involving the history of Bell Labs. In this case, we're assuming that the source material mentioned John Bardeen."
                    example = '{"entities": [{"type": "person", "title": "John Bardeen", "desc": "John Bardeen, along with Walter Brattain and Bill Shockley, co-invented the transistor during his time as a physicist at Bell Labs."}, ...]}'
                    example_cont = "For this example, you may also want to have included the transistor (object), The Invention of the Transistor (event), Walter Brattain (person), and Bill Shockley (person), assuming that all of these were actually mentioned in the source material."
                    conclusion = "Now, read the user's research topic and extract the relevant entites from the source given above."
                    system_prompt = "\n\n".join([intro, prompt_src_text, wiki, type_req, neg_req, rel_req, format_req, example, example_cont, conclusion])
                    user_prompt = self.topic

                    logger.debug(f"Make Entity User Prompt Length: {get_token_estimate(user_prompt)}")
                    logger.debug(f"Make Entity System Prompt Length: {get_token_estimate(system_prompt)}")

                    resp: LMResponse = lm.run(user_prompt, system_prompt, [], json_schema=Entities)
                    entities: Entities = resp.parsed

                    for ent in entities.entities:
                        ent: EntityData

                        if ent.type not in ENTITY_TYPES:
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
                            new_entity = Entity(
                                type=ent.type,
                                title=ent.title,
                                desc=ent.desc,
                                slug=slug
                            )
                            new_entity: Entity = self._insert_row(new_entity)
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

        return made_entities


    def write(self, lm: LM, max_n=None, rewrite=False) -> list[Entity]:
        all_entity_text = ""
        
        all_entities: list[Entity] = self.get_all_entities()
        all_entities_info = [(x.title, x.slug) for x in all_entities]
        all_entity_text = "\n".join([f"[{x[0]}]({x[1]})" for x in all_entities_info])

        if rewrite:
            entities = list(all_entities)
        else:
            entities = self._match_rows(Entity(is_written=False))
        written = []
        total = min(len(entities), max_n) if max_n is not None else len(entities)
        for i in tqdm(range(total), desc="Writing", disable=logger.level > logging.INFO):
            ent: Entity = entities[i]

            logger.debug(f"Writing entity '{ent.title}'")

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
                    links = "You can specify a link to another wiki entry like: [[slug | Title]]. Whenever you mention some other entity, you should probably use a link. Here are all the entries in the wiki for your reference:"
                    all_entity_text = all_entity_text
                    source_instruct = "Below are sources from which you can draw material for your wiki entry. **Use only these sources for the information in your entry. You may not draw from any other outside information you may have.**"
                    source_text = make_retrieval_prompt(lm, [data.text for data in combined], prefixes=[f"<START OF SOURCE WITH ID {data.id}>" for data in combined], suffixes=[f"</END OF SOURCE WITH ID {data.id}>" for data in combined])
                    references = "In order to cite a source using a footnote, use the syntax '[[@SOURCE_ID]]', with the @ sign. For example, a footnote to source with ID 15 would be [[@15]]. A link to the proper source will be automatically placed; DO NOT WRITE A FOOTNOTES OR REFERENCES SECTION. THEY WILL BE AUTOMATICALLY INCLUDED. WHENEVER YOU CITE A SOURCE (as opposed to another article) YOU MUST USE THE AT (@) SIGN."
                    conclusion = "Now the user will specify which wiki page you are tasked with writing."
                    system = "\n\n".join([intro, links, all_entity_text, source_instruct, source_text, references, conclusion])

                    user_prompt_intro = f"You are writing the wiki entry for {ent.title} ({ent.slug})."
                    user_prompt_disambiguation = f"A brief description of this entity for disambiguation: {ent.desc}"
                    user_prompt_topic = f"The goal of the wiki is to fulfill this research goal: {self.topic}"
                    prompt = "\n".join([user_prompt_intro, user_prompt_disambiguation, user_prompt_topic])
                    
                    logger.debug(f"Write User Prompt Length: {get_token_estimate(prompt)}")
                    logger.debug(f"Write System Prompt Length: {get_token_estimate(system)}")

                    lm_resp: LMResponse = lm.run(prompt, system, [])
                    new_markdown = lm_resp.text
                    
                    ent.markdown = new_markdown
                    ent.is_written = True
                    self._update_row(ent)
                    written.append(ent)

                except:
                    logger.debug(traceback.format_exc())
                    logger.error(f"An exception occurred trying to write entry for {ent.slug}. Moving on.")

        return written


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


    def serve(self):
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
        
        app.run(port=5000, threaded=False)
