from typing import List

from pydantic import BaseModel, Field

from schemas.account_base import AccountRequest, AccountDisplay
from schemas.address_base import AddressRequest, AddressDisplay
from schemas.branch_base import BranchRequest, BranchDisplay
from schemas.market_base import MarketRequest, MarketDisplay, MarketBasicDisplay, MarketComplexDisplay
from schemas.user_base import UserRequest, UserBasicDisplay, UserBase, UserDisplay


class MarketFullRequest(BaseModel):
    user: UserRequest = Field(...)
    market: MarketRequest = Field(...)
    branch: BranchRequest = Field(...)
    address: AddressRequest = Field(...)
    account: AccountRequest = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "user": {
                   "email": "tacos@tacos.com",
                   "name": "Tacos al Carbon",
                   "phone": "+525599887766",
                   "type_user": "market",
                   "password": "tacos98==9*",
                   "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxJ9NUy6G4nu5JG5C7UE7\nwU8htabM07d0xemw6EU0q1QxfK+K1xHG6RpvAnP4l9kDkHgL88E2jmYFhgABJhhC\nZsX0NS0nJh7J4a6vGlJ4Y/jn6flH+YEf0+6YzUa93ADq6mCxsRMNqR9nOcE2Irkm\nEfHqxwUsCYz/LC/iG/ERtD4CTPitxhznYATB9vK+k67ocaStEsGb9pDIEK0n2brp\nshm+U+ubLLOE0nCLH11APPqHm0F3zocqotS+4Fh/5texVhnsFzkogdowiiNLOzAV\nNBOLi+o+h1YiXwbFeQfphm4XDC60TdMVidmRgGV8UJfudi4eFRS8eLv8Jy395fGs\nQwIDAQAB\n-----END PUBLIC KEY-----"
                },
                "market": {
                    "id_user": 1,
                    "type_market": "Taqueria",
                    "web_page": "https://www.facebook.com/1478526",
                    "rfc": "RETY020321WDV"
                },
                "branch": {
                    "id_market": "MKT-b7eb707466ad4eb3b60ca153aa565036",
                    "branch_name": "Sucursal principal",
                    "service_hours": "09:00 - 21:00",
                    "phone": "+525599887766",
                    "password": "8745213sf"
                },
                "address": {
                    "id_branch": "BRH-684572407e864236917cab16f7baa36e",
                    "id_client": None,
                    "type_owner": "market",
                    "is_main": True,
                    "zip_code": "18966",
                    "state": "Ciudad de México",
                    "city": "CDMX",
                    "neighborhood": "La gran Loma",
                    "street": "Avenida Principal",
                    "ext_number": "5",
                    "inner_number": "12A"
                },
                "account": {
                    "id_user": 1,
                    "alias_account": "Cuenta maestra",
                    "paypal_email": "market@mail.com",
                    "paypal_id_client": "XXXXXXXXXXXXXXXXXXXXXX",
                    "paypal_secret": "************************",
                    "type_owner": "market",
                    "main_account": True
                }
            }
        }


class MarketFullDisplay(BaseModel):
    user: UserBasicDisplay = Field(...)
    market: MarketDisplay = Field(...)
    branch: BranchDisplay = Field(...)
    address: AddressDisplay = Field(...)
    account: AccountDisplay = Field(...)

    class Config:
        orm_mode = True


class MarketProfileDisplay(BaseModel):
    user: UserDisplay = Field(...)
    market: MarketComplexDisplay = Field(...)

    class Config:
        orm_mode = True


class MarketSimpleDisplay(BaseModel):
    market: MarketBasicDisplay = Field(...)
    user: UserBase = Field(...)

    class Config:
        orm_mode = True


class MarketSimpleListDisplay(BaseModel):
    markets: List[MarketSimpleDisplay] = Field(..., min_items=0)

    class Config:
        orm_mode = True
