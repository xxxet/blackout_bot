"""seed

Revision ID: 31d1c6ff6784
Revises: 972c34565a6b
Create Date: 2024-07-11 01:19:42.027571

"""
from typing import Sequence, Union

from migration.seed import delete_groups, seed_groups

# revision identifiers, used by Alembic.
revision: str = '31d1c6ff6784'
down_revision: Union[str, None] = '972c34565a6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    seed_groups()


def downgrade() -> None:
    delete_groups()
