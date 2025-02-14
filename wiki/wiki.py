from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .db import Base, Source, WebSource, SourceData, SourcePrimaryData, SourceScreenshot
from .scraper import Scraper, ScrapeResponse
from .search_engine import WebLink
import os


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
                    with open(path, 'rb') as f:
                        file_data = f.read()
            
                    primary_data = SourcePrimaryData(
                        mimetype=resp.metadata.content_type,
                        data=file_data,
                        source_id=new_source.id,
                        text=None  # TODO
                    )
                    session.add(primary_data)

                with resp.consume_screenshots() as (ss_paths, ss_mimetypes):
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
                    

    def make_entities(self, lm):
        # Go through sources
        while True:
            sources = self.get_sources(are_entities_extracted=False)

            for src in sources:
                src: Source
                primary_data = self.get_source_primary_data(src.id)
                # TODO

            if not len(sources):
                break