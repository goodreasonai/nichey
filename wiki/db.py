from dataclasses import dataclass
import datetime
import sqlite3
from datetime import datetime
import tempfile
import os
from .logger import logger


DB_VERSION = 2  # Incremement when making changes to the schema to force auto migration

ENTITY_TYPES = ["person", "place", "organization", "event", "publication", "law", "product", "object", "concept"]

@dataclass
class Source():
    title: str | None = None
    text: str | None = None

    id: int | None = None
    created_at: datetime | None = None
    are_entities_extracted: int | None = None

    author: str | None = None
    desc: str | None = None
    url: str | None = None
    snippet: str | None = None
    query: str | None = None
    search_engine: str | None = None

@dataclass
class PrimarySourceData():
    source_id: int | None = None
    mimetype: str | None = None
    data: bytes | None = None
    id: int | None = None
    created_at: datetime | None = None

@dataclass
class ScreenshotData():
    source_id: int | None = None
    mimetype: str | None = None
    data: bytes | None = None
    place: int | None = None 
    id: int | None = None
    created_at: datetime | None = None

@dataclass
class Entity():
    slug: str | None = None
    title: str | None = None
    type: str | None = None
    desc: str | None = None
    markdown: str | None = None
    is_written: int | None = None
    id: int | None = None
    created_at: datetime | None = None

@dataclass
class Reference():
    source_id: int = None
    entity_id: int = None
    id: int = None

# Mapping of table names to dataclasses
TABLE_TO_DATACLASS = {
    "sources": Source,
    "primary_source_data": PrimarySourceData,
    "screenshot_data": ScreenshotData,
    "entities": Entity,
    "refs": Reference
}
DATACLASS_TO_TABLE = {v: k for k, v in TABLE_TO_DATACLASS.items()}

def create_db(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    try:
        sql = """
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            are_entities_extracted INTEGER DEFAULT 0,
            
            title TEXT,
            text TEXT,

            author TEXT,
            desc TEXT,
            url TEXT,
            snippet TEXT,
            query TEXT,
            search_engine TEXT,

            tbl TEXT DEFAULT 'sources'
        )
        """
        cursor.execute(sql)

        # FTS5 Search over source text
        sql = """
            CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts5 USING fts5(
                source_id UNINDEXED,
                title,
                author,
                desc,
                text
            );
        """
        cursor.execute(sql)
        sql = """
            CREATE TRIGGER IF NOT EXISTS after_sources_insert
            AFTER INSERT ON sources
            BEGIN
                INSERT INTO sources_fts5 (source_id, title, author, desc, text) VALUES (NEW.id, NEW.title, NEW.author, NEW.desc, NEW.text);
            END;
        """
        cursor.execute(sql)
        sql = """
            CREATE TRIGGER IF NOT EXISTS after_sources_update
            AFTER UPDATE ON sources
            BEGIN
                DELETE FROM sources_fts5 WHERE source_id = OLD.id;
                INSERT INTO sources_fts5 (source_id, title, author, desc, text) VALUES (NEW.id, NEW.title, NEW.author, NEW.desc, NEW.text);
            END;
        """
        cursor.execute(sql)
        sql = """
            CREATE TRIGGER IF NOT EXISTS after_sources_delete
            AFTER DELETE ON sources
            BEGIN
                DELETE FROM sources_fts5 WHERE source_id = OLD.id;
            END;
        """
        cursor.execute(sql)

        sql = """
        CREATE TABLE primary_source_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            mimetype TEXT,
            data BLOB,

            tbl TEXT DEFAULT 'primary_source_data'
        )
        """
        cursor.execute(sql)

        sql = """
            CREATE TABLE screenshot_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                mimetype TEXT,
                data BLOB,
                place INTEGER,

                tbl TEXT DEFAULT 'screenshot_data'
            )
        """
        cursor.execute(sql)

        sql = """
            CREATE TABLE entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug VARCHAR(255) UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                type TEXT,
                desc TEXT,
                markdown TEXT,
                is_written INTEGER DEFAULT 0,

                tbl TEXT DEFAULT 'entities'
            )
        """
        cursor.execute(sql)
        sql = """
            CREATE UNIQUE INDEX idx_entities_slug ON entities(slug);
        """
        cursor.execute(sql)

        sql = """
            CREATE TABLE refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                entity_id INTEGER,

                tbl TEXT DEFAULT 'refs'
            )
        """
        cursor.execute(sql)
        sql = """
            CREATE INDEX idx_references_source_id ON refs(source_id);
        """
        cursor.execute(sql)
        sql = """
            CREATE INDEX idx_references_entity_id ON refs(entity_id);
        """
        cursor.execute(sql)

        sql = f"""
            PRAGMA user_version = {DB_VERSION}
        """
        cursor.execute(sql)
        conn.commit()
    finally:
        conn.close()


def obj_factory(cursor: sqlite3.Cursor, row):
    """Maps database rows to their respective dataclass objects."""
    fields = [column[0] for column in cursor.description]
    my_dict = { key: value for key, value in zip(fields, row) }
    if 'tbl' not in my_dict:  # Would be something special like getting a pragma or something
        return my_dict
    tbl = my_dict['tbl']
    dataclass = TABLE_TO_DATACLASS[tbl]
    del my_dict['tbl']
    return dataclass(**my_dict)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Migrates the user's database to the current version
# Will copy over all columns that still exist + add new ones (with null values)
def migrate_db(path, conn: sqlite3.Connection):
    sql = "PRAGMA user_version"
    res = conn.execute(sql)
    version = res.fetchone()['user_version']
    if version >= DB_VERSION:
        return path, conn

    logger.warning("Existing wiki database is out of date; migrating to new version.")

    # Create new database
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    db_path = temp_file.name

    create_db(db_path)
    new_conn = sqlite3.connect(db_path)
    new_conn.row_factory = obj_factory

    new_cursor = new_conn.cursor()
    conn.row_factory = dict_factory  # Makes it easier to copy things over, but new one stays obj_factory
    old_cursor = conn.cursor()

    tables_to_reconstruct = [x for x in TABLE_TO_DATACLASS.keys()]

    for table in tables_to_reconstruct:
        # Get common columns first
        new_cursor.execute(f"PRAGMA table_info({table});")
        new_columns = {col["name"] for col in new_cursor.fetchall()}

        old_cursor.execute(f"PRAGMA table_info({table});")
        old_columns = {col["name"] for col in old_cursor.fetchall()}

        common_columns = new_columns.intersection(old_columns)
        if not common_columns:
            continue

        columns_list = ", ".join(common_columns)

        # 1. Read rows from old DB in one go (or chunked if data is huge).
        select_sql = f"SELECT {columns_list} FROM {table}"
        old_cursor.execute(select_sql)
        rows = old_cursor.fetchall()

        # 2. Insert them into new DB efficiently:
        placeholders = ", ".join(["?"] * len(common_columns))
        insert_sql = f"INSERT INTO {table} ({columns_list}) VALUES ({placeholders})"

        # Wrap in a transaction for fewer commits
        new_conn.execute("BEGIN TRANSACTION;")
        # executemany can take an iterable of tuples
        new_cursor.executemany(
            insert_sql,
            (
                tuple(row_dict[col] for col in common_columns)
                for row_dict in rows
            ),
        )
        new_conn.execute("COMMIT;")

    new_conn.commit()
    
    new_cursor.close()
    old_cursor.close()

    # Remove the old database and attach new one
    os.remove(path)
    return db_path, new_conn
