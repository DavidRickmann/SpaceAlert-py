import pytest

from spacealert.actions import parse_board
from spacealert.player import Bots, Player
from spacealert.resolver import Game
from spacealert.ship import LOWER_WHITE, UPPER_RED, Zone


def game(*boards, maintained=True):
    """A game whose computer is kept maintained unless a test says otherwise."""
    crew = [Player(f"P{i + 1}", parse_board(b)) for i, b in enumerate(boards)]
    g = Game(crew)
    if maintained:
        g.ship.computer_maintained.update({1, 4, 8})
    return g


def test_delay_shifts_cards_until_an_empty_space():
    p = Player("P", parse_board("A B C - red"))
    p.shift_from(1)
    assert [str(a) if a else "-" for a in p.board[:5]] == ["-", "A", "B", "C", "red"]


def test_delay_pushes_last_card_off_the_board():
    p = Player("P", parse_board("A A A A A A A A A A A B"))
    p.shift_from(12)
    assert p.board[11] is None


def test_delaying_an_empty_space_does_nothing():
    p = Player("P", parse_board("- A"))
    p.shift_from(1)
    assert str(p.board[1]) == "A"


def test_second_player_in_same_gravolift_is_delayed():
    g = game("lift A", "lift A")
    g.play_turn(1)
    g.play_turn(2)
    assert g.crew[0].board[1] is not None and g.crew[1].board[1] is None
    assert str(g.crew[1].board[2]) == "A"


def test_computer_not_maintained_delays_everyone():
    g = game("- - A", maintained=False)
    g.play_turn(1)
    g.play_turn(2)
    g.play_turn(3)
    assert g.crew[0].board[2] is None and str(g.crew[0].board[3]) == "A"


def test_maintaining_computer_avoids_delay():
    g = game("- C A", maintained=False)
    for t in (1, 2, 3):
        g.play_turn(t)
    assert str(g.crew[0].board[2]) == "A"


def test_heavy_laser_uses_reactor_energy():
    g = game("A")
    g.play_turn(1)
    assert g.ship.reactors[Zone.WHITE] == 2


def test_weapon_fires_once_per_turn():
    g = game("A", "A")
    g.play_turn(1)
    assert g.ship.reactors[Zone.WHITE] == 2


def test_heroic_shield_can_exceed_capacity():
    g = game("B*")
    g.play_turn(1)
    assert g.ship.shields[Zone.WHITE] == 4


def test_heroic_bonus_needs_a_real_transfer():
    g = game("B B*")
    g.play_turn(1)
    g.play_turn(2)
    assert g.ship.shields[Zone.WHITE] == 3


def test_lateral_reactor_draws_from_central():
    g = game("lift red B")
    for t in (1, 2, 3):
        g.play_turn(t)
    assert g.ship.reactors[Zone.RED] == 3 and g.ship.reactors[Zone.WHITE] == 2


def test_interceptors_need_battlebots():
    g = game("red C")
    g.play_turn(1)
    g.play_turn(2)
    assert g.crew[0].station == UPPER_RED


def test_interceptors_take_off_with_battlebots():
    g = game("red lift C lift C | bot -")
    for t in range(1, 6):
        g.play_turn(t)
    assert g.crew[0].in_space and g.crew[0].bots is Bots.ACTIVE
    g.play_turn(6)
    assert g.crew[0].in_space
    g.play_turn(7)
    assert g.crew[0].station == UPPER_RED


def test_only_one_crew_member_in_space():
    g = game("C", "C")
    for p in g.crew:
        p.station, p.bots = UPPER_RED, Bots.ACTIVE
    g.play_turn(1)
    assert g.crew[0].in_space and not g.crew[1].in_space


def test_other_action_in_space_is_delayed_and_player_returns():
    g = game("- bot A -")
    g.crew[0].station = None
    g.crew[0].bots = Bots.ACTIVE
    g.play_turn(1)
    assert g.crew[0].station == UPPER_RED
    assert [str(a) if a else "-" for a in g.crew[0].board[:4]] == ["-", "bot", "A", "-"]


def test_staying_in_space_with_bot_action():
    g = game("bot")
    g.crew[0].station = None
    g.crew[0].bots = Bots.ACTIVE
    g.play_turn(1)
    assert g.crew[0].in_space


def test_rocket_launch_and_flight():
    g = game("lift blue C C -")
    for t in range(1, 4):
        g.play_turn(t)
    assert g.ship.rockets == 2 and g.ship.rocket_track == [False, True]
    g.play_turn(4)  # second rocket launches; first strikes and is gone
    assert g.ship.rockets == 1 and g.ship.rocket_track == [False, True]


def test_visual_confirmation_scores_best_per_phase():
    g = game("C C -", "- C C", "- C -")
    for p in g.crew:
        p.station = LOWER_WHITE
    for t in (1, 2, 3):
        g.play_turn(t)
    assert g.ship.visual_confirmation == {1: 3}


def test_full_resolve_runs():
    result = game("A B C", "lift B A").resolve()
    assert result.log[0] == "== Turn 1 =="


def test_bad_tokens_are_rejected():
    with pytest.raises(ValueError):
        parse_board("jump")
    with pytest.raises(ValueError):
        parse_board("C*")
    with pytest.raises(ValueError):
        parse_board("A " * 13)
