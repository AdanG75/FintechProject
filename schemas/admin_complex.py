from pydantic import BaseModel, Field

from schemas.admin_base import AdminRequest, AdminDisplay
from schemas.user_base import UserRequest, UserBasicDisplay


class AdminFullRequest(BaseModel):
    user: UserRequest = Field(...)
    admin: AdminRequest = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "user": {
                   "email": "admin@mail.com",
                   "name": "Admin 75",
                   "phone": "+525512334455",
                   "type_user": "admin",
                   "password": "123456789password",
                   "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxJ9NUy6G4nu5JG5C7UE7\nwU8htabM07d0xemw6EU0q1QxfK+K1xHG6RpvAnP4l9kDkHgL88E2jmYFhgABJhhC\nZsX0NS0nJh7J4a6vGlJ4Y/jn6flH+YEf0+6YzUa93ADq6mCxsRMNqR9nOcE2Irkm\nEfHqxwUsCYz/LC/iG/ERtD4CTPitxhznYATB9vK+k67ocaStEsGb9pDIEK0n2brp\nshm+U+ubLLOE0nCLH11APPqHm0F3zocqotS+4Fh/5texVhnsFzkogdowiiNLOzAV\nNBOLi+o+h1YiXwbFeQfphm4XDC60TdMVidmRgGV8UJfudi4eFRS8eLv8Jy395fGs\nQwIDAQAB\n-----END PUBLIC KEY-----"
                },
                "admin": {
                    "id_user": 1,
                    "full_name": "Juan Escutia"
                }
            }
        }


class AdminFullDisplay(BaseModel):
    user: UserBasicDisplay = Field(...)
    admin: AdminDisplay = Field(...)

    class Config:
        orm_mode = True
