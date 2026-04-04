import pytest

from connect4.core.exceptions import ColumnFullError, GameOverError
from connect4.core.game import Game
from connect4.core.models import GameStatus, Player


class TestPlay:
    def test_first_move_is_player_one(self) -> None:
        game = Game()
        assert game.current_player == Player.ONE
        game.play(0)
        assert game.current_player == Player.TWO

    def test_alternating_turns(self) -> None:
        game = Game()
        for i in range(6):
            expected = Player.ONE if i % 2 == 0 else Player.TWO
            assert game.current_player == expected
            game.play(i)

    def test_moves_recorded(self) -> None:
        game = Game()
        game.play(3)
        game.play(4)
        game.play(3)
        assert game.moves == [3, 4, 3]

    def test_column_full_raises(self) -> None:
        game = Game()
        # Fill col 0 by alternating: P1→col0, P2→col0, ...
        # This gives col0 = [P1,P2,P1,P2,P1,P2] — no vertical 4-in-a-row
        for _ in range(6):
            game.play(0)
        with pytest.raises(ColumnFullError):
            game.play(0)


class TestWin:
    def test_horizontal_win(self) -> None:
        game = Game()
        # P1: 0,1,2,3 — P2: 0,1,2 (stacking on same cols, row 1)
        # Actually, let's do a proper game:
        # P1 plays cols 0,1,2,3 on row 0, P2 plays cols 0,1,2 on row 1
        moves = [0, 0, 1, 1, 2, 2, 3]  # P1 wins horizontally on row 0
        for col in moves:
            game.play(col)
        assert game.status == GameStatus.WON
        assert game.winner == Player.ONE

    def test_vertical_win(self) -> None:
        game = Game()
        # P1 stacks column 0, P2 plays column 1
        moves = [0, 1, 0, 1, 0, 1, 0]  # P1 wins vertically in col 0
        for col in moves:
            game.play(col)
        assert game.status == GameStatus.WON
        assert game.winner == Player.ONE

    def test_play_after_win_raises(self) -> None:
        game = Game()
        moves = [0, 1, 0, 1, 0, 1, 0]  # P1 wins
        for col in moves:
            game.play(col)
        with pytest.raises(GameOverError):
            game.play(2)

    def test_player_two_can_win(self) -> None:
        game = Game()
        # P1 plays col 6 as throwaway, P2 wins horizontally
        moves = [6, 0, 6, 1, 6, 2, 5, 3]  # P2 wins on row 0 cols 0-3
        for col in moves:
            game.play(col)
        assert game.status == GameStatus.WON
        assert game.winner == Player.TWO


class TestDraw:
    def test_draw(self) -> None:
        """Fill the board without any four-in-a-row."""
        game = Game()
        # Target board (groups-of-2 pattern, no 4-in-a-row in any direction):
        #   col 0: [1,1,2,2,1,1]  col 1: [2,2,1,1,2,2]
        #   col 2: [1,1,2,2,1,1]  col 3: [2,2,1,1,2,2]
        #   col 4: [1,1,2,2,1,1]  col 5: [2,2,1,1,2,2]
        #   col 6: [1,2,1,2,1,2]
        # Fill column pairs (0,1), (2,3), (4,5) then col 6 alone.
        # Each pair: a,b,a,b,b,a,b,a,a,b,a,b  (12 moves, 6 P1 + 6 P2)
        moves = [
            0,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            0,
            1,
            0,
            1,  # cols 0-1
            2,
            3,
            2,
            3,
            3,
            2,
            3,
            2,
            2,
            3,
            2,
            3,  # cols 2-3
            4,
            5,
            4,
            5,
            5,
            4,
            5,
            4,
            4,
            5,
            4,
            5,  # cols 4-5
            6,
            6,
            6,
            6,
            6,
            6,  # col 6
        ]
        for col in moves:
            game.play(col)

        assert game.status == GameStatus.DRAW
        assert game.winner is None


class TestReplay:
    def test_replay_produces_same_board(self) -> None:
        game = Game()
        moves = [0, 1, 0, 1, 0, 1]
        for col in moves:
            game.play(col)

        board = game.replay()
        # Verify the replayed board matches
        for col in range(7):
            for row in range(6):
                assert board.get(col, row) == game.board.get(col, row)

    def test_replay_after_win(self) -> None:
        game = Game()
        moves = [0, 1, 0, 1, 0, 1, 0]  # P1 wins vertically
        for col in moves:
            game.play(col)

        board = game.replay()
        assert board.check_winner() == Player.ONE


class TestStatus:
    def test_initial_status(self) -> None:
        game = Game()
        assert game.status == GameStatus.IN_PROGRESS
        assert game.winner is None

    def test_in_progress_during_play(self) -> None:
        game = Game()
        game.play(0)
        game.play(1)
        assert game.status == GameStatus.IN_PROGRESS
