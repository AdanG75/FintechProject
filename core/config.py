import os


class Settings:
    PROJECT_NAME: str = "Fintech75"
    PROJECT_VERSION: str = "1.0.0"

    def start(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'fintech75-917eb42b6c2a.json'


settings = Settings()
