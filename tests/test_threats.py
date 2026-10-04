from spacealert.actions import parse_board
from spacealert.player import Bots, Player
from spacealert.resolver import Game
from spacealert.ship import LOWER_BLUE, LOWER_WHITE, UPPER_RED, UPPER_WHITE, Zone
from spacealert.threats import ExternalThreat, find_card


def setup(threats, *boards, station=None):
    """threats: (card, turn, zone, trajectory) tuples. The computer is kept maintained."""
    crew = [Player(f"P{i + 1}", parse_board(b)) for i, b in enumerate(boards)]
    if station:
        for p in crew:
            p.station = station
    ts = [ExternalThreat(find_card(c), n, Zone(z), tr) for c, n, z, tr in threats]
    g = Game(crew, ts, seed=0)
    g.ship.computer_maintained.update({1, 4, 8})
    return g


def run(g, turns):
    for t in range(1, turns + 1):
        g.play_turn(t)


def test_threat_moves_and_acts():
    g = setup([("Fighter", 1, "red", "T1")])
    run(g, 2)  # speed 3 on T1 (start at 9): 9 -> 6 -> 3, passing X at 4
    t = g.threats[0]
    assert t.position == 3 and t.x_done
    assert g.ship.shields[Zone.RED] == 0 and not g.ship.damage[Zone.RED]


def test_threat_survives_after_z():
    g = setup([("Meteoroid", 1, "red", "T1")])
    run(g, 2)  # speed 5: 9 -> 4 -> 0
    t = g.threats[0]
    assert t.state == "survived"
    assert len(g.ship.damage[Zone.RED]) == 4  # 5 hp attack, 1 shield


def test_heavy_laser_hits_closest_in_zone():
    g = setup([("Gunship", 1, "white", "T7"), ("Fighter", 2, "white", "T7")], "- A")
    run(g, 2)
    gunship, fighter = g.threats
    assert gunship.damage == 3 and fighter.damage == 0


def test_shields_reduce_damage_and_destroy():
    g = setup([("Fighter", 1, "white", "T7")], "A A", "- - A*")
    run(g, 3)
    assert g.threats[0].state == "destroyed"


def test_stealth_fighter_untargetable_until_revealed():
    g = setup([("Stealth Fighter", 1, "white", "T7")], "A")
    run(g, 1)
    assert g.threats[0].damage == 0


def test_cryoshield_absorbs_first_hit():
    g = setup([("Cryoshield Fighter", 1, "white", "T7")], "A A")
    run(g, 2)
    assert g.threats[0].damage == 4  # first hit absorbed, second 5 - 1 shield


def test_pulse_cannon_strips_energy_cloud_shields():
    g = setup([("Energy Cloud", 1, "white", "T1")], "- A", station=LOWER_WHITE)
    run(g, 2)  # cloud at distance 2 on turn 2
    assert g.threats[0].damage == 1


def test_rocket_hits_next_turn():
    g = setup([("Fighter", 1, "red", "T1")], "C", station=LOWER_BLUE)
    run(g, 2)
    assert g.threats[0].damage == 1  # rocket 3 - shields 2


def test_rocket_ignores_threats_it_cannot_target():
    g = setup([("Amoeba", 1, "red", "T1")], "C", station=LOWER_BLUE)
    run(g, 2)
    assert g.threats[0].damage == 0


def interceptor_game(*cards):
    g = setup([(c, 1, z, "T1") for c, z in zip(cards, ("red", "blue"))], "- - C")
    g.crew[0].station, g.crew[0].bots = UPPER_RED, Bots.ACTIVE
    run(g, 3)  # fighters reach distance 1 after turn 2; interceptors launch on turn 3
    return g


def test_interceptors_hit_a_lone_target_hard():
    g = interceptor_game("Fighter")
    assert g.threats[0].damage == 1  # strength 3 vs shields 2


def test_interceptors_split_strength_between_targets():
    g = interceptor_game("Fighter", "Fighter")
    assert [t.damage for t in g.threats] == [0, 0]  # strength 1 each vs shields 2


def test_swarm_takes_one_damage_per_turn():
    g = setup([("Swarm", 1, "white", "T7")], "A")
    run(g, 1)
    assert g.threats[0].damage == 1


def test_destroyer_doubles_damage():
    g = setup([("Destroyer", 1, "red", "T1")])
    g.ship.shields[Zone.RED] = 0
    run(g, 3)  # X (attack 1) on turn 3: 9,7,5,3
    assert len(g.ship.damage[Zone.RED]) == 2


def test_scout_boosts_other_attacks():
    # Scout passes X on turn 3; the Fighter appears then and passes X on turn 4.
    g = setup([("Scout", 1, "red", "T1"), ("Fighter", 3, "blue", "T1")])
    run(g, 4)
    assert g.ship.shields[Zone.BLUE] == 0 and len(g.ship.damage[Zone.BLUE]) == 1


def test_marauder_gives_all_threats_a_shield():
    g = setup([("Marauder", 1, "red", "T1"), ("Gunship", 1, "white", "T7")], "- - A")
    run(g, 3)
    gunship = g.threats[1]
    assert gunship.damage == 2  # 5 - (2 + 1)


def test_leviathan_damages_other_threats_when_destroyed():
    g = setup([("Leviathan Tanker", 1, "white", "T7"), ("Fighter", 1, "red", "T7")])
    tanker, fighter = g.threats
    tanker.state = fighter.state = "active"
    tanker.damage = 7
    g.ship.fired[UPPER_WHITE] = 5
    g.compute_damage()
    assert tanker.state == "destroyed" and fighter.damage == 1


def test_asteroid_explodes_for_squares_passed():
    g = setup([("Minor Asteroid", 1, "white", "T7")])
    t = g.threats[0]
    t.state, t.xy_passed, t.damage = "active", 2, 6
    g.ship.shields[Zone.WHITE] = 0
    g.ship.fired[UPPER_WHITE] = 5
    g.compute_damage()
    assert t.state == "destroyed" and len(g.ship.damage[Zone.WHITE]) == 2


def test_behemoth_rams_interceptors():
    g = setup([("Behemoth", 1, "red", "T1")], "bot")
    t = g.threats[0]
    t.state, t.position = "active", 2
    g.crew[0].station, g.crew[0].bots = None, Bots.ACTIVE
    g.compute_damage()
    assert t.damage == 5 and g.crew[0].knocked_out and g.crew[0].bots is Bots.DISABLED


def test_seventh_damage_loses_the_game():
    g = setup([("Meteoroid", 1, "red", "T1")])
    g.ship.damage_stacks[Zone.RED] = g.ship.damage_stacks[Zone.RED][:2]
    result = g.resolve()
    assert result.lost and result.score is None


def test_scoring_after_a_clean_mission():
    g = setup([("Fighter", 1, "white", "T7")], "A A", "- - A*")
    result = g.resolve()
    assert result.lost is None
    assert result.destroyed_points == 4
    assert result.score == 4 - result.total_damage - result.worst_zone_damage


def test_find_card_by_name_or_code():
    assert find_card("man of war").code == "SE1-02"
    assert find_card("se1-02").name == "Man-of-War"
