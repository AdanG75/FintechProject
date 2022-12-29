from enum import Enum


class RequestType(Enum):
    main: str = "main"
    reload: str = "reload"
    alias: str = "alias"
    update: str = "update"
