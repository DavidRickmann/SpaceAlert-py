"""Trajectory boards.

Each trajectory is written from the ship outwards: index 0 is the Z square
and the last character is the start square (S). Squares 0-4 are distance 1,
5-9 distance 2 and the rest distance 3.
"""

TRAJECTORIES = {
    "T1": "Z---X----S",
    "T2": "Z------X--S",
    "T3": "Z-Y----X---S",
    "T4": "Z---Y---X---S",
    "T5": "Z-----Y---X--S",
    "T6": "Z-Y---Y--X----S",
    "T7": "Z---Y--Y---X---S",
}


def distance(position: int) -> int:
    return min(3, position // 5 + 1)


def parse_trajectory(name: str) -> str:
    key = name.strip().upper()
    if key not in TRAJECTORIES:
        raise ValueError(f"Unknown trajectory {name!r} (use T1 to T7)")
    return key
