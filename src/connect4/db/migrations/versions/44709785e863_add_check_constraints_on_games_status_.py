"""add check constraints on games.status and moves.column

Revision ID: 44709785e863
Revises: ce6b09c779e0
Create Date: 2026-04-05 08:47:41.830157

"""

from typing import Sequence, Union

from alembic import op

revision: str = "44709785e863"
down_revision: Union[str, Sequence[str], None] = "ce6b09c779e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE games
        ADD CONSTRAINT chk_game_status
        CHECK (status IN ('waiting', 'in_progress', 'won', 'draw'))
    """)
    op.execute("""
        ALTER TABLE moves
        ADD CONSTRAINT chk_move_column
        CHECK ("column" BETWEEN 0 AND 6)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE moves DROP CONSTRAINT chk_move_column")
    op.execute("ALTER TABLE games DROP CONSTRAINT chk_game_status")
