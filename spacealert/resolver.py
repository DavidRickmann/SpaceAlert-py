"""Runs the Resolution Round turn by turn.

Covers the ship, the crew and external threats. Internal threats are not
modelled yet, so battlebots find no intruders and there is nothing to repair.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from .actions import TURNS, Action, Kind
from .player import Bots, Player
from .ship import (
    BATTLEBOT_STATIONS,
    LOWER_BLUE,
    LOWER_WHITE,
    PULSE_CANNON_STRENGTH,
    UPPER_RED,
    UPPER_WHITE,
    ZONES,
    Deck,
    Ship,
    Station,
    Zone,
)
from .threats import ExternalThreat
from .trajectories import TRAJECTORIES

# Turns at whose end the computer must have been maintained, and the turns
# that maintenance counts for.
COMPUTER_CHECKS = {2: (1, 2), 5: (4, 5), 9: (8, 9)}
VISUAL_CONFIRMATION_POINTS = {1: 1, 2: 2, 3: 3, 4: 5, 5: 7}
ROCKET_STRENGTH = 3
ROCKET_RANGE = 2


def phase_of(turn: int) -> int:
    return 1 if turn <= 3 else 2 if turn <= 7 else 3


class ShipLost(Exception):
    pass


@dataclass
class Result:
    log: list[str]
    lost: str | None
    destroyed_points: int = 0
    survived_points: int = 0
    total_damage: int = 0
    worst_zone_damage: int = 0
    knocked_out: int = 0
    disabled_bots: int = 0
    visual_confirmation_points: int = 0

    @property
    def score(self) -> int | None:
        if self.lost:
            return None
        return (
            self.destroyed_points
            + self.survived_points
            - self.total_damage
            - self.worst_zone_damage
            - 2 * self.knocked_out
            - self.disabled_bots
            + self.visual_confirmation_points
        )

    def summary(self) -> str:
        if self.lost:
            return f"MISSION FAILED: {self.lost}"
        return "\n".join(
            [
                f"Threats destroyed:        +{self.destroyed_points}",
                f"Threats survived:         +{self.survived_points}",
                f"Damage to the ship:       -{self.total_damage}",
                f"Most damaged zone:        -{self.worst_zone_damage}",
                f"Crew knocked out (x2):    -{2 * self.knocked_out}",
                f"Disabled battlebots:      -{self.disabled_bots}",
                f"Visual confirmation:      +{self.visual_confirmation_points}",
                f"SCORE:                    {self.score}",
            ]
        )


@dataclass
class Game:
    crew: list[Player]
    threats: list[ExternalThreat] = field(default_factory=list)
    seed: int | None = None
    ship: Ship = field(default_factory=Ship)
    log: list[str] = field(default_factory=list)
    turn: int = 0
    lost: str | None = None
    heroic_interceptors: bool = False

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        for stack in self.ship.damage_stacks.values():
            self.rng.shuffle(stack)
        self.threats.sort(key=lambda t: t.number)

    def say(self, text: str) -> None:
        self.log.append(text)

    # -- the round -------------------------------------------------------

    def resolve(self) -> Result:
        try:
            for turn in range(1, TURNS + 1):
                self.play_turn(turn)
            self.final_turn()
        except ShipLost:
            pass
        return self.result()

    def result(self) -> Result:
        res = Result(log=self.log, lost=self.lost)
        if self.lost:
            return res
        for t in self.threats:
            if t.state == "destroyed":
                res.destroyed_points += t.card.points[1]
            elif t.state in ("survived", "active"):
                res.survived_points += t.card.points[0]
        damage = [len(self.ship.damage[z]) for z in ZONES]
        res.total_damage = sum(damage)
        res.worst_zone_damage = max(damage)
        res.knocked_out = sum(p.knocked_out for p in self.crew)
        res.disabled_bots = sum(p.bots is Bots.DISABLED for p in self.crew)
        res.visual_confirmation_points = sum(
            VISUAL_CONFIRMATION_POINTS[min(n, 5)] for n in self.ship.visual_confirmation.values()
        )
        return res

    def play_turn(self, turn: int) -> None:
        self.turn = turn
        self.say(f"== Turn {turn} ==")
        self.ship.start_turn()
        self.threats_appear()
        self.player_actions()
        self.compute_damage()
        self.threat_actions()
        if turn in COMPUTER_CHECKS:
            self.computer_check(turn)

    def final_turn(self) -> None:
        """Turn 13: no player actions, a last rocket and a last threat step."""
        self.turn = TURNS + 1
        self.say(f"== Turn {self.turn} (rocket resolution) ==")
        for p in self.crew:
            if p.in_space and not p.knocked_out:
                p.station = UPPER_RED
                self.say(f"{p.name} returns from space to the {UPPER_RED} station")
        self.compute_damage()
        self.threat_actions()
        for t in self.active_threats():
            self.say(f"{t} is left behind as the ship jumps: survived")

    def lose(self, reason: str) -> None:
        self.lost = reason
        self.say(f"!! {reason}. The ship is lost.")
        raise ShipLost(reason)

    # -- threats appear ----------------------------------------------------

    def threats_appear(self) -> None:
        for t in self.threats:
            if t.number == self.turn and t.state == "waiting":
                t.state = "active"
                self.say(f"{t} appears on {t.trajectory}")

    def active_threats(self) -> list[ExternalThreat]:
        return [t for t in self.threats if t.active]

    # -- player actions --------------------------------------------------

    def player_actions(self) -> None:
        self.heroic_interceptors = False
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
            self.heroic_interceptors = action.heroic
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
            name, strength, zone = "heavy laser cannon", self.ship.heavy_laser_strength(station.zone), station.zone
        elif station == LOWER_WHITE:
            name, strength, zone = "pulse cannon", PULSE_CANNON_STRENGTH, Zone.WHITE
        else:
            name, strength, zone = "light laser cannon", self.ship.light_laser_strength(station.zone), None
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
        zone = station.zone
        if station.deck is Deck.UPPER:
            target, source, cap, what = self.ship.shields, zone, self.ship.shield_capacity(zone), "shield"
        else:
            target, source, cap, what = self.ship.reactors, Zone.WHITE, self.ship.reactor_capacity(zone), "reactor"
        moved = max(0, min(cap - target[zone], self.ship.reactors[source]))
        self.ship.reactors[source] -= moved
        target[zone] += moved
        if not moved:
            self.say(f"{p.name}: no energy to move into the {zone.value} {what}")
            return
        if heroic:
            target[zone] += 1
        self.say(f"{p.name} charges the {zone.value} {what} to {target[zone]}")

    def refuel(self, p: Player, heroic: bool) -> None:
        if self.ship.fuel_capsules == 0:
            self.say(f"{p.name}: no fuel capsules left")
            return
        self.ship.fuel_capsules -= 1
        cap = self.ship.reactor_capacity(Zone.WHITE)
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
        elif self.ship.interceptors_lost:
            self.say(f"{p.name}: the interceptors were lost earlier in the mission")
        elif any(q.in_space and not q.knocked_out for q in self.crew):
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

    def delay_players(self, who: Callable[[Player], bool], where: str) -> None:
        names = [p.name for p in self.crew if not p.knocked_out and who(p)]
        for p in self.crew:
            if not p.knocked_out and who(p):
                p.delay_pending = True
        if names:
            self.say(f"Players {where} are delayed: {', '.join(names)}")

    def knock_out(self, p: Player, cause: str) -> None:
        p.knocked_out = True
        if p.bots is not None:
            p.bots = Bots.DISABLED
        self.say(f"{p.name} is knocked out by {cause}")

    # -- compute damage --------------------------------------------------

    def targetable(self, t: ExternalThreat) -> bool:
        if not t.active:
            return False
        if t.card.stealth and not t.revealed:
            return False
        if t.card.hidden_at_distance_3 and t.distance == 3:
            return False
        return True

    @staticmethod
    def closest(threats: list[ExternalThreat]) -> ExternalThreat | None:
        return min(threats, key=lambda t: (t.position, t.number), default=None)

    def shields_of(self, t: ExternalThreat) -> int:
        bonus = any(
            m.card.shield_bonus and m.x_done and m.state != "destroyed" for m in self.threats
        )
        return t.base_shields + (1 if bonus else 0)

    def compute_damage(self) -> None:
        hits: dict[ExternalThreat, list[int]] = defaultdict(list)
        pulse_hit: set[ExternalThreat] = set()
        rocket_hit: set[ExternalThreat] = set()
        candidates = [t for t in self.active_threats() if self.targetable(t)]

        for station, strength in self.ship.fired.items():
            if station == LOWER_WHITE:
                in_range = [t for t in candidates if t.distance <= self.ship.pulse_cannon_range()]
                for t in in_range:
                    hits[t].append(strength)
                    pulse_hit.add(t)
                self.say(f"Pulse cannon hits {self.names(in_range)}")
                continue
            heavy = station.deck is Deck.UPPER
            options = [
                t for t in candidates
                if t.zone is station.zone and not (heavy and t.card.heavy_lasers_ignore)
            ]
            target = self.closest(options)
            if target:
                hits[target].append(strength)
            self.say(f"The {station} cannon targets {target or 'nothing'}")

        if self.ship.rocket_track[1]:
            self.fire_rocket(candidates, hits, rocket_hit)

        for p in self.crew:
            if p.in_space and not p.knocked_out:
                self.interceptors_attack(p, candidates, hits)

        self.apply_hits(hits, pulse_hit, rocket_hit)
        self.ship.end_compute_damage()

    def fire_rocket(self, candidates, hits, rocket_hit) -> None:
        magnets = [t for t in candidates if t.card.rocket_magnet]
        options = magnets or [t for t in candidates if t.card.rockets and t.distance <= ROCKET_RANGE]
        target = self.closest(options)
        if target is None:
            self.say("The rocket finds no target")
        elif target.card.decoy:
            self.say(f"The rocket is wasted on the decoy {target}")
        else:
            hits[target].append(ROCKET_STRENGTH)
            rocket_hit.add(target)
            self.say(f"The rocket targets {target}")

    def interceptors_attack(self, p: Player, candidates, hits) -> None:
        in_range = [t for t in candidates if t.distance == 1]
        bonus = 1 if self.heroic_interceptors else 0
        if not in_range:
            self.say(f"{p.name}'s interceptors find no target")
        elif len(in_range) == 1 and in_range[0].card.behemoth:
            hits[in_range[0]].append(9 + bonus)
            self.say(f"{p.name}'s interceptors ram the {in_range[0]}")
            self.knock_out(p, in_range[0].card.name)
            self.ship.interceptors_lost = True
        else:
            strength = (3 if len(in_range) == 1 else 1) + bonus
            for t in in_range:
                hits[t].append(strength)
            self.say(f"{p.name}'s interceptors attack {self.names(in_range)} at strength {strength}")

    def apply_hits(self, hits, pulse_hit, rocket_hit) -> None:
        for t in self.threats:
            t.damaged_this_step = False
        for t in sorted(hits, key=lambda t: t.number):
            total = sum(hits[t])
            if t.cryoshield_up:
                t.cryoshield_up = False
                self.say(f"{t}'s cryoshield absorbs the hit and breaks")
                continue
            shields = 0 if t.card.pulse_strips_shields and t in pulse_hit else self.shields_of(t)
            dealt = total - shields
            if t.card.max_damage_per_turn is not None:
                dealt = min(dealt, t.card.max_damage_per_turn)
            if dealt > 0:
                t.damage += dealt
                t.damaged_this_step = True
            self.say(f"{t} takes {max(dealt, 0)} damage (strength {total} vs shields {shields}): {t.damage}/{t.card.hp}")
            if t.card.rocket_magnet and t in rocket_hit:
                t.base_shields += 1
                self.say(f"{t} hardens its shields to {t.base_shields}")

        destroyed = [t for t in self.active_threats() if t.damage >= t.card.hp]
        for t in destroyed:
            self.destroy(t)
        for tanker in [t for t in destroyed if t.card.leviathan]:
            self.say(f"The exploding {tanker} damages every other threat")
            for t in self.active_threats():
                t.damage += 1
                t.damaged_this_step = True
            for t in self.active_threats():
                if t.damage >= t.card.hp:
                    destroyed.append(t)
                    self.destroy(t)

        for t in sorted(destroyed, key=lambda t: t.number):
            if t.card.asteroid and t.xy_passed:
                self.say(f"The shattered {t} sprays debris")
                self.attack(t, [t.zone], t.card.asteroid * t.xy_passed)
        for t in self.active_threats():
            if t.card.nemesis and t.damaged_this_step:
                self.say(f"{t} lashes out after being hit")
                self.attack(t, ZONES, 1)

    def destroy(self, t: ExternalThreat) -> None:
        if t.state != "destroyed":
            t.state = "destroyed"
            self.say(f"{t} is destroyed")

    @staticmethod
    def names(threats: list[ExternalThreat]) -> str:
        return ", ".join(str(t) for t in threats) or "nothing"

    # -- threat actions --------------------------------------------------

    def threat_actions(self) -> None:
        for t in self.active_threats():
            if t.active:
                self.advance(t, t.speed)
        if self.ship.rocket_track[0]:
            self.ship.rocket_track = [False, True]

    def advance(self, t: ExternalThreat, squares: int) -> None:
        track = TRAJECTORIES[t.trajectory]
        start = t.position
        t.position = max(0, start - squares)
        for square in range(start - 1, t.position - 1, -1):
            if not t.active:
                return
            letter = track[square]
            if letter in "XY":
                t.xy_passed += 1
            if letter in "XYZ":
                self.threat_action(t, letter)
        if t.position == 0 and t.active:
            t.state = "survived"
            self.say(f"{t} has completed its run: survived")

    def threat_action(self, t: ExternalThreat, letter: str) -> None:
        self.say(f"{t} performs its {letter} action")
        if letter == "X":
            t.x_done = True
            if t.card.attack_bonus:
                self.say("Other threats' attacks are boosted by 1")
            if t.card.shield_bonus:
                self.say("All threats gain 1 shield point")
        for effect in getattr(t.card, letter.lower()):
            effect(self, t)

    def attack(self, t: ExternalThreat, zones: list[Zone], strength: int, ignore_shields: bool = False) -> None:
        boosted = any(
            s.card.attack_bonus and s.x_done and s.state != "destroyed" and s is not t
            for s in self.threats
        )
        strength += 1 if boosted else 0
        if strength <= 0:
            return
        for zone in [z for z in ZONES if z in zones]:
            absorbed = 0 if ignore_shields else min(self.ship.shields[zone], strength)
            self.ship.shields[zone] -= absorbed
            dealt = strength - absorbed
            if t.card.double_damage:
                dealt *= 2
            self.say(
                f"{t} attacks the {zone.value} zone with {strength}: "
                f"shields absorb {absorbed}, {dealt} damage"
            )
            self.damage_zone(zone, dealt)

    def damage_zone(self, zone: Zone, points: int) -> None:
        for _ in range(points):
            tile = self.ship.draw_damage(zone)
            if tile is None:
                self.lose(f"The {zone.value} zone takes a seventh damage")
            self.say(f"  {zone.value} zone damaged: {tile.value}")

    def computer_check(self, turn: int) -> None:
        if self.ship.computer_maintained & set(COMPUTER_CHECKS[turn]):
            return
        self.say("Computer not maintained: everyone on board is delayed")
        for p in self.crew:
            if not p.in_space and not p.knocked_out:
                p.delay_pending = True
