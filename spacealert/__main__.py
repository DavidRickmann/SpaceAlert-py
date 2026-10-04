"""Resolve a mission from a file of action boards.

    python -m spacealert examples/boards.txt

Each non-blank line is `Name: <12 actions>`, in turn order starting with the
captain. Lines starting with `#` are ignored. See spacealert/actions.py for
the notation.
"""

import sys

from .actions import parse_board
from .player import Player
from .resolver import Game


def read_crew(text: str) -> list[Player]:
    crew = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, sep, board = line.partition(":")
        if not sep:
            raise SystemExit(f"Line {number}: expected 'Name: actions'")
        try:
            crew.append(Player(name.strip(), parse_board(board)))
        except ValueError as e:
            raise SystemExit(f"Line {number}: {e}")
    return crew


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(__doc__)
    with open(argv[1], encoding="utf-8") as f:
        crew = read_crew(f.read())
    result = Game(crew).resolve()
    print("\n".join(result.log))
    print()
    print(f"Visual confirmation: {result.visual_confirmation_points}")
    print(f"Knocked out: {result.knocked_out}, disabled battlebots: {result.disabled_bots}")
    print(f"Score so far (no threats yet): {result.score}")


if __name__ == "__main__":
    main(sys.argv)
