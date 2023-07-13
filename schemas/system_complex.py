from pydantic import BaseModel, Field

from schemas.market_base import MarketRequest, MarketDisplay
from schemas.user_base import UserRequest, UserBasicDisplay


class SystemFullRequest(BaseModel):
    user: UserRequest = Field(...)
    market: MarketRequest = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "email": "system@fintech75.com",
                    "name": "Fintech75",
                    "phone": "+525599999999",
                    "type_user": "system",
                    "password": "superpassword75",
                    "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxJ9NUy6G4nu5JG5C7UE7\nwU8htabM07d0xemw6EU0q1QxfK+K1xHG6RpvAnP4l9kDkHgL88E2jmYFhgABJhhC\nZsX0NS0nJh7J4a6vGlJ4Y/jn6flH+YEf0+6YzUa93ADq6mCxsRMNqR9nOcE2Irkm\nEfHqxwUsCYz/LC/iG/ERtD4CTPitxhznYATB9vK+k67ocaStEsGb9pDIEK0n2brp\nshm+U+ubLLOE0nCLH11APPqHm0F3zocqotS+4Fh/5texVhnsFzkogdowiiNLOzAV\nNBOLi+o+h1YiXwbFeQfphm4XDC60TdMVidmRgGV8UJfudi4eFRS8eLv8Jy395fGs\nQwIDAQAB\n-----END PUBLIC KEY-----"
                },
                "market": {
                    "id_user": 1,
                    "type_market": "System",
                    "web_page": "https://fintech75.app/",
                    "rfc": "FTEC200321STC"
                }
            }
        }


class SystemFullDisplay(BaseModel):
    user: UserBasicDisplay = Field(...)
    market: MarketDisplay = Field(...)

    class Config:
        orm_mode = True
