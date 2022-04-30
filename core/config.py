import os
from pathlib import Path

from dotenv import load_dotenv

from core.secret_manager import access_secret_version


class Settings:
    __ON_ClOUD: bool
    __PROJECT_NAME: str
    __PROJECT_VERSION: str
    __POSTGRES_USER: str
    __POSTGRES_PASSWORD: str
    __POSTGRES_SERVER: str
    __POSTGRES_PORT: str
    __POSTGRES_DB: str
    __DATABASE_URL: str
    __DB_SOCKET_DIR: str
    __INSTANCE_CONNECTION_NAME: str
    __SECRET_KEY: str
    __ALGORITHM: str
    __ACCESS_TOKEN_EXPIRE_MINUTES: int

    def __init__(self):
        # Change value to True if app will being deployed to AppEngine
        self.__ON_CLOUD = True

        if not self.__ON_CLOUD:
            env_path = Path('.') / '.env'
            load_dotenv(dotenv_path=env_path)

            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'fintech75-aa48eab9d1dc.json'

        self.__PROJECT_NAME: str = os.environ.get("PROJECT_NAME")
        self.__PROJECT_VERSION: str = os.environ.get("PROJECT_VERSION")

        self.__POSTGRES_USER: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("POSTGRES_USER")
        )
        self.__POSTGRES_PASSWORD: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("POSTGRES_PASSWORD")
        )
        self.__POSTGRES_SERVER: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("POSTGRES_SERVER")
        )
        self.__POSTGRES_PORT: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("POSTGRES_PORT")
        )
        self.__POSTGRES_DB: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("POSTGRES_DB")
        )
        self.__DB_SOCKET_DIR: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("DB_SOCKET_DIR")
        )
        self.__INSTANCE_CONNECTION_NAME: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("INSTANCE_CONNECTION_NAME")
        )
        self.__SECRET_KEY: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get('SECRET_KEY')
        )
        self.__ALGORITHM: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get('ALGORITHM')
        )

        self.__ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))

    def get_database_url(self):
        if not self.__ON_CLOUD:
            self.__DATABASE_URL = f"postgresql://" \
                                  f"{self.__POSTGRES_USER}:{self.__POSTGRES_PASSWORD}@" \
                                  f"{self.__POSTGRES_SERVER}:{self.__POSTGRES_PORT}/" \
                                  f"{self.__POSTGRES_DB}"
        else:
            # postgresql+pg8000://<db_user>:<db_pass>@/<db_name>
            #                         ?unix_sock=<socket_path>/<cloud_sql_instance_name>/.s.PGSQL.<db_port>
            self.__DATABASE_URL = f"postgresql+pg8000://" \
                                  f"{self.__POSTGRES_USER}:{self.__POSTGRES_PASSWORD}@/" \
                                  f"{self.__POSTGRES_DB}?unix_socket={self.__DB_SOCKET_DIR}/" \
                                  f"{self.__INSTANCE_CONNECTION_NAME}/.s.PGSQL.{self.__POSTGRES_PORT}"

        return self.__DATABASE_URL

    def get_secret_key(self):
        return self.__SECRET_KEY

    def get_algorithm(self):
        return self.__ALGORITHM

    def get_expire_minutes(self):
        return self.__ACCESS_TOKEN_EXPIRE_MINUTES

    def get_project_name(self):
        return self.__PROJECT_NAME

    def get_project_version(self):
        return self.__PROJECT_VERSION


settings = Settings()
