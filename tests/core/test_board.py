import pytest

from connect4.core.board import COLUMNS, ROWS, Board
from connect4.core.exceptions import ColumnFullError, InvalidMoveError
from connect4.core.models import Player

P1 = Player.ONE
P2 = Player.TWO


class TestDrop:
    def test_drop_returns_row(self) -> None:
        board = Board()
        assert board.drop(0, P1) == 0
        assert board.drop(0, P2) == 1
        assert board.drop(0, P1) == 2

    def test_drop_different_columns(self) -> None:
        board = Board()
        assert board.drop(0, P1) == 0
        assert board.drop(3, P2) == 0
        assert board.drop(6, P1) == 0

    def test_drop_column_full_raises(self) -> None:
        board = Board()
        for i in range(ROWS):
            board.drop(0, P1 if i % 2 == 0 else P2)
        with pytest.raises(ColumnFullError):
            board.drop(0, P1)

    def test_drop_negative_column_raises(self) -> None:
        board = Board()
        with pytest.raises(InvalidMoveError):
            board.drop(-1, P1)

    def test_drop_column_out_of_range_raises(self) -> None:
        board = Board()
        with pytest.raises(InvalidMoveError):
            board.drop(COLUMNS, P1)


class TestGet:
    def test_get_empty_cell(self) -> None:
        board = Board()
        assert board.get(0, 0) is None

    def test_get_after_drop(self) -> None:
        board = Board()
        board.drop(3, P1)
        assert board.get(3, 0) == P1
        assert board.get(3, 1) is None

    def test_get_stacked_pieces(self) -> None:
        board = Board()
        board.drop(2, P1)
        board.drop(2, P2)
        assert board.get(2, 0) == P1
        assert board.get(2, 1) == P2


class TestIsFull:
    def test_empty_board_not_full(self) -> None:
        board = Board()
        assert not board.is_full

    def test_single_column_full(self) -> None:
        board = Board()
        for i in range(ROWS):
            board.drop(0, P1 if i % 2 == 0 else P2)
        assert board.is_column_full(0)
        assert not board.is_full

    def test_full_board(self) -> None:
        board = Board()
        for c in range(COLUMNS):
            for r in range(ROWS):
                board.drop(c, P1 if (c + r) % 2 == 0 else P2)
        assert board.is_full


class TestCheckWinner:
    def test_no_winner_empty_board(self) -> None:
        board = Board()
        assert board.check_winner() is None

    def test_horizontal_win(self) -> None:
        board = Board()
        for c in range(4):
            board.drop(c, P1)
        assert board.check_winner() == P1

    def test_vertical_win(self) -> None:
        board = Board()
        for _ in range(4):
            board.drop(0, P2)
        assert board.check_winner() == P2

    def test_diagonal_up_right_win(self) -> None:
        """Diagonal ↗: (0,0), (1,1), (2,2), (3,3)."""
        board = Board()
        # Build a staircase for P1
        # Col 0: P1
        board.drop(0, P1)
        # Col 1: P2, P1
        board.drop(1, P2)
        board.drop(1, P1)
        # Col 2: P2, P2, P1
        board.drop(2, P2)
        board.drop(2, P2)
        board.drop(2, P1)
        # Col 3: P2, P2, P2, P1
        board.drop(3, P2)
        board.drop(3, P2)
        board.drop(3, P2)
        board.drop(3, P1)
        assert board.check_winner() == P1

    def test_diagonal_down_right_win(self) -> None:
        """Diagonal ↘: (0,3), (1,2), (2,1), (3,0)."""
        board = Board()
        # Col 0: P2, P2, P2, P1
        board.drop(0, P2)
        board.drop(0, P2)
        board.drop(0, P2)
        board.drop(0, P1)
        # Col 1: P2, P2, P1
        board.drop(1, P2)
        board.drop(1, P2)
        board.drop(1, P1)
        # Col 2: P2, P1
        board.drop(2, P2)
        board.drop(2, P1)
        # Col 3: P1
        board.drop(3, P1)
        assert board.check_winner() == P1

    def test_three_in_a_row_no_win(self) -> None:
        board = Board()
        for c in range(3):
            board.drop(c, P1)
        assert board.check_winner() is None

    def test_no_false_positive_mixed(self) -> None:
        """Alternating pieces should not trigger a win."""
        board = Board()
        for c in range(6):
            board.drop(c, P1 if c % 2 == 0 else P2)
        assert board.check_winner() is None
