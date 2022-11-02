from sqlalchemy.orm import Session

from db.orm.markets_orm import get_all_markets as db_get_all_markets
from db.orm.users_orm import get_user_by_id
from schemas.market_base import MarketBasicDisplay
from schemas.market_complex import MarketSimpleDisplay, MarketSimpleListDisplay
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
