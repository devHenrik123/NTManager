from abc import ABC
from copy import deepcopy
from datetime import datetime, timedelta


class MetaObject:
    def __init__(self, id_: str, lifetime: timedelta) -> None:
        self._id: str = id_
        self._destruction_date: datetime = datetime.now() + lifetime

    @property
    def id(self) -> str:
        return self._id

    @property
    def destruction_date(self) -> datetime:
        return self._destruction_date


class MetaWorld(ABC):
    _Objects: dict[str, MetaObject] = {}

    @staticmethod
    def objects() -> list[MetaObject]:
        return list(MetaWorld._Objects.values())

    @staticmethod
    def add(obj: MetaObject) -> None:
        MetaWorld._Objects[obj.id] = obj

    @staticmethod
    def get(obj_id: str) -> MetaObject | None:
        return MetaWorld._Objects.get(obj_id, None)

    @staticmethod
    async def clean() -> None:
        now: datetime = datetime.now()
        for id_, obj in deepcopy(MetaWorld._Objects).items():
            if obj.destruction_date < now:
                del MetaWorld._Objects[id_]
