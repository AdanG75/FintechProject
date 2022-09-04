from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from schemas.type_user import TypeUser

pattern_phone: str = r"^\+?\d{1,4}([ -]?\d){3,14}$"


class UserBase(BaseModel):
    email: EmailStr = Field(...)
    name: str = Field(...)
    phone: Optional[str] = Field(None, regex=pattern_phone, min_length=7, max_length=25)
    type_user: TypeUser = Field(...)


class UserRequest(UserBase):
    password: Optional[str] = Field(None, min_length=8, max_length=49)
    public_key: Optional[str] = Field(None, min_length=32, max_length=1024)

    class Config:
        schema_extra = {
            "example": {
                "email": "example@mail.com",
                "name": "Pedro",
                "phone": "+527449634562",
                "type_user": "client",
                "password": "AvenDF98-pal",
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv5OpqsWW5664Jz/hDrNd\nP5m/cbS4KVCJ+nJuahZ4Nc4x2Sf2I8yreXmYZZE9ZnsGdYXLff4cWkpZa0cVtMds\nqwHsPcou8lbIXCgm0+Vjimla4incSmYnglcQrnSQnbEL2W2Fb3u7qMPv9toEIh3o\nstD7b5Am9J6SeSewPrv8HUgd/mxgby85MjPo5p9BXk8zSbTxyDFqAynWm9nMYdBV\n/PqvyglBXwtIaCmE6ydAZu+a3URfTsVrW3OVcATFeBgRfmCeuYjFVsrj5j6il5qr\nX5uN1gZtvfme/oVDBirgnM2daHPf4IIlvNQSzTwJvztUyth4BpWivn8v0O9qUtgy\nWwIDAQAB\n-----END PUBLIC KEY-----"
            }
        }


class MarketInner(BaseModel):
    id_market: str = Field(...)
    type_market: str = Field(...)
    web_page: Optional[str] = Field(None)
    rfc: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class ClientInner(BaseModel):
    id_client: str = Field(...)
    last_name: str = Field(...)
    birth_date: str = Field(...)
    age: int = Field(...)

    class Config:
        orm_mode = True


class AdminInner(BaseModel):
    id_admin: str = Field(...)
    full_name: str = Field(...)

    class Config:
        orm_mode = True


class AccountInner(BaseModel):
    id_account: int = Field(...)
    alias_account: str = Field(...)
    paypal_email: Optional[str] = Field(None)
    main_account: bool = Field(...)

    class Config:
        orm_mode = True


class UserBasicDisplay(UserBase):
    id_user: int = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class UserDisplay(UserBase):
    id_user: int = Field(...)
    created_time: datetime = Field(...)

    accounts: Optional[List[AccountInner]] = Field(None)

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


class UserAdminDisplay(UserDisplay):
    admin: AdminInner = Field(...)

    class Config:
        orm_mode = True


class UserPublicKey(BaseModel):
    public_key: str = Field(..., min_length=32, max_length=1024)


class UserPublicKeyRequest(UserPublicKey):

    class Config:
        schema_extra = {
            "example": {
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv5OpqsWW5664Jz/hDrNd\nP5m/cbS4KVCJ+nJuahZ4Nc4x2Sf2I8yreXmYZZE9ZnsGdYXLff4cWkpZa0cVtMds\nqwHsPcou8lbIXCgm0+Vjimla4incSmYnglcQrnSQnbEL2W2Fb3u7qMPv9toEIh3o\nstD7b5Am9J6SeSewPrv8HUgd/mxgby85MjPo5p9BXk8zSbTxyDFqAynWm9nMYdBV\n/PqvyglBXwtIaCmE6ydAZu+a3URfTsVrW3OVcATFeBgRfmCeuYjFVsrj5j6il5qr\nX5uN1gZtvfme/oVDBirgnM2daHPf4IIlvNQSzTwJvztUyth4BpWivn8v0O9qUtgy\nWwIDAQAB\n-----END PUBLIC KEY-----"
            }
        }


class PublicKeyDisplay(UserPublicKey):

    class Config:
        orm_mode = True
