"""create refresh_tokens table

Revision ID: ce6b09c779e0
Revises: 3b9771039e7f
Create Date: 2026-04-04 20:50:08.356956

"""

from typing import Sequence, Union

from alembic import op

revision: str = "ce6b09c779e0"
down_revision: Union[str, Sequence[str], None] = "3b9771039e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE refresh_tokens (
            id          CHAR(26) PRIMARY KEY,
            player_id   CHAR(26) NOT NULL REFERENCES players(id) ON DELETE CASCADE,
            token_hash  VARCHAR(64) NOT NULL UNIQUE,
            expires_at  TIMESTAMPTZ NOT NULL,
            revoked_at  TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX idx_refresh_tokens_player_id
        ON refresh_tokens(player_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
