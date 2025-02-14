from sqlalchemy import Column, Integer, String, Sequence, DateTime, func, Boolean, ForeignKey, LargeBinary, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


# Parent to web source
class Source(Base):
    __tablename__ = 'source'
    id = Column(Integer, Sequence('source_id'), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    are_entities_extracted = Column(Boolean, default=False)
    title = Column(String)
    type = Column(String)

    __mapper_args__ = {'polymorphic_identity': 'source', 'polymorphic_on': 'type'}


# The inheritance here is joined table inheritance
class WebSource(Source):
    __tablename__ = 'web_source'
    id = Column(Integer, ForeignKey('source.id'), primary_key=True)
    url = Column(String, nullable=False)  # Required field
    snippet = Column(String)  # Snippet returned in search result, if applicable
    query = Column(String)  # Query used to get source, if applicable
    search_engine = Column(String)  # Search engine where the source was found, if applicable
    
    __mapper_args__ = {'polymorphic_identity': 'web_source'}


# Parent to primary data and screenshots
class SourceData(Base):
    __tablename__ = 'source_data'

    id = Column(Integer, Sequence('source_data_id'), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    mimetype = Column(String, nullable=False)
    data = Column(LargeBinary)
    type = Column(String)

    source_id = Column(Integer, 
                      ForeignKey('source.id', ondelete="CASCADE"),
                      nullable=False)

    __mapper_args__ = {'polymorphic_identity': 'source_data', 'polymorphic_on': 'type'}


class SourcePrimaryData(SourceData):
    __tablename__ = 'source_primary_data'

    id = Column(Integer, ForeignKey('source_data.id'), primary_key=True)
    text = Column(Text)

    __mapper_args__ = {'polymorphic_identity': 'source_primary_data'}


class SourceScreenshot(SourceData):
    __tablename__ = 'source_screenshot'

    id = Column(Integer, ForeignKey('source_data.id'), primary_key=True)
    order = Column(Integer, nullable=False)

    __mapper_args__ = {'polymorphic_identity': 'source_screenshot'}

