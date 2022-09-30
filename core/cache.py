from typing import Union, List

from redis import Redis

from core.config import settings
from db.orm.exceptions_orm import cache_exception

CACHE_TIME = 180


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
