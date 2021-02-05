import datetime
import os

from loguru import logger
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, BigInteger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GuildSettings(Base):
    __tablename__ = 'guild_settings'
    guild_id = Column(BigInteger, primary_key=True, unique=True)
    server_name = Column(String)
    prefix = Column(String)
    region = Column(String)
    owner_id = Column(BigInteger)
    is_premium = Column(Boolean)


class SecretSanta(Base):
    __tablename__ = "secret_santa"
    id = Column(Integer, autoincrement=True, primary_key=True)
    secret_santa_id = Column(Integer, ForeignKey('secret_santa_settings.id'))
    user_id = Column(BigInteger, nullable=False)
    assigned_user_id = Column(BigInteger)
    address = Column(String, nullable=True)
    note = Column(Text)


class SecretSantaSettings(Base):
    __tablename__ = "secret_santa_settings"
    id = Column(Integer, autoincrement=True, primary_key=True)
    guild_id = Column(BigInteger)
    event_type_id = Column(Integer, ForeignKey('event_type.id'))
    channel_id = Column(BigInteger)
    message_id = Column(BigInteger)
    organizer_id = Column(BigInteger, nullable=False)
    budget = Column(String)
    ended = Column(Boolean)


class EventType(Base):
    __tablename__ = "event_type"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String)
    address_required = Column(Boolean, default=False)


if __name__ == '__main__':
    # Create an engine that stores data in the local directory's
    # sqlalchemy_example.db file.
    # HOST = auth.get('database', 'HOST')
    # USERNAME = auth.get('database', 'USERNAME')
    # PASSWORD = auth.get('database', 'PASSWORD')
    # DATABASE = auth.get('database', 'DATABASE')
    engine = create_engine(os.environ["DATABASE_URL"])
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    Base.metadata.create_all(bind=engine)
    logger.success("Created Database Tables")
