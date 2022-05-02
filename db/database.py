from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings


URL_POSTGRES_DB = settings.get_database_url()
engine = create_engine(URL_POSTGRES_DB)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# It is used to create Models
Base = declarative_base()


def get_db():
    """
    Provide the DB instance
    :return: The DB instance
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
