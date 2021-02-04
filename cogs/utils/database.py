import os
from configparser import ConfigParser
from datetime import datetime

import discord
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
auth = ConfigParser()
auth.read('./auth.ini')

class Database:
    def __init__(self):
        Base = declarative_base()
        HOST = auth.get('database', 'HOST')
        USERNAME = auth.get('database', 'USERNAME')
        PASSWORD = auth.get('database', 'PASSWORD')
        DATABASE = auth.get('database', 'DATABASE')
        engine = create_engine(f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}")
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

