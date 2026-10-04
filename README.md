# SpaceAlert
A companion tool for playing the board game Space Alert: enter everyone's
action boards after the Action Round and let it run the Resolution Round.

## Status
- [x] Ship and crew: movement, gravolifts, cannons, energy, battlebots,
      interceptors, rockets, computer maintenance, delays, heroic actions,
      visual confirmation
- [x] External threats from the base game (white and yellow cards), random
      damage tiles, scoring
- [ ] Internal threats
- [ ] Entering boards through a friendlier interface
- [ ] Characters, specialisations and experience (New Frontier)

## Try it
    python -m spacealert examples/mission.txt --seed 1
    python -m pytest

The mission file format is described in `spacealert/mission.py` and the
board notation in `spacealert/actions.py`. Damage tiles are drawn at
random; pass `--seed` to repeat the same draws.

The earlier auto-resolver prototype lives in `archive/`.
Rules notes, threat data and assets from the old Flash resolver are in `Reference/`.
