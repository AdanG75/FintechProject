from pydantic import BaseModel, Field

from schemas.address_base import AddressRequest, AddressDisplay
from schemas.client_base import ClientRequest, ClientDisplay
from schemas.credit_base import CreditDisplay
from schemas.user_base import UserRequest, UserBasicDisplay


class ClientFullRequest(BaseModel):
    user: UserRequest = Field(...)
    client: ClientRequest = Field(...)
    address: AddressRequest = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "email": "un_cliente@clientmail.com",
                    "name": "Don Ramón",
                    "phone": "+528123658547",
                    "type_user": "client",
                    "password": "147963lkjh::ZXC",
                    "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxJ9NUy6G4nu5JG5C7UE7\nwU8htabM07d0xemw6EU0q1QxfK+K1xHG6RpvAnP4l9kDkHgL88E2jmYFhgABJhhC\nZsX0NS0nJh7J4a6vGlJ4Y/jn6flH+YEf0+6YzUa93ADq6mCxsRMNqR9nOcE2Irkm\nEfHqxwUsCYz/LC/iG/ERtD4CTPitxhznYATB9vK+k67ocaStEsGb9pDIEK0n2brp\nshm+U+ubLLOE0nCLH11APPqHm0F3zocqotS+4Fh/5texVhnsFzkogdowiiNLOzAV\nNBOLi+o+h1YiXwbFeQfphm4XDC60TdMVidmRgGV8UJfudi4eFRS8eLv8Jy395fGs\nQwIDAQAB\n-----END PUBLIC KEY-----"
                },
                "client": {
                    "id_user": 1,
                    "last_name": "Valdés",
                    "birth_date": "1923/09/02"
                },
                "address": {
                    "id_branch": None,
                    "id_client": "CLI-5966ce3b1a984854879e9dbe41f97bb0",
                    "type_owner": "client",
                    "is_main": True,
                    "zip_code": "18062",
                    "state": "Ciudad de México",
                    "city": "CDMX",
                    "neighborhood": "La Sierra",
                    "street": "Calle Cinco",
                    "ext_number": "12",
                    "inner_number": None
                }
            }
        }


class ClientComplexDisplay(BaseModel):
    user: UserBasicDisplay = Field(...)
    client: ClientDisplay = Field(...)


class ClientFullDisplay(ClientComplexDisplay):
    address: AddressDisplay = Field(...)
    global_credit: CreditDisplay = Field(...)

    class Config:
        orm_mode = True


class ClientProfileDisplay(ClientComplexDisplay):
    class Config:
        orm_mode = True
