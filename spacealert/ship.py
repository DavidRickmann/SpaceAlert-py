"""The spaceship: zones, decks, stations and the state of every system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Zone(Enum):
    RED = "red"
    WHITE = "white"
    BLUE = "blue"


class Deck(Enum):
    UPPER = "upper"
    LOWER = "lower"


# Zones in board order, left to right. Red arrows move towards index 0.
ZONES = [Zone.RED, Zone.WHITE, Zone.BLUE]


@dataclass(frozen=True)
class Station:
    zone: Zone
    deck: Deck

    @property
    def code(self) -> str:
        return self.deck.value[0].upper() + self.zone.value[0].upper()

    @classmethod
    def parse(cls, code: str) -> "Station":
        code = code.strip().upper()
        decks = {"U": Deck.UPPER, "L": Deck.LOWER}
        zones = {"R": Zone.RED, "W": Zone.WHITE, "B": Zone.BLUE}
        if len(code) != 2 or code[0] not in decks or code[1] not in zones:
            raise ValueError(f"Unknown station {code!r} (use UR, UW, UB, LR, LW or LB)")
        return cls(zones[code[1]], decks[code[0]])

    def moved(self, towards: Zone) -> "Station":
        """One step through a door towards the given side of the ship."""
        i = ZONES.index(self.zone)
        target = ZONES.index(towards)
        if i == target:
            return self
        step = 1 if target > i else -1
        return Station(ZONES[i + step], self.deck)

    def other_deck(self) -> "Station":
        deck = Deck.LOWER if self.deck is Deck.UPPER else Deck.UPPER
        return Station(self.zone, deck)

    def __str__(self) -> str:
        return f"{self.deck.value} {self.zone.value}"


UPPER_RED = Station(Zone.RED, Deck.UPPER)
UPPER_WHITE = Station(Zone.WHITE, Deck.UPPER)
UPPER_BLUE = Station(Zone.BLUE, Deck.UPPER)
LOWER_RED = Station(Zone.RED, Deck.LOWER)
LOWER_WHITE = Station(Zone.WHITE, Deck.LOWER)
LOWER_BLUE = Station(Zone.BLUE, Deck.LOWER)

HEAVY_LASER_STRENGTH = {Zone.RED: 4, Zone.WHITE: 5, Zone.BLUE: 4}
LIGHT_LASER_STRENGTH = 2
PULSE_CANNON_STRENGTH = 1
SHIELD_CAPACITY = {Zone.RED: 2, Zone.WHITE: 3, Zone.BLUE: 2}
REACTOR_CAPACITY = {Zone.RED: 3, Zone.WHITE: 5, Zone.BLUE: 3}

BATTLEBOT_STATIONS = (LOWER_RED, UPPER_BLUE)


@dataclass
class Ship:
    shields: dict[Zone, int] = field(default_factory=lambda: {z: 1 for z in ZONES})
    reactors: dict[Zone, int] = field(
        default_factory=lambda: {Zone.RED: 2, Zone.WHITE: 3, Zone.BLUE: 2}
    )
    fuel_capsules: int = 3
    rockets: int = 3
    # Rocket track: square 1 (just launched) and square 2 (deals damage).
    rocket_track: list[bool] = field(default_factory=lambda: [False, False])
    # Battlebot squads still in storage, by station.
    battlebots_in_storage: set[Station] = field(default_factory=lambda: set(BATTLEBOT_STATIONS))
    # Weapons fired this turn, with the strength they fire at.
    fired: dict[Station, int] = field(default_factory=dict)
    # Zones whose gravolift has been used this turn.
    gravolifts_used: set[Zone] = field(default_factory=set)
    damaged_gravolifts: set[Zone] = field(default_factory=set)
    computer_maintained: set[int] = field(default_factory=set)
    # Best visual confirmation per phase: number of players on one turn.
    visual_confirmation: dict[int, int] = field(default_factory=dict)

    def start_turn(self) -> None:
        self.gravolifts_used.clear()

    def end_compute_damage(self) -> None:
        """Energy leaves the cannons and a rocket that has struck is gone."""
        self.fired.clear()
        self.rocket_track[1] = False
