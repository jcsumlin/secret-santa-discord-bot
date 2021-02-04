"""seed guild settings

Revision ID: 61043123657a
Revises: 
Create Date: 2021-02-04 00:29:21.120272

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.sql import table, column
from sqlalchemy import String, BigInteger, Boolean

revision = '61043123657a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    guild_settings = table('guild_settings',
                           column('guild_id', BigInteger),
                           column('server_name', String),
                           column('prefix', String),
                           column('region', String),
                           column('owner_id', BigInteger),
                           column('is_premium', Boolean),
                           )
    op.bulk_insert(guild_settings,
                   [
                       {
                           "guild_id": 593887030216228973,
                           "server_name": "Bot Playground",
                           "prefix": "!",
                           "region": "(us_central,us-central)",
                           "owner_id": 204792579881959424,
                           "is_premium": False
                       }
                   ]
                   )

def downgrade():
    pass
