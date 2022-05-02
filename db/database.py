from sqlalchemy import create_engine
from sqlalchemy import engine as db_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

if settings.is_on_cloud():
    URL_POSTGRES_DB = settings.get_database_url()
    engine = create_engine(URL_POSTGRES_DB)
else:
    engine = create_engine(
        # Equivalent URL:
        # postgresql+pg8000://<db_user>:<db_pass>@/<db_name>
        #                         ?unix_sock=<socket_path>/<cloud_sql_instance_name>/.s.PGSQL.<port>
        # Note: Some drivers require the `unix_sock` query parameter to use a different key.
        # For example, 'psycopg2' uses the path set to `host` in order to connect successfully.
        db_engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=settings.get_db_user(),  # e.g. "my-database-user"
            password=settings.get_db_password(),  # e.g. "my-database-password"
            database=settings.get_db_name(),  # e.g. "my-database-name"
            query={
                "unix_sock": "{}/{}/.s.PGSQL.{}".format(
                    settings.get_db_socket(),  # e.g. "/cloudsql"
                    settings.get_db_instance(),  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
                    settings.get_db_port()  # e.g. "5432"
                )
            }
        )
    )

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
