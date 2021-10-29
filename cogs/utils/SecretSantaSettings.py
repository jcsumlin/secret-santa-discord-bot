from .database import Database
from create_databases import SecretSantaSettings


class SecretSantaSettingsModel(Database):
    def __init__(self):
        super().__init__()

    async def add(self, data: dict):
        new = SecretSantaSettings(
            guild_id=data["guild"].id,
            event_type_id=data["event_type"],
            channel_id=data["channel"].id,
            message_id=data["message"].id,
            organizer_id=data["organizer"].id,
            budget=data["budget"],
            ended=False
        )
        self.session.add(new)
        self.session.commit()
        return new

    async def save(self):
        return self.session.commit()

    async def get_by_ids(self, guild_id: int, channel_id: int, message_id: int):
        return self.session.query(SecretSantaSettings) \
            .filter_by(guild_id=guild_id) \
            .filter_by(channel_id=channel_id) \
            .filter_by(message_id=message_id) \
            .one_or_none()

    async def get_all(self):
        return self.session.query(SecretSantaSettings).all()

    async def get_by_id(self, record_id: int):
        return self.session.query(SecretSantaSettings) \
            .filter_by(id=record_id) \
            .one_or_none()


