"""Resolve a mission file.

    python -m spacealert examples/mission.txt [--seed N]

See spacealert/mission.py for the file format. Damage tiles are drawn at
random; give a seed to get the same draws every time.
"""

import argparse

from .mission import parse_mission


def main() -> None:
    parser = argparse.ArgumentParser(prog="spacealert", description="Resolve a Space Alert mission.")
    parser.add_argument("mission", help="mission file")
    parser.add_argument("--seed", type=int, help="seed for drawing damage tiles")
    args = parser.parse_args()
    with open(args.mission, encoding="utf-8") as f:
        try:
            game = parse_mission(f.read(), seed=args.seed)
        except ValueError as e:
            raise SystemExit(str(e))
    result = game.resolve()
    print("\n".join(result.log))
    print()
    print(result.summary())


if __name__ == "__main__":
    main()
