"""create initial tables

Revision ID: da41918033c1
Revises: 4c9be0b2e8e0
Create Date: 2025-11-20 18:21:13.999064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da41918033c1'
down_revision: Union[str, Sequence[str], None] = '4c9be0b2e8e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
