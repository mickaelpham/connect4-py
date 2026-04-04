from connect4.core.board import Board
from connect4.core.exceptions import GameOverError
from connect4.core.models import GameStatus, Player


class Game:
    """Event-sourced Connect 4 game. Stores moves and derives board state."""

    __slots__ = ("_board", "_moves", "_status", "_winner")

    def __init__(self) -> None:
        self._board = Board()
        self._moves: list[int] = []
        self._status = GameStatus.IN_PROGRESS
        self._winner: Player | None = None

    @property
    def moves(self) -> list[int]:
        return list(self._moves)

    @property
    def status(self) -> GameStatus:
        return self._status

    @property
    def winner(self) -> Player | None:
        return self._winner

    @property
    def current_player(self) -> Player:
        return Player.ONE if len(self._moves) % 2 == 0 else Player.TWO

    @property
    def board(self) -> Board:
        return self._board

    def play(self, column: int) -> None:
        """Play a move in the given column for the current player."""
        if self._status != GameStatus.IN_PROGRESS:
            raise GameOverError("Game is already over")

        player = self.current_player
        self._board.drop(column, player)
        self._moves.append(column)

        winner = self._board.check_winner()
        if winner is not None:
            self._status = GameStatus.WON
            self._winner = winner
        elif self._board.is_full:
            self._status = GameStatus.DRAW

    def replay(self) -> Board:
        """Rebuild and return a new board from the move history."""
        board = Board()
        for i, column in enumerate(self._moves):
            player = Player.ONE if i % 2 == 0 else Player.TWO
            board.drop(column, player)
        self._board = board
        return board
