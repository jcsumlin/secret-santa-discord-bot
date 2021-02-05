import os
from configparser import ConfigParser

from .database import Database
from create_databases import GuildSettings

class GuildSettingsModel(Database):
    def __init__(self):
        super().__init__()

    async def add(self, guild_id: int, server_name: str, region: str, owner_id: int):
        new = GuildSettings(
            guild_id=guild_id,
            server_name=server_name,
            prefix=os.environ["PREFIX"],
            region=region,
            owner_id=owner_id,
            is_premium=False
        )
        self.session.add(new)
        return self.session.commit()

    async def get_by_id(self, guild_id:int):
        return self.session.query(GuildSettings).filter_by(guild_id=guild_id).one_or_none()



