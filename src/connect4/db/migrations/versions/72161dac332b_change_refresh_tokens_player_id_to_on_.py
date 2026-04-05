"""change refresh_tokens.player_id to ON DELETE RESTRICT

Revision ID: 72161dac332b
Revises: 44709785e863
Create Date: 2026-04-05 08:55:22.923225

"""

from typing import Sequence, Union

from alembic import op

revision: str = "72161dac332b"
down_revision: Union[str, Sequence[str], None] = "44709785e863"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE refresh_tokens
        DROP CONSTRAINT refresh_tokens_player_id_fkey,
        ADD CONSTRAINT refresh_tokens_player_id_fkey
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE RESTRICT
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE refresh_tokens
        DROP CONSTRAINT refresh_tokens_player_id_fkey,
        ADD CONSTRAINT refresh_tokens_player_id_fkey
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
    """)
