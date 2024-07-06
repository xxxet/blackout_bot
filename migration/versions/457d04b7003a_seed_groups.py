"""seed groups

Revision ID: 457d04b7003a
Revises: 8a7b8e7e4c3b
Create Date: 2024-07-04 18:50:22.665709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migration.seed import seed_groups, delete_groups

# revision identifiers, used by Alembic.
revision: str = '457d04b7003a'
down_revision: Union[str, None] = '8a7b8e7e4c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    seed_groups()


def downgrade() -> None:
    delete_groups()
