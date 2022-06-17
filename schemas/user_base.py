from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from schemas.type_user import TypeUser


class UserBase(BaseModel):
    email: EmailStr = Field(...)
    name: str = Field(...)
    user_type: TypeUser = Field(...)


class UserRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=49)
    public_key: str = Field(..., min_length=32, max_length=1024)

    class Config:
        schema_extra = {
            "example": {
                "email": "example@mail.com",
                "name": "Pedro",
                "user_type": "client",
                "password": "AvenDF98-pal",
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv5OpqsWW5664Jz/hDrNd\nP5m/cbS4KVCJ+nJuahZ4Nc4x2Sf2I8yreXmYZZE9ZnsGdYXLff4cWkpZa0cVtMds\nqwHsPcou8lbIXCgm0+Vjimla4incSmYnglcQrnSQnbEL2W2Fb3u7qMPv9toEIh3o\nstD7b5Am9J6SeSewPrv8HUgd/mxgby85MjPo5p9BXk8zSbTxyDFqAynWm9nMYdBV\n/PqvyglBXwtIaCmE6ydAZu+a3URfTsVrW3OVcATFeBgRfmCeuYjFVsrj5j6il5qr\nX5uN1gZtvfme/oVDBirgnM2daHPf4IIlvNQSzTwJvztUyth4BpWivn8v0O9qUtgy\nWwIDAQAB\n-----END PUBLIC KEY-----"
            }
        }


class MarketInner:
    id_market: str = Field(...)
    type_market: str = Field(...)
    rfc: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class ClientInner(BaseModel):
    id_client: str = Field(...)
    id_address: int = Field(...)
    last_name: str = Field(...)
    birth_date: str = Field(...)
    age: int = Field(...)

    class Config:
        orm_mode = True


class AccountInner(BaseModel):
    id_account: int = Field(...)
    paypal_email: EmailStr = Field(...)
    type_owner: TypeUser = Field(...)
    main_account: bool = Field(True)

    class Config:
        orm_mode = True


class UserBasicDisplay(UserBase):
    id_user: int = Field(...)

    class Config:
        orm_mode = True


class UserDisplay(UserBase):
    id_user: int = Field(...)
    accounts: Optional[List[AccountInner]] = Field(None)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class UserClientDisplay(UserDisplay):
    client: ClientInner = Field(...)

    class Config:
        orm_mode = True


class UserMarketDisplay(UserDisplay):
    market: MarketInner = Field(...)

    class Config:
        orm_mode = True
