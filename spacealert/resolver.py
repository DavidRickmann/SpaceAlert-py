"""Runs the Resolution Round turn by turn.

This first version covers the ship and the crew. Threats are not modelled
yet, so weapons fire at nothing and battlebots find no intruders; the turn
structure leaves a place for each threat step.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .actions import TURNS, Action, Kind
from .player import Bots, Player
from .ship import (
    BATTLEBOT_STATIONS,
    HEAVY_LASER_STRENGTH,
    LIGHT_LASER_STRENGTH,
    LOWER_BLUE,
    LOWER_WHITE,
    PULSE_CANNON_STRENGTH,
    REACTOR_CAPACITY,
    SHIELD_CAPACITY,
    UPPER_RED,
    UPPER_WHITE,
    Deck,
    Ship,
    Station,
    Zone,
)

# Turns at whose end the computer must have been maintained, and the turns
# that maintenance counts for.
COMPUTER_CHECKS = {2: (1, 2), 5: (4, 5), 9: (8, 9)}
VISUAL_CONFIRMATION_POINTS = {1: 1, 2: 2, 3: 3, 4: 5, 5: 7}


def phase_of(turn: int) -> int:
    return 1 if turn <= 3 else 2 if turn <= 7 else 3


@dataclass
class Result:
    log: list[str]
    visual_confirmation_points: int
    knocked_out: int
    disabled_bots: int

    @property
    def score(self) -> int:
        return self.visual_confirmation_points - 2 * self.knocked_out - self.disabled_bots


@dataclass
class Game:
    crew: list[Player]
    ship: Ship = field(default_factory=Ship)
    log: list[str] = field(default_factory=list)
    turn: int = 0

    def say(self, text: str) -> None:
        self.log.append(text)

    # -- the round -------------------------------------------------------

    def resolve(self) -> Result:
        for turn in range(1, TURNS + 1):
            self.play_turn(turn)
        self.final_turn()
        return Result(
            log=self.log,
            visual_confirmation_points=sum(
                VISUAL_CONFIRMATION_POINTS[n] for n in self.ship.visual_confirmation.values()
            ),
            knocked_out=sum(p.knocked_out for p in self.crew),
            disabled_bots=sum(p.bots is Bots.DISABLED for p in self.crew),
        )

    def play_turn(self, turn: int) -> None:
        self.turn = turn
        self.say(f"== Turn {turn} ==")
        self.ship.start_turn()
        self.player_actions()
        self.compute_damage()
        self.threat_actions()
        if turn in COMPUTER_CHECKS:
            self.computer_check(turn)

    def final_turn(self) -> None:
        """Turn 13: no player actions, a last rocket and a last threat step."""
        self.turn = TURNS + 1
        self.say(f"== Turn {self.turn} (rocket resolution) ==")
        self.compute_damage()
        for p in self.crew:
            if p.in_space:
                p.station = UPPER_RED
                self.say(f"{p.name} returns from space to the {UPPER_RED} station")
        self.threat_actions()

    # -- player actions --------------------------------------------------

    def player_actions(self) -> None:
        for p in self.crew:
            if p.knocked_out:
                continue
            if p.delay_pending:
                p.delay_pending = False
                p.shift_from(self.turn)
            self.perform(p, p.action(self.turn))
        self.resolve_visual_confirmation()

    def perform(self, p: Player, action: Action | None) -> None:
        if p.in_space:
            self.act_in_space(p, action)
            return
        if action is None:
            return
        if action.tripped:
            self.say(f"{p.name} tripped: next action delayed")
            p.delay_pending = True
        if action.is_move:
            self.move(p, action)
        elif action.kind is Kind.A:
            self.action_a(p, action.heroic)
        elif action.kind is Kind.B:
            self.action_b(p, action.heroic)
        elif action.kind is Kind.C:
            self.action_c(p)
        elif action.kind is Kind.BOT:
            self.say(f"{p.name}: battlebot action has no effect (no intruder)")

    def act_in_space(self, p: Player, action: Action | None) -> None:
        if action is not None and action.kind is Kind.BOT:
            self.say(f"{p.name} stays out in the interceptors")
            return
        if action is not None:
            # Anything else is delayed, leaving an empty turn to fly home on.
            p.shift_from(self.turn)
            self.say(f"{p.name}'s {action} is delayed while returning from space")
        p.station = UPPER_RED
        self.say(f"{p.name} returns from space to the {UPPER_RED} station")

    def move(self, p: Player, action: Action) -> None:
        if action.kind is Kind.HEROIC_MOVE:
            p.station = action.target
        elif action.kind is Kind.LIFT:
            zone = p.station.zone
            if zone in self.ship.gravolifts_used or zone in self.ship.damaged_gravolifts:
                p.delay_pending = True
                self.say(f"{p.name} squeezes into a busy or damaged gravolift: next action delayed")
            self.ship.gravolifts_used.add(zone)
            p.station = p.station.other_deck()
        else:
            p.station = p.station.moved(action.direction)
        self.say(f"{p.name} moves to the {p.station} station")

    def action_a(self, p: Player, heroic: bool) -> None:
        station = p.station
        bonus = 1 if heroic else 0
        if station in self.ship.fired:
            self.say(f"{p.name}: the weapon at {station} has already fired this turn")
            return
        if station.deck is Deck.UPPER:
            name, strength, zone = "heavy laser cannon", HEAVY_LASER_STRENGTH[station.zone], station.zone
        elif station == LOWER_WHITE:
            name, strength, zone = "pulse cannon", PULSE_CANNON_STRENGTH, Zone.WHITE
        else:
            name, strength, zone = "light laser cannon", LIGHT_LASER_STRENGTH, None
        if zone is not None:
            if self.ship.reactors[zone] == 0:
                self.say(f"{p.name}: no energy in the {zone.value} reactor to fire the {name}")
                return
            self.ship.reactors[zone] -= 1
        self.ship.fired[station] = strength + bonus
        self.say(f"{p.name} fires the {station} {name} (strength {strength + bonus})")

    def action_b(self, p: Player, heroic: bool) -> None:
        station = p.station
        if station == LOWER_WHITE:
            self.refuel(p, heroic)
            return
        if station.deck is Deck.UPPER:
            target, store, source, cap, what = self.ship.shields, station.zone, station.zone, SHIELD_CAPACITY[station.zone], "shield"
        else:
            target, store, source, cap, what = self.ship.reactors, station.zone, Zone.WHITE, REACTOR_CAPACITY[station.zone], "reactor"
        moved = max(0, min(cap - target[store], self.ship.reactors[source]))
        self.ship.reactors[source] -= moved
        target[store] += moved
        if moved and heroic:
            target[store] += 1
        self.say(f"{p.name} charges the {station.zone.value} {what} to {target[store]}")

    def refuel(self, p: Player, heroic: bool) -> None:
        if self.ship.fuel_capsules == 0:
            self.say(f"{p.name}: no fuel capsules left")
            return
        self.ship.fuel_capsules -= 1
        cap = REACTOR_CAPACITY[Zone.WHITE]
        added = max(0, cap - self.ship.reactors[Zone.WHITE])
        self.ship.reactors[Zone.WHITE] += added
        if added and heroic:
            self.ship.reactors[Zone.WHITE] += 1
        self.say(
            f"{p.name} refuels the central reactor to {self.ship.reactors[Zone.WHITE]} "
            f"({self.ship.fuel_capsules} capsules left)"
        )

    def action_c(self, p: Player) -> None:
        station = p.station
        if station == UPPER_RED:
            self.launch_interceptors(p)
        elif station == UPPER_WHITE:
            self.ship.computer_maintained.add(self.turn)
            self.say(f"{p.name} maintains the computer")
        elif station in BATTLEBOT_STATIONS:
            self.activate_bots(p, station)
        elif station == LOWER_WHITE:
            p.visual_confirmation_turn = self.turn  # counted after everyone has acted
        elif station == LOWER_BLUE:
            self.launch_rocket(p)

    def launch_interceptors(self, p: Player) -> None:
        if p.bots is not Bots.ACTIVE:
            self.say(f"{p.name}: cannot take off without an active battlebot squad")
        elif any(q.in_space for q in self.crew):
            self.say(f"{p.name}: the interceptors are already out")
        else:
            p.station = None
            self.say(f"{p.name} takes off in the interceptors")

    def activate_bots(self, p: Player, station: Station) -> None:
        if p.bots is Bots.DISABLED:
            p.bots = Bots.ACTIVE
            self.say(f"{p.name} reactivates their battlebots")
        elif p.bots is Bots.ACTIVE:
            self.say(f"{p.name}: already leading active battlebots")
        elif station in self.ship.battlebots_in_storage:
            self.ship.battlebots_in_storage.remove(station)
            p.bots = Bots.ACTIVE
            self.say(f"{p.name} activates the battlebots at the {station} station")
        else:
            self.say(f"{p.name}: the battlebots here have already been taken")

    def launch_rocket(self, p: Player) -> None:
        if self.ship.rockets == 0:
            self.say(f"{p.name}: no rockets left")
        elif self.ship.rocket_track[0]:
            self.say(f"{p.name}: a rocket has already been launched this turn")
        else:
            self.ship.rockets -= 1
            self.ship.rocket_track[0] = True
            self.say(f"{p.name} launches a rocket ({self.ship.rockets} left)")

    def resolve_visual_confirmation(self) -> None:
        lookers = [p for p in self.crew if p.visual_confirmation_turn == self.turn]
        if not lookers:
            return
        phase = phase_of(self.turn)
        best = self.ship.visual_confirmation.get(phase, 0)
        if len(lookers) > best:
            self.ship.visual_confirmation[phase] = len(lookers)
        names = ", ".join(p.name for p in lookers)
        self.say(f"Visual confirmation by {names} (phase {phase} best: {self.ship.visual_confirmation[phase]})")

    # -- compute damage and threats (threats to come) --------------------

    def compute_damage(self) -> None:
        if self.ship.rocket_track[1]:
            self.say("The rocket finds no target")
        for p in self.crew:
            if p.in_space:
                self.say(f"{p.name}'s interceptors find no target")
        self.ship.end_compute_damage()

    def threat_actions(self) -> None:
        if self.ship.rocket_track[0]:
            self.ship.rocket_track = [False, True]

    def computer_check(self, turn: int) -> None:
        if self.ship.computer_maintained & set(COMPUTER_CHECKS[turn]):
            return
        self.say("Computer not maintained: everyone on board is delayed")
        for p in self.crew:
            if not p.in_space and not p.knocked_out:
                p.delay_pending = True
