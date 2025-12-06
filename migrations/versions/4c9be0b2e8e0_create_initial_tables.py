"""create initial tables

Revision ID: 4c9be0b2e8e0
Revises: 9b9a8c59ef2b
Create Date: 2025-11-20 18:18:10.850761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c9be0b2e8e0'
down_revision: Union[str, Sequence[str], None] = '9b9a8c59ef2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
