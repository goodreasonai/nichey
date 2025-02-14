from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .db import Base, Source, WEBPAGE
from .scraper import Scraper, ScrapeResponse
from .search_engine import WebLink


class Wiki():
    title: str
    topic: str
    path: str
    _engine: Engine
    def __init__(self, title=None, topic=None, path=None):
        self.title = title
        self.topic = topic
        if path is None:
            self.path = 'wiki.db'
        else:
            # TODO: auto populate title / topic, other things
            self.path = path

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


    # Should also add source data
    def add_source(self, type, title, link, snippet=None, query=None, search_engine=None):
        with self._get_session() as session:
            new_source = Source(
                type=type,
                title=title,
                link=link,
                snippet=snippet,
                query=query,
                search_engine=search_engine
            )
            session.add(new_source)

    def get_sources(self, limit=100, offset=0) -> list[Source]:
        with self._get_session() as session:
            sources = session.query(Source).limit(limit).offset(offset).all()
            return sources

    # Scrapes and stores info in the db
    def scrape_web_results(self, scraper: Scraper, results: list[WebLink]):
        for res in results:
            resp: ScrapeResponse = scraper.scrape(res.url)
            self.add_source(
                type=WEBPAGE,
                title=resp.metadata.title,
                link=resp.url,
                query=res.query,
                search_engine=res.search_engine
            )
            # TODO add source data as well
