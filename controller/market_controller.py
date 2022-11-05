from typing import Optional

from sqlalchemy.orm import Session

from db.models.markets_db import DbMarket
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credit_by_id_market_and_id_client
from db.orm.exceptions_orm import not_values_sent_exception
from db.orm.markets_orm import get_all_markets as db_get_all_markets, get_market_by_id_market
from db.orm.users_orm import get_user_by_id
from schemas.market_base import MarketBasicDisplay, MarketComplexDisplay
from schemas.market_complex import MarketSimpleDisplay, MarketSimpleListDisplay, MarketCreditClient, CreditClientInner
from schemas.user_base import UserBase


def get_all_markets(db: Session, except_system: bool = True) -> MarketSimpleListDisplay:
    markets = db_get_all_markets(db, remove_market_system=except_system)

    if len(markets) > 0:
        users = [get_user_by_id(db, market.id_user) for market in markets]

        markets_to_display = []
        for i in range(len(markets)):
            simple_market = MarketSimpleDisplay(
                market=MarketBasicDisplay.from_orm(markets[i]),
                user=UserBase.from_orm(users[i])
            )
            markets_to_display.append(simple_market)

        market_list = MarketSimpleListDisplay(
            markets=markets_to_display
        )

    else:
        markets_dict = {"markets": markets}
        market_list = MarketSimpleListDisplay.parse_obj(markets_dict)

    return market_list


def get_market_based_on_client(db: Session, id_market: str, id_client: str) -> MarketCreditClient:
    client = get_client_by_id_client(db, id_client)
    market = get_market_by_id_market(db, id_market)

    credit = get_credit_by_id_market_and_id_client(db, market.id_market, client.id_client)
    if credit is None:
        market_credit_client = set_MarketCreditClient(client.id_client, False, None, None, market)
    else:
        market_credit_client = set_MarketCreditClient(
            id_client=client.id_client,
            have_credit=True,
            id_credit=credit.id_credit,
            type_credit=credit.type_credit,
            market=market
        )

    return market_credit_client


def set_MarketCreditClient(
        id_client: str,
        have_credit: bool,
        id_credit: Optional[int],
        type_credit: Optional[str],
        market: DbMarket
) -> MarketCreditClient:
    if have_credit and id_credit is None:
        raise not_values_sent_exception

    credit_client = CreditClientInner(
        id_client=id_client,
        have_credit=have_credit,
        id_credit=id_credit,
        type_credit=type_credit
    )

    return MarketCreditClient(
        market=MarketComplexDisplay.from_orm(market),
        credit_client=credit_client
    )
