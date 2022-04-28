import os

from decouple import config


class Settings:
    PROJECT_NAME: str = "Fintech75"
    PROJECT_VERSION: str = "1.0.0"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DATABASE_URL: str

    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'fintech75-917eb42b6c2a.json'
        self.POSTGRES_USER: str = config("POSTGRES_USER")
        self.POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD")
        self.POSTGRES_SERVER: str = config("POSTGRES_SERVER")
        self.POSTGRES_PORT: str = config("POSTGRES_PORT")
        self.POSTGRES_DB: str = config("POSTGRES_DB")

    def get_database_url(self):
        self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self.DATABASE_URL


settings = Settings()
