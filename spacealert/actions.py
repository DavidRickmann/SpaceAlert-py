"""Action cards as played on a player's action board, and how to write them down.

Board notation, one token per turn (case-insensitive, `|` between phases is
ignored):

    -        no card
    red      move one station towards the red zone
    blue     move one station towards the blue zone
    lift     take the gravolift to the other deck
    A B C    system actions
    bot      battlebot action (attack an intruder, or stay out in interceptors)
    A* B* bot*   heroic versions of A, B and the battlebot action
    @LR      heroic movement straight to a station (UR UW UB LR LW LB)

Add `!` to any token ("Oops, I tripped") to perform it as written but delay
the player's next action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ship import Station, Zone

TURNS = 12


class Kind(Enum):
    RED = "red"
    BLUE = "blue"
    LIFT = "lift"
    A = "A"
    B = "B"
    C = "C"
    BOT = "bot"
    HEROIC_MOVE = "@"


@dataclass(frozen=True)
class Action:
    kind: Kind
    heroic: bool = False
    target: Station | None = None
    tripped: bool = False

    @property
    def is_move(self) -> bool:
        return self.kind in (Kind.RED, Kind.BLUE, Kind.LIFT, Kind.HEROIC_MOVE)

    @property
    def direction(self) -> Zone:
        return Zone.RED if self.kind is Kind.RED else Zone.BLUE

    def __str__(self) -> str:
        if self.kind is Kind.HEROIC_MOVE:
            text = "@" + self.target.code
        else:
            text = self.kind.value + ("*" if self.heroic else "")
        return text + ("!" if self.tripped else "")


_SIMPLE = {
    "red": Kind.RED,
    "blue": Kind.BLUE,
    "lift": Kind.LIFT,
    "a": Kind.A,
    "b": Kind.B,
    "c": Kind.C,
    "bot": Kind.BOT,
}
_HEROIC = (Kind.A, Kind.B, Kind.BOT)


def parse_action(token: str) -> Action | None:
    token = token.strip()
    tripped = token.endswith("!")
    if tripped:
        token = token[:-1]
    if token in ("-", "."):
        if tripped:
            raise ValueError("An empty space cannot be tripped on")
        return None
    if token.startswith("@"):
        return Action(Kind.HEROIC_MOVE, heroic=True, target=Station.parse(token[1:]), tripped=tripped)
    heroic = token.endswith("*")
    if heroic:
        token = token[:-1]
    kind = _SIMPLE.get(token.lower())
    if kind is None:
        raise ValueError(f"Unknown action {token!r}")
    if heroic and kind not in _HEROIC:
        raise ValueError(f"There is no heroic version of {token!r}")
    return Action(kind, heroic=heroic, tripped=tripped)


def parse_board(text: str) -> list[Action | None]:
    tokens = [t for t in text.replace("|", " ").split()]
    if len(tokens) > TURNS:
        raise ValueError(f"A board has {TURNS} spaces, got {len(tokens)}")
    board = [parse_action(t) for t in tokens]
    return board + [None] * (TURNS - len(board))


def format_board(board: list[Action | None]) -> str:
    cells = [str(a) if a else "-" for a in board]
    return " ".join(cells[:3]) + " | " + " ".join(cells[3:7]) + " | " + " ".join(cells[7:])
