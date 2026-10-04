"""Crew members and their action boards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .actions import TURNS, Action
from .ship import UPPER_WHITE, Station


class Bots(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class Player:
    name: str
    board: list[Action | None]
    station: Station | None = UPPER_WHITE  # None while out in the interceptors
    bots: Bots | None = None
    knocked_out: bool = False
    delay_pending: bool = False
    visual_confirmation_turn: int | None = None

    @property
    def in_space(self) -> bool:
        return self.station is None

    def action(self, turn: int) -> Action | None:
        return self.board[turn - 1]

    def shift_from(self, turn: int) -> None:
        """Delay the card on `turn`: it and any cards behind it move one space later.

        Shifting stops at the first empty space; a card pushed off the end of
        the board is lost. Delaying an empty space does nothing.
        """
        carry = None
        for i in range(turn - 1, TURNS):
            carry, self.board[i] = self.board[i], carry
            if carry is None:
                return
