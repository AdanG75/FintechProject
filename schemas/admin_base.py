
from pydantic import BaseModel, EmailStr, Field


class AdminBase(BaseModel):
    username: str = Field(..., min_length=4, max_length=49)
    email: EmailStr = Field(...)


class AdminRequest(AdminBase):
    password: str = Field(..., min_length=8, max_length=31)
    public_key: str = Field(..., min_length=64)

    class Config:
        schema_extra = {
            "example": {
                "username": "super_user",
                "email": "mail@fintech75.com",
                "password": "secret-password",
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxJ9NUy6G4nu5JG5C7UE7\nwU8htabM07d0xemw6EU0q1QxfK+K1xHG6RpvAnP4l9kDkHgL88E2jmYFhgABJhhC\nZsX0NS0nJh7J4a6vGlJ4Y/jn6flH+YEf0+6YzUa93ADq6mCxsRMNqR9nOcE2Irkm\nEfHqxwUsCYz/LC/iG/ERtD4CTPitxhznYATB9vK+k67ocaStEsGb9pDIEK0n2brp\nshm+U+ubLLOE0nCLH11APPqHm0F3zocqotS+4Fh/5texVhnsFzkogdowiiNLOzAV\nNBOLi+o+h1YiXwbFeQfphm4XDC60TdMVidmRgGV8UJfudi4eFRS8eLv8Jy395fGs\nQwIDAQAB\n-----END PUBLIC KEY-----"
            }
        }


class AdminDisplay(AdminBase):
    id: int = Field(gt=0)

    class Config:
        orm_mode = True


class AdminToken(BaseModel):
    token_type: str
    access_token: str
    admin: AdminDisplay

