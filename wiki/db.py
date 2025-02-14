from sqlalchemy import Column, Integer, String, Sequence, DateTime, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, Sequence('source_id'), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())  # Auto-set on creation
    type = Column(String(50), nullable=False)  # 'local' or 'web'
    link = Column(String, nullable=False)  # Required field
    title = Column(String)  # Nullable
    
    snippet = Column(String)  # Snippet returned in search result, if applicable
    query = Column(String)  # Query used to get source, if applicable
    search_engine = Column(String)  # Search engine where the source was found, if applicable

    def __repr__(self):
        return f"<Source(id={self.id}, title={self.title}, ...)>"


# Source types
WEBPAGE = 'web'
LOCAL = 'local'
