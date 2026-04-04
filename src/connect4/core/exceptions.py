class Connect4Error(Exception):
    """Base exception for Connect 4 game errors."""


class InvalidMoveError(Connect4Error):
    """Raised when a move is invalid (wrong turn, out-of-range column)."""


class ColumnFullError(Connect4Error):
    """Raised when attempting to drop a piece into a full column."""


class GameOverError(Connect4Error):
    """Raised when attempting to play after the game has ended."""
