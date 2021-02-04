"""seed event types

Revision ID: 0311eb0fc2e6
Revises: 61043123657a
Create Date: 2021-02-04 14:27:03.847005

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean

# revision identifiers, used by Alembic.
revision = '0311eb0fc2e6'
down_revision = '61043123657a'
branch_labels = None
depends_on = None


def upgrade():
    guild_settings = table('event_type',
                           column('id', Integer),
                           column('name', String),
                           column('address_required', Boolean),
                       )
    op.bulk_insert(guild_settings,
                   [
                       {
                           "id": 1,
                           "name": "Virtual Gift Exchange",
                           "address_required": False
                       },
                       {
                           "id": 2,
                           "name": "Shipped Gift Exchange",
                           "address_required": True
                       }
                   ]
                   )


def downgrade():
    pass
