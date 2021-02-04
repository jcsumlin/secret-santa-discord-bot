from loguru import logger

from .database import Database
from create_databases import SecretSanta


class SecretSantaModel(Database):
    def __init__(self):
        super().__init__()

    async def add(self, secret_santa_id: int, user_id: int, assigned_user_id: int = 0, address: str = "",
                  note: str = ""):
        new = SecretSanta(
            secret_santa_id=secret_santa_id,
            user_id=user_id,
            assigned_user_id=assigned_user_id,
            address=address,
            note=note
        )
        self.session.add(new)
        self.session.commit()
        return new

    async def save(self):
        return self.session.commit()

    async def get_by_user_id(self, user_id: int):
        return self.session.query(SecretSanta).filter_by(user_id=user_id).one_or_none()

    async def get_all(self, guild_id):
        return self.session.query(SecretSanta).filter_by(guild_id=guild_id).all()

    async def get_by_user_id_and_settings_id(self, user_id: int, settings_id: int):
        return self.session.query(SecretSanta) \
            .filter_by(user_id=user_id) \
            .filter_by(secret_santa_id=settings_id) \
            .one_or_none()

    def delete(self, record: SecretSanta):
        try:
            self.session.delete(record)
            self.session.commit()
        except Exception as e:
            logger.error(e)
            return False
        return True
