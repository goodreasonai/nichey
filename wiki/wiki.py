from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .db import Base, Source, WebSource, Entity, SourcePrimaryData, SourceScreenshot, ENTITY_TYPES, Reference
from .scraper import Scraper, ScrapeResponse
from .search_engine import WebLink
from .file_loaders import get_loader, FileLoader, RawChunk, TextSplitter
from .utils import get_ext_from_mime_type, get_token_estimate
import os
import sys
from pydantic import BaseModel
from .lm import LM, get_safe_context_length, LMResponse
from slugify import slugify
import traceback
from typing import Generator, Tuple, List


class Wiki():
    title: str
    topic: str
    path: str
    _engine: Engine
    def __init__(self, title=None, topic=None, path=None, replace=False):
        self.title = title
        self.topic = topic
        if path is None:
            self.path = 'wiki.db'
        else:
            # TODO: auto populate title / topic, other things
            self.path = path
        
        if replace:
            os.remove(self.path)

        # For a file-based database
        self._engine = create_engine(f'sqlite:///{self.path}')
        Base.metadata.create_all(self._engine)


    @contextmanager
    def _get_session(self):
        """Provide a transactional scope around a series of operations."""
        Session = sessionmaker(bind=self._engine, expire_on_commit=False)
        session = Session()
        try:
            yield session
            session.commit()  # Commit if all operations succeed
        except Exception as e:
            session.rollback()  # Rollback on any error
            raise e
        finally:
            session.close()  # Ensure the session is closed


    def set_title(self, title):
        self.title = title

    def set_topic(self, topic):
        self.topic = topic


    def get_sources(self, limit=100, offset=0, **kwargs) -> list[Source]:
        with self._get_session() as session:
            sources = session.query(Source).filter_by(**kwargs).limit(limit).offset(offset).all()
            return sources
        
    def get_entities(self, limit=100, offset=0, **kwargs) -> list[Entity]:
        with self._get_session() as session:
            entities = session.query(Entity).filter_by(**kwargs).limit(limit).offset(offset).all()
            return entities
    
    def get_source_primary_data(self, source_id) -> SourcePrimaryData:
        with self._get_session() as session:
            source = session.query(SourcePrimaryData).filter_by(source_id=source_id).first()
            return source
    
    def get_source_screenshots(self, source_id) -> list[SourceScreenshot]:
        with self._get_session() as session:
            sources = session.query(SourceScreenshot).filter_by(source_id=source_id).all()
            return sources

    # Scrapes and stores info in the db
    def scrape_web_results(self, scraper: Scraper, results: list[WebLink]):
        for res in results:
            resp: ScrapeResponse = scraper.scrape(res.url)

            with self._get_session() as session:
                new_source = WebSource(
                    title=resp.metadata.title,
                    url=resp.url,
                    snippet=res.snippet,
                    query=res.query,
                    search_engine=res.search_engine
                )

                session.add(new_source)
                session.flush()  # Get the new_source ID before committing

                with resp.consume_data() as path:
                    with resp.consume_screenshots() as (ss_paths, ss_mimetypes):
                        ext = get_ext_from_mime_type(resp.metadata.content_type)
                        loader: FileLoader = get_loader(ext, path)
                        if not loader:
                            print(f"Filetype '{resp.metadata.content_type}' cannot be parsed; moving along.", file=sys.stderr)
                            continue  # By exiting both consumes, they are automatically cleaned up

                        # This section takes up a lot of memory - copying both the text and file data to move it over to the database.
                        # There should be a better way.

                        txt = ""
                        splitter = TextSplitter()
                        for chunk in loader.load_and_split(splitter):
                            chunk: RawChunk
                            txt += chunk.page_content

                        with open(path, 'rb') as f:
                            file_data = f.read()

                        primary_data = SourcePrimaryData(
                            mimetype=resp.metadata.content_type,
                            data=file_data,
                            source_id=new_source.id,
                            text=txt
                        )
                        session.add(primary_data)

                        ss_paths: list[str]
                        ss_mimetypes: list[str]
                        for i, (ss_path, ss_mimetype) in enumerate(zip(ss_paths, ss_mimetypes)):
                            with open(ss_path, 'rb') as f:
                                ss_data = f.read()
                            
                            screenshot = SourceScreenshot(
                                mimetype=ss_mimetype,
                                data=ss_data,
                                source_id=new_source.id,
                                order=i
                            )
                            session.add(screenshot)
                    

    def make_entities(self, lm: LM) -> Generator[Tuple[List[Entity], Source]]:
        # Go through sources
        offset = 0  # Gets incremeted on an error
        while True:
            with self._get_session() as session:
                sources = session.query(Source).filter_by(are_entities_extracted=False).limit(100).offset(offset).all()
                if not len(sources):
                    break
                for src in sources:
                    made_entities = []
                    try:
                        src: Source
                        primary_data = self.get_source_primary_data(src.id)
                        text = primary_data.text
                        if text:
                            not_entities = ["Countries", "Nouns unrelated to the research topic", "Very common nouns or words", "Well-known cities not especially significant to the research topic"]
                            class EntityData(BaseModel):
                                type: str
                                title: str
                                desc: str

                            class Entities(BaseModel):
                                entities: list[EntityData]

                            intro = "You are tasked with extracting relevant entities from the given source material into JSON. Here is the text extracted from the source material:"

                            safe_token_length = get_safe_context_length(lm)                    
                            token_tot = 0
                            prompt_src_text = ""
                            splitter = TextSplitter()
                            for chunk_txt in splitter.split_text(text):
                                if get_token_estimate(chunk_txt) + token_tot > safe_token_length:
                                    break
                                prompt_src_text += chunk_txt
                            
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

                            resp: LMResponse = lm.run(user_prompt, system_prompt, [], json_schema=Entities)
                            entities: Entities = resp.parsed

                            for ent in entities.entities:
                                ent: EntityData

                                if ent.type not in ENTITY_TYPES:
                                    print(f"Extracted type '{ent.type}' not recognized (title was '{ent.title}', source was '{src.title}')", file=sys.stderr)

                                slug = slugify(ent.title, max_length=255)  # 255 is the max length of the slug text in the database... may want to standardize this somewhere.
                                # Check for duplicate
                                existing = session.query(Entity).filter_by(slug=slug).first()
                                if existing:
                                    print(f"Duplicate entity found for {slug}; not re-adding.", file=sys.stderr)
                                else:
                                    new_entity = Entity(
                                        type=ent.type,
                                        title=ent.title,
                                        desc=ent.desc,
                                        slug=slug
                                    )
                                    session.add(new_entity)
                                    session.flush()  # Make sure ID is loaded
                                    made_entities.append(new_entity)
                                    new_reference = Reference(
                                        source_id=src.id,
                                        entity_id=new_entity.id
                                    )
                                    session.add(new_reference)
                        src.are_entities_extracted = True
                        session.commit()
                        yield (made_entities, src)

                    except Exception as e:
                        print(traceback.format_exc())
                        print(f"An exception occurred trying to parse entities of source with id {src.id}. Moving on.", file=sys.stderr)
                        offset += 1

            if not len(sources):
                break