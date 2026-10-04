# SpaceAlert
A companion tool for playing the board game Space Alert: enter everyone's
action boards after the Action Round and let it run the Resolution Round.

## Status
- [x] Ship and crew: movement, gravolifts, cannons, energy, battlebots,
      interceptors, rockets, computer maintenance, delays, heroic actions,
      visual confirmation
- [ ] External threats and damage
- [ ] Internal threats
- [ ] Entering boards through a friendlier interface
- [ ] Characters, specialisations and experience (New Frontier)

## Try it
    python -m spacealert examples/boards.txt
    python -m pytest

Board notation is described in `spacealert/actions.py`.

The earlier auto-resolver prototype lives in `archive/`.
Rules notes, threat data and assets from the old Flash resolver are in `Reference/`.
