from connect4.core.exceptions import ColumnFullError, InvalidMoveError
from connect4.core.models import Player

COLUMNS = 7
ROWS = 6
WIN_LENGTH = 4


class Board:
    """7×6 Connect 4 board. Columns are stored bottom-up."""

    __slots__ = ("_grid",)

    def __init__(self) -> None:
        self._grid: list[list[Player]] = [[] for _ in range(COLUMNS)]

    def drop(self, column: int, player: Player) -> int:
        """Drop a piece into *column*. Returns the row where it landed."""
        if column < 0 or column >= COLUMNS:
            raise InvalidMoveError(f"Column {column} is out of range (0-{COLUMNS - 1})")
        col = self._grid[column]
        if len(col) >= ROWS:
            raise ColumnFullError(f"Column {column} is full")
        col.append(player)
        return len(col) - 1

    def get(self, column: int, row: int) -> Player | None:
        """Return the player at (column, row), or None if empty."""
        col = self._grid[column]
        if row < len(col):
            return col[row]
        return None

    def is_column_full(self, column: int) -> bool:
        return len(self._grid[column]) >= ROWS

    @property
    def is_full(self) -> bool:
        return all(len(col) >= ROWS for col in self._grid)

    def check_winner(self) -> Player | None:
        """Return the winning player, or None if no winner yet."""
        for c in range(COLUMNS):
            for r in range(len(self._grid[c])):
                player = self._grid[c][r]
                if self._check_direction(c, r, player, 1, 0):  # horizontal
                    return player
                if self._check_direction(c, r, player, 0, 1):  # vertical
                    return player
                if self._check_direction(c, r, player, 1, 1):  # diagonal ↗
                    return player
                if self._check_direction(c, r, player, 1, -1):  # diagonal ↘
                    return player
        return None

    def _check_direction(
        self,
        c: int,
        r: int,
        player: Player,
        dc: int,
        dr: int,
    ) -> bool:
        """Check for WIN_LENGTH consecutive pieces in direction (dc, dr)."""
        for i in range(1, WIN_LENGTH):
            nc, nr = c + dc * i, r + dr * i
            if nc < 0 or nc >= COLUMNS or nr < 0 or nr >= ROWS:
                return False
            if self.get(nc, nr) != player:
                return False
        return True
