from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


money_pattern = r'^\d{1,12}(\.\d{1,2})?$'
quantity_pattern = r'^\d+$'
email_pattern = r"[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.?){2,4}$"


class UnitAmountInner(BaseModel):
    currency_code: str = Field('MXN', min_length=2, max_length=4)
    value: str = Field(..., regex=money_pattern)


class ItemInner(BaseModel):
    name: str = Field(..., min_length=2, max_length=79)
    description: str = Field('Movement', min_length=2, max_length=499)
    quantity: str = Field('1', regex=quantity_pattern)
    unit_amount: UnitAmountInner = Field(...)


class ItemTotalInner(BaseModel):
    item_total: UnitAmountInner = Field(...)


class AmountInner(UnitAmountInner):
    breakdown: Optional[ItemTotalInner] = Field(None)


class PurchaseUnitInner(BaseModel):
    items: Optional[List[ItemInner]] = Field(None, min_items=1)
    amount: AmountInner = Field(...)


class UrlInner(BaseModel):
    return_url: HttpUrl = Field('https://www.fintech75.app/successful-transaction')
    cancel_url: HttpUrl = Field('https://www.fintech75.app/cancel-transaction')


class PaypalComplexOrderRequest(BaseModel):
    intent: str = Field('CAPTURE', min_length=2, max_length=39)
    purchase_units: List[PurchaseUnitInner] = Field(..., min_items=1)
    application_context: Optional[UrlInner] = Field(None)

    class Config:
        schema_extra = {
            "example": {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "items": [
                            {
                                "name": "Something old",
                                "description": "Green XL",
                                "quantity": "1",
                                "unit_amount": {
                                    "currency_code": "MXN",
                                    "value": "50.00"
                                }
                            }
                        ],
                        "amount": {
                            "currency_code": "MXN",
                            "value": "50.00",
                            "breakdown": {
                                "item_total": {
                                    "currency_code": "MXN",
                                    "value": "50.00"
                                }
                            }
                        }
                    }
                ],
                "application_context": {
                    "return_url": "https://fintech75.app/",
                    "cancel_url": "https://fintech75.app/docs"
                }
            }
        }


# Order response
class OrderResponseBase(BaseModel):
    id: str = Field(..., min_length=8, max_length=25)
    intent: str = Field(..., min_length=5, max_length=10)
    status: str = Field(..., min_length=4, max_length=25)
    create_time: datetime = Field(...)
    total: UnitAmountInner = Field(...)


class LinkInner(BaseModel):
    href: HttpUrl = Field(...)
    rel: str = Field(..., min_length=4, max_length=8)
    method: str = Field(..., min_length=3, max_length=8)


class PayeeInner(BaseModel):
    email_address: str = Field(..., regex=email_pattern, min_length=4, max_length=80)
    merchant_id: str = Field(..., min_length=8, max_length=25)


class PayerInner(BaseModel):
    payer_id: str = Field(..., min_length=8, max_length=25)
    name: str = Field(..., min_length=2, max_length=80)
    surname: str = Field(..., min_length=2, max_length=80)
    email_address: str = Field(..., regex=email_pattern, min_length=4, max_length=80)


class CaptureInner(BaseModel):
    id: str = Field(..., min_length=8, max_length=25)
    status: str = Field(..., min_length=4, max_length=25)
    amount: UnitAmountInner = Field(...)
    final_capture: bool = Field(...)


class CreatePaypalOrderResponse(OrderResponseBase):
    payee: PayeeInner = Field(...)
    approve_link: LinkInner = Field(...)
    capture_link: LinkInner = Field(...)


class CreatePaypalOrderMinimalResponse(BaseModel):
    id: str = Field(..., min_length=8, max_length=25)
    status: str = Field(..., min_length=4, max_length=25)
    approve_link: LinkInner = Field(...)
    capture_link: LinkInner = Field(...)


class CapturePaypalOrderResponse(OrderResponseBase):
    payer: PayerInner = Field(...)
    capture: CaptureInner = Field(...)
    refund_link: LinkInner = Field(...)


class RealPaypalAmounts(BaseModel):
    gross_amount: UnitAmountInner = Field(...)
    paypal_fee: UnitAmountInner = Field(...)
    net_amount: UnitAmountInner = Field(...)
