from .database import Database
from create_databases import EventType


class EventTypeModel(Database):
    def __init__(self):
        super().__init__()

    async def add(self, name: str, address_required: bool):
        new = EventType(
            name=name,
            address_required=address_required,
        )
        self.session.add(new)
        return self.session.commit()

    async def save(self):
        return self.session.commit()

    async def get_by_id(self, id: int):
        return self.session.query(EventType).filter_by(id=id).one_or_none()

    async def get_all(self):
        return self.session.query(EventType).all()
