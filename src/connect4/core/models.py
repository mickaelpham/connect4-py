from enum import IntEnum, StrEnum


class Player(IntEnum):
    ONE = 1
    TWO = 2


class GameStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    DRAW = "draw"
