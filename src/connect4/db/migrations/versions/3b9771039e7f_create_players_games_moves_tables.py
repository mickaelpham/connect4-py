"""create players games moves tables

Revision ID: 3b9771039e7f
Revises:
Create Date: 2026-04-04 20:04:09.611208

"""

from typing import Sequence, Union

from alembic import op

revision: str = "3b9771039e7f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE players (
            id          CHAR(26) PRIMARY KEY,
            username    VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE games (
            id          CHAR(26) PRIMARY KEY,
            player1_id  CHAR(26) NOT NULL REFERENCES players(id),
            player2_id  CHAR(26) REFERENCES players(id),
            status      VARCHAR(20) NOT NULL DEFAULT 'waiting',
            winner_id   CHAR(26) REFERENCES players(id),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE moves (
            id          CHAR(26) PRIMARY KEY,
            game_id     CHAR(26) NOT NULL REFERENCES games(id),
            player_id   CHAR(26) NOT NULL REFERENCES players(id),
            "column"    SMALLINT NOT NULL,
            move_number SMALLINT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (game_id, move_number)
        )
    """)

    op.execute("""
        CREATE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON players
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)

    op.execute("""
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON games
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON games")
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON players")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")
    op.execute("DROP TABLE IF EXISTS moves")
    op.execute("DROP TABLE IF EXISTS games")
    op.execute("DROP TABLE IF EXISTS players")
