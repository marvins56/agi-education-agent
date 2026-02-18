"""merge heads

Revision ID: e0a2c7f1eddf
Revises: 009_user_llm_settings, 5909f1fc5982
Create Date: 2026-02-18 21:35:05.049272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0a2c7f1eddf'
down_revision: Union[str, None] = ('009_user_llm_settings', '5909f1fc5982')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
