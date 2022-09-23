import os
from pathlib import Path
from typing import Union

import sqlalchemy
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv

from core.secret_manager import access_secret_version


class Settings(object):
    __ON_ClOUD: bool
    __PROJECT_NAME: str
    __PROJECT_VERSION: str
    __ID_SYSTEM: int
    __MARKET_SYSTEM: str
    __POSTGRES_USER: str
    __POSTGRES_PASSWORD: str
    __POSTGRES_DB: str
    __POSTGRES_SERVER: str
    __POSTGRES_PORT: int
    __DATABASE_URL: Union[str, URL]
    __DB_SOCKET_DIR: str
    __INSTANCE_CONNECTION_NAME: str
    __SECRET_KEY: str
    __ALGORITHM: str
    __ACCESS_TOKEN_EXPIRE_MINUTES: int
    __CIPHER_KEY: str
    __IV: str
    __BLOCK_SIZE: int
    __PUBLIC_KEY: str
    __PRIVATE_KEY: str
    __SERVER_BUCKET: str
    __GOOGLE_TOKEN: str
    __GOOGLE_REFRESH_TOKEN: str
    __GOOGLE_CLIENT_ID: str
    __GOOGLE_CLIENT_SECRET: str
    __TOKEN_URI: str

    def __init__(self):
        # Change value to True if app will being deployed to AppEngine
        self.__ON_CLOUD = False

        if not self.__ON_CLOUD:
            env_path = Path('.') / '.env'
            load_dotenv(dotenv_path=env_path)

            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'fintech75-aa48eab9d1dc.json'

        self.__PROJECT_NAME: str = os.environ.get("PROJECT_NAME")
        self.__PROJECT_VERSION: str = os.environ.get("PROJECT_VERSION")

        if self.__ON_CLOUD:
            self.__POSTGRES_USER: str = access_secret_version(
                project_id=self.__PROJECT_NAME,
                secret_id=os.environ.get("POSTGRES_USER")
            )
            self.__POSTGRES_PASSWORD: str = access_secret_version(
                project_id=self.__PROJECT_NAME,
                secret_id=os.environ.get("POSTGRES_PASSWORD")
            )
            self.__POSTGRES_DB: str = access_secret_version(
                project_id=self.__PROJECT_NAME,
                secret_id=os.environ.get("POSTGRES_DB")
            )

            self.__ID_SYSTEM: int = int(access_secret_version(
                project_id=self.__PROJECT_NAME,
                secret_id=os.environ.get("ID_SYSTEM")
            ))
            self.__MARKET_SYSTEM: str = access_secret_version(
                project_id=self.__PROJECT_NAME,
                secret_id=os.environ.get("MARKET_SYSTEM")
            )

            self.__POSTGRES_SERVER: str = ""
            self.__POSTGRES_PORT: int = 0
        else:
            self.__POSTGRES_USER: str = os.environ.get("POSTGRES_USER")
            self.__POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD")
            self.__POSTGRES_DB: str = os.environ.get("POSTGRES_DB")
            self.__POSTGRES_SERVER: str = os.environ.get("POSTGRES_SERVER")
            self.__POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT"))

            self.__ID_SYSTEM: int = int(os.environ.get("ID_SYSTEM"))
            self.__MARKET_SYSTEM: str = os.environ.get("MARKET_SYSTEM")

            # Hybrid test
            # self.__POSTGRES_USER: str = access_secret_version(
            #     project_id=self.__PROJECT_NAME,
            #     secret_id=os.environ.get("POSTGRES_USER")
            # )
            # self.__POSTGRES_PASSWORD: str = access_secret_version(
            #     project_id=self.__PROJECT_NAME,
            #     secret_id=os.environ.get("POSTGRES_PASSWORD")
            # )
            # self.__POSTGRES_DB: str = access_secret_version(
            #     project_id=self.__PROJECT_NAME,
            #     secret_id=os.environ.get("POSTGRES_DB")
            # )
            # self.__POSTGRES_SERVER: str = ""
            # self.__POSTGRES_PORT: int = 0

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
        self.__CIPHER_KEY: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("CIPHER_KEY")
        )
        self.__IV: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("IV")
        )
        self.__BLOCK_SIZE: int = int(access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("BLOCK_SIZE")
        ))
        self.__PRIVATE_KEY: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("PRIVATE_KEY")
        )
        self.__PUBLIC_KEY: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("PUBLIC_KEY")
        )
        self.__SERVER_BUCKET = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("SERVER_BUCKET")
        )
        self.__GOOGLE_TOKEN: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("GOOGLE_TOKEN")
        )
        self.__GOOGLE_REFRESH_TOKEN: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("GOOGLE_REFRESH_TOKEN")
        )
        self.__GOOGLE_CLIENT_ID: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("GOOGLE_CLIENT_ID")
        )
        self.__GOOGLE_CLIENT_SECRET: str = access_secret_version(
            project_id=self.__PROJECT_NAME,
            secret_id=os.environ.get("GOOGLE_CLIENT_SECRET")
        )

        self.__TOKEN_URI: str = os.environ.get('TOKEN_URI')
        self.__ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)

        return cls.instance

    def get_database_url(self):
        # if not self.__ON_CLOUD:
        #     self.__DATABASE_URL = f"postgresql://" \
        #                           f"{self.__POSTGRES_USER}:{self.__POSTGRES_PASSWORD}@" \
        #                           f"{self.__POSTGRES_SERVER}:{self.__POSTGRES_PORT}/" \
        #                           f"{self.__POSTGRES_DB}"

        if not self.is_on_cloud():
            self.__DB_SOCKET_DIR = "/home/coffe/cloudsql/"

            # Original
            self.__DATABASE_URL = f"postgresql://" \
                                  f"{self.__POSTGRES_USER}:{self.__POSTGRES_PASSWORD}@" \
                                  f"{self.__POSTGRES_SERVER}:{self.__POSTGRES_PORT}/" \
                                  f"{self.__POSTGRES_DB}"

            # Hybrid test
            # self.__DATABASE_URL = sqlalchemy.engine.url.URL.create(
            #     drivername="postgresql+pg8000",
            #     username=self.__POSTGRES_USER,
            #     password=self.__POSTGRES_PASSWORD,
            #     database=self.__POSTGRES_DB,
            #     query={
            #         "unix_sock": "{}/.s.PGSQL.5432".format(self.__DB_SOCKET_DIR + self.__INSTANCE_CONNECTION_NAME)
            #     }
            # )

        else:
            self.__DATABASE_URL = sqlalchemy.engine.url.URL.create(
                drivername="postgresql+pg8000",
                username=self.__POSTGRES_USER,
                password=self.__POSTGRES_PASSWORD,
                database=self.__POSTGRES_DB,
                query={
                    "unix_sock": "{}/.s.PGSQL.5432".format(self.__DB_SOCKET_DIR + self.__INSTANCE_CONNECTION_NAME)
                }
            )

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

    def get_server_cipher_key(self):
        return self.__CIPHER_KEY

    def get_server_iv(self):
        return self.__IV

    def get_server_block_size(self):
        return self.__BLOCK_SIZE

    def get_server_public_key(self):
        return self.__PUBLIC_KEY

    def get_server_private_key(self):
        return self.__PRIVATE_KEY

    def get_server_bucket(self):
        return self.__SERVER_BUCKET

    def get_id_system(self):
        return self.__ID_SYSTEM

    def get_market_system(self):
        return self.__MARKET_SYSTEM

    def get_google_token(self):
        return self.__GOOGLE_TOKEN

    def get_google_refresh_token(self):
        return self.__GOOGLE_REFRESH_TOKEN

    def get_google_client_id(self):
        return self.__GOOGLE_CLIENT_ID

    def get_google_client_secret(self):
        return self.__GOOGLE_CLIENT_SECRET

    def get_token_uri(self):
        return self.__TOKEN_URI

    def is_on_cloud(self):
        return self.__ON_CLOUD


def charge_settings() -> Settings:
    setting = Settings()

    return setting


settings = Settings()
