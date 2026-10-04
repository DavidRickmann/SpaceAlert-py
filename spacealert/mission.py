"""Reading a mission file: trajectories, threats and the crew's action boards.

    # Trajectories for the red, white and blue zones.
    trajectories: T1 T4 T7

    # When and where each threat appeared: turn, zone, card name or code.
    threat: 1 red Fighter
    threat: 4 blue SE1-01

    # Action boards, captain first. See spacealert/actions.py for notation.
    Alice: red lift C | bot C - - | bot - - - -

Anything after `#` is a comment.
"""

from __future__ import annotations

from .actions import parse_board
from .player import Player
from .resolver import Game
from .ship import ZONES, Zone
from .threats import ExternalThreat, find_card
from .trajectories import parse_trajectory


def parse_mission(text: str, seed: int | None = None) -> Game:
    trajectories: dict[Zone, str] | None = None
    threat_lines: list[tuple[int, str]] = []
    crew: list[Player] = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        key, sep, rest = line.partition(":")
        if not sep:
            raise ValueError(f"Line {number}: expected 'something: ...'")
        key, rest = key.strip(), rest.strip()
        try:
            if key.lower() == "trajectories":
                names = rest.split()
                if len(names) != 3:
                    raise ValueError("give three trajectories, for red, white and blue")
                trajectories = dict(zip(ZONES, (parse_trajectory(n) for n in names)))
            elif key.lower() == "threat":
                threat_lines.append((number, rest))
            else:
                crew.append(Player(key, parse_board(rest)))
        except ValueError as e:
            raise ValueError(f"Line {number}: {e}") from None

    threats = []
    for number, rest in threat_lines:
        try:
            turn, zone, card = rest.split(None, 2)
            if trajectories is None:
                raise ValueError("list the trajectories before any threats")
            zone = Zone(zone.lower())
            threats.append(ExternalThreat(find_card(card), int(turn), zone, trajectories[zone]))
        except ValueError as e:
            raise ValueError(f"Line {number}: {e}") from None
    return Game(crew, threats, seed=seed)
