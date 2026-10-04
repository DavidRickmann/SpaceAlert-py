"""External threat cards from the base game, and threats in play.

A card's X, Y and Z actions are lists of effects. Each effect is a function
taking the game and the threat performing it. Rules that are not actions
(stealth, cryoshields and so on) are flags on the card, and the resolver
checks for them where they matter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .ship import ZONES, Zone
from .trajectories import TRAJECTORIES, distance

if TYPE_CHECKING:
    from .resolver import Game

Effect = Callable[["Game", "ExternalThreat"], None]


# -- effects -------------------------------------------------------------


def attack(n: int, ignore_shields: bool = False) -> Effect:
    return lambda g, t: g.attack(t, [t.zone], n, ignore_shields)


def attack_all(n: int) -> Effect:
    return lambda g, t: g.attack(t, ZONES, n)


def attack_others(n: int) -> Effect:
    return lambda g, t: g.attack(t, [z for z in ZONES if z is not t.zone], n)


def attack_zones(n: int, *zones: Zone) -> Effect:
    return lambda g, t: g.attack(t, list(zones), n)


def attack_remaining_hp(per_point: int = 1, all_zones: bool = False) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        g.attack(t, ZONES if all_zones else [t.zone], per_point * t.remaining_hp)

    return effect


def if_damaged(inner: Effect) -> Effect:
    return lambda g, t: inner(g, t) if t.damage > 0 else None


def unless_damage_at_least(k: int, inner: Effect) -> Effect:
    return lambda g, t: inner(g, t) if t.damage < k else None


def heal(n: int) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        t.damage = max(0, t.damage - n)
        g.say(f"{t} repairs to {t.damage} damage")

    return effect


def heal_half(g: Game, t: ExternalThreat) -> None:
    t.damage -= t.damage // 2
    g.say(f"{t} heals to {t.damage} damage")


def speed_up(n: int) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        t.speed_bonus += n
        g.say(f"{t} speeds up to {t.speed}")

    return effect


def shields_to(n: int) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        t.base_shields = n
        g.say(f"{t} now has {n} shield points")

    return effect


def shields_up(n: int) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        t.base_shields += n
        g.say(f"{t} now has {t.base_shields} shield points")

    return effect


def drain_shields(g: Game, t: ExternalThreat) -> None:
    for z in ZONES:
        g.ship.shields[z] = 0
    g.say(f"{t} drains all energy from the shields")


def drain_one_from_each_shield(g: Game, t: ExternalThreat) -> None:
    for z in ZONES:
        g.ship.shields[z] = max(0, g.ship.shields[z] - 1)
    g.say(f"{t} drains 1 energy from each shield")


def reveal(g: Game, t: ExternalThreat) -> None:
    t.revealed = True
    g.say(f"{t} reveals itself")


def take_damage(n: int) -> Effect:
    def effect(g: Game, t: ExternalThreat) -> None:
        t.damage += n
        g.say(f"{t} takes {n} damage ({t.damage}/{t.card.hp})")
        if t.damage >= t.card.hp:
            g.destroy(t)

    return effect


def destroy_ship(g: Game, t: ExternalThreat) -> None:
    g.lose(f"{t} destroys itself and the ship")


def delay_zone(g: Game, t: ExternalThreat) -> None:
    g.delay_players(lambda p: p.station is not None and p.station.zone is t.zone, f"in the {t.zone.value} zone")


def delay_ship(g: Game, t: ExternalThreat) -> None:
    g.delay_players(lambda p: p.station is not None, "on the ship")


def knock_out_ship(g: Game, t: ExternalThreat) -> None:
    for p in g.crew:
        if p.station is not None and not p.knocked_out:
            g.knock_out(p, str(t))


def scout_y(g: Game, t: ExternalThreat) -> None:
    g.say(f"{t} guides the other threats one square closer")
    for other in g.active_threats():
        if other is not t:
            g.advance(other, 1)


# -- cards ---------------------------------------------------------------


@dataclass(frozen=True)
class ThreatCard:
    code: str
    name: str
    points: tuple[int, int]  # (survived, destroyed)
    speed: int
    hp: int
    shields: int
    x: tuple[Effect, ...]
    y: tuple[Effect, ...]
    z: tuple[Effect, ...]
    rockets: bool = True  # can be targeted by rockets
    stealth: bool = False  # untargetable until its X action
    decoy: bool = False  # rockets are wasted on it
    cryoshield: bool = False
    pulse_strips_shields: bool = False  # Energy Cloud, Maelstrom
    max_damage_per_turn: int | None = None  # Swarm
    hidden_at_distance_3: bool = False  # satellites
    heavy_lasers_ignore: bool = False  # Scout
    attack_bonus: bool = False  # Scout: +1 to other threats' attacks after X
    shield_bonus: bool = False  # Marauder: +1 shields to all threats after X
    double_damage: bool = False  # Destroyer
    leviathan: bool = False  # 1 damage to all other threats when destroyed
    asteroid: int = 0  # attack per X/Y square passed, when destroyed
    rocket_magnet: bool = False  # Juggernaut
    behemoth: bool = False
    nemesis: bool = False

    @property
    def serious(self) -> bool:
        return self.code.startswith("S")


W, WS = (2, 4), (4, 8)  # white-symboled common / serious
Y, YS = (3, 6), (6, 12)  # yellow-symboled common / serious

CARDS = [
    # White common
    ThreatCard("E1-01", "Pulse Ball", W, 2, 5, 1, (attack_all(1),), (attack_all(1),), (attack_all(2),)),
    ThreatCard("E1-02", "Destroyer", W, 2, 5, 2, (attack(1),), (attack(2),), (attack(2),), double_damage=True),
    ThreatCard("E1-03", "Stealth Fighter", W, 3, 4, 2, (reveal,), (attack(2),), (attack(2),), stealth=True),
    ThreatCard("E1-04", "Energy Cloud", W, 2, 5, 3, (drain_shields,), (attack_others(1),), (attack_others(2),),
               pulse_strips_shields=True),
    ThreatCard("E1-05", "Gunship", W, 2, 5, 2, (attack(2),), (attack(2),), (attack(3),)),
    ThreatCard("E1-06", "Cryoshield Fighter", W, 3, 4, 1, (attack(1),), (attack(2),), (attack(2),), cryoshield=True),
    ThreatCard("E1-07", "Fighter", W, 3, 4, 2, (attack(1),), (attack(2),), (attack(3),)),
    ThreatCard("E1-08", "Armored Grappler", W, 2, 4, 3, (attack(1),), (heal(1),), (attack(4),)),
    ThreatCard("E1-09", "Amoeba", W, 2, 8, 0, (heal(2),), (heal(2),), (attack(5),), rockets=False),
    ThreatCard("E1-10", "Meteoroid", W, 5, 5, 0, (), (), (attack_remaining_hp(),), rockets=False),
    # White serious
    ThreatCard("SE1-01", "Frigate", WS, 2, 7, 2, (attack(2),), (attack(3),), (attack(4),)),
    ThreatCard("SE1-02", "Man-of-War", WS, 1, 9, 2, (attack(2), speed_up(1)), (attack(3), shields_up(1)), (attack(5),)),
    ThreatCard("SE1-03", "Leviathan Tanker", WS, 2, 8, 3, (attack(2),), (attack(2), heal(2)), (attack(2),), leviathan=True),
    ThreatCard("SE1-04", "Pulse Satellite", WS, 3, 4, 2, (attack_all(1),), (attack_all(2),), (attack_all(3),),
               hidden_at_distance_3=True),
    ThreatCard("SE1-05", "Cryoshield Frigate", WS, 2, 7, 1, (attack(2),), (attack(3),), (attack(4),), cryoshield=True),
    ThreatCard("SE1-06", "Interstellar Octopus", WS, 2, 8, 1, (if_damaged(attack_all(1)),), (if_damaged(attack_all(2)),),
               (attack_remaining_hp(2),), rockets=False),
    ThreatCard("SE1-07", "Maelstrom", WS, 2, 8, 3, (drain_shields,), (attack_others(2),), (attack_others(3),),
               pulse_strips_shields=True),
    ThreatCard("SE1-08", "Asteroid", WS, 3, 9, 0, (), (), (attack_remaining_hp(),), rockets=False, asteroid=2),
    # Yellow common
    ThreatCard("E2-01", "Kamikaze", Y, 4, 5, 2, (speed_up(1), shields_to(1)), (speed_up(1), shields_to(0)), (attack(6),)),
    ThreatCard("E2-02", "Scout", Y, 2, 3, 1, (), (scout_y,), (attack(3, ignore_shields=True),),
               heavy_lasers_ignore=True, attack_bonus=True),
    ThreatCard("E2-03", "Phantom Fighter", Y, 3, 3, 3, (reveal,), (attack(2),), (attack(3),), stealth=True, decoy=True),
    ThreatCard("E2-04", "Swarm", Y, 2, 3, 0, (attack(1),), (attack(2), attack_others(1)), (attack(3), attack_others(2)),
               rockets=False, max_damage_per_turn=1),
    ThreatCard("E2-05", "Jellyfish", Y, 2, 13, -2, (attack_all(1), heal_half), (attack_all(1), heal_half), (attack_all(2),),
               rockets=False),
    ThreatCard("E2-06", "Marauder", Y, 3, 6, 1, (), (drain_one_from_each_shield,), (attack(4),), shield_bonus=True),
    ThreatCard("E2-07", "Minor Asteroid", Y, 4, 7, 0, (), (), (attack_remaining_hp(),), rockets=False, asteroid=1),
    # Yellow serious
    ThreatCard("SE2-01", "Behemoth", YS, 2, 7, 4, (unless_damage_at_least(2, attack(2)),),
               (unless_damage_at_least(3, attack(3)),), (unless_damage_at_least(6, attack(6)),), behemoth=True),
    ThreatCard("SE2-02", "Juggernaut", YS, 1, 10, 3, (speed_up(2), attack(2)), (speed_up(2), attack(3)), (attack(7),),
               rocket_magnet=True),
    ThreatCard("SE2-03", "Psionic Satellite", YS, 2, 5, 2, (delay_zone,), (delay_ship,), (knock_out_ship,),
               hidden_at_distance_3=True),
    ThreatCard("SE2-04", "Nebula Crab", YS, 2, 7, 2, (shields_to(4),), (speed_up(2), shields_to(2)),
               (attack_zones(5, Zone.RED, Zone.BLUE),), rockets=False),
    ThreatCard("SE2-05", "Nemesis", (0, 12), 3, 9, 1, (attack(1), take_damage(1)), (attack(2), take_damage(2)),
               (destroy_ship,), nemesis=True),
    ThreatCard("SE2-06", "Major Asteroid", YS, 2, 11, 0, (), (), (attack_remaining_hp(),), rockets=False, asteroid=3),
]


def _key(text: str) -> str:
    return "".join(c for c in text.lower() if c.isalnum())


_LOOKUP = {**{_key(c.code): c for c in CARDS}, **{_key(c.name): c for c in CARDS}}


def find_card(text: str) -> ThreatCard:
    card = _LOOKUP.get(_key(text))
    if card is None:
        raise ValueError(f"Unknown external threat {text!r}")
    return card


# -- threats in play -------------------------------------------------------


@dataclass(eq=False)
class ExternalThreat:
    card: ThreatCard
    number: int  # the turn it appears, which is also its token number
    zone: Zone
    trajectory: str
    position: int = 0
    damage: int = 0
    base_shields: int = 0
    speed_bonus: int = 0
    revealed: bool = False
    cryoshield_up: bool = False
    x_done: bool = False
    xy_passed: int = 0
    state: str = "waiting"  # waiting, active, destroyed, survived
    damaged_this_step: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        self.position = len(TRAJECTORIES[self.trajectory]) - 1
        self.base_shields = self.card.shields
        self.cryoshield_up = self.card.cryoshield

    @property
    def speed(self) -> int:
        return self.card.speed + self.speed_bonus

    @property
    def distance(self) -> int:
        return distance(self.position)

    @property
    def remaining_hp(self) -> int:
        return max(0, self.card.hp - self.damage)

    @property
    def active(self) -> bool:
        return self.state == "active"

    def __str__(self) -> str:
        return f"{self.card.name} [{self.number}, {self.zone.value}]"
