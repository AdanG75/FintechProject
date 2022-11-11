from typing import Union, Optional

from redis import Redis

from core.cache import is_the_same


def check_performer_in_cache(
        r: Redis,
        identifier: Union[str, int],
        actual_performer: Union[str, int]
) -> Optional[bool]:
    above_performer = r.get(f'PFR-{identifier}')
    if above_performer is None:
        return None
    else:
        return is_the_same(above_performer, actual_performer)
