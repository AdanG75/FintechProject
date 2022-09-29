from redis import Redis

from core.config import settings


def get_cache_client() -> Redis:
    r_cache = Redis(host=settings.get_redis_host(), port=settings.get_redis_port())

    try:
        yield r_cache
    finally:
        r_cache.close()


