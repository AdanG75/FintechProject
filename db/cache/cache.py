from typing import Union, List, Optional

from redis import Redis

from core.config import settings
from db.orm.exceptions_orm import cache_exception

CACHE_TIME = 300


def get_cache_client() -> Redis:
    r_cache = Redis(host=settings.get_redis_host(), port=settings.get_redis_port())

    try:
        yield r_cache
    finally:
        r_cache.close()


def is_the_same(radis_value: bytes, value: Union[str, int, float, bool]) -> bool:
    return radis_value.decode('utf-8') == str(value)


def batch_save(r: Redis, values: dict, seconds: int = CACHE_TIME) -> List[bool]:
    with r.pipeline() as pipe:
        for key, item in values.items():
            pipe.set(name=key, value=item, ex=seconds)

        result = pipe.execute()

    for res in result:
        if not res:
            raise cache_exception

    return result


def item_save(
        r: Redis,
        r_key: str,
        r_value: Union[float, int, str, bytes, bool],
        seconds: int = CACHE_TIME
) -> bool:
    return r.setex(r_key, time=seconds, value=r_value)


def item_get(
        r: Redis,
        r_key: str
) -> Optional[str]:
    item_value = r.get(r_key)
    if item_value is not None:
        return item_value.decode('utf-8')
    else:
        return None


def check_item_if_exist(
        r: Redis,
        r_key: str,
        value: Union[str, bytes, int, float, bool]
) -> Optional[bool]:

    r_value = r.get(r_key)
    if value is not None:
        return is_the_same(r_value, value)

    return None
