"""
Demo player stats and heights for the sample league.

Everything here only ADDS data and skips what already exists, so it is safe to run against a
database that holds real rows (unlike seed.py, which wipes the tables first).

Usage:
    cd pitchtrack-backend
    PYTHONPATH=. pipenv run python seed.py --stats
"""

import random

from extensions import db
from models import Match, Player, PlayerMatchStat

MATCH_MINUTES = 90
ASSIST_CHANCE = 0.7
YELLOW_CHANCE = 0.1
RED_CHANCE = 0.015

SCORER_WEIGHTS = {"Forward": 6, "Midfielder": 3, "Defender": 1, "Goalkeeper": 0}
ASSIST_WEIGHTS = {"Forward": 3, "Midfielder": 5, "Defender": 2, "Goalkeeper": 0}
HEIGHT_RANGES = {
    "Goalkeeper": (183, 196),
    "Defender": (175, 190),
    "Midfielder": (168, 184),
    "Forward": (170, 188),
}


def make_height(position, key):
    """A stable height in cm for a player, drawn from a range that fits the position."""
    low, high = HEIGHT_RANGES[position]
    return random.Random(f"height:{key}").randint(low, high)


# How a typical finish is split: mostly right foot, then left, headers and the odd penalty
GOAL_TYPE_WEIGHTS = {"right_foot_goals": 55, "left_foot_goals": 25, "headed_goals": 12, "penalty_goals": 8}


def split_goal_types(goals, key):
    """Give each of `goals` a type. The same key always produces the same split, and it adds up to `goals`."""
    rng = random.Random(f"goaltypes:{key}")
    counts = dict.fromkeys(GOAL_TYPE_WEIGHTS, 0)
    for _ in range(goals):
        counts[rng.choices(list(GOAL_TYPE_WEIGHTS), weights=list(GOAL_TYPE_WEIGHTS.values()))[0]] += 1
    return counts


def _pick(rng, players, weights_by_position):
    weights = [weights_by_position[p.position] for p in players]
    return rng.choices(players, weights=weights if sum(weights) else None)[0]


def _team_rows(rng, match_id, players, goals, minutes):
    scored, assisted = {}, {}
    for _ in range(goals):
        scorer = _pick(rng, players, SCORER_WEIGHTS)
        scored[scorer.id] = scored.get(scorer.id, 0) + 1
        if rng.random() < ASSIST_CHANCE:
            helper = _pick(rng, [p for p in players if p.id != scorer.id], ASSIST_WEIGHTS)
            assisted[helper.id] = assisted.get(helper.id, 0) + 1

    rows = []
    for player in players:
        sent_off = rng.random() < RED_CHANCE
        booked = rng.random() < YELLOW_CHANCE
        player_goals = scored.get(player.id, 0)
        rows.append({
            "player_id": player.id,
            "started": True,
            "minutes_played": rng.randint(max(1, minutes // 3), minutes) if sent_off and minutes else minutes,
            "goals": player_goals,
            "assists": assisted.get(player.id, 0),
            "yellow_cards": 1 if booked else 0,
            "red_cards": 1 if sent_off else 0,
            # Types use their own seed so they never shift the goals, cards or minutes above
            **split_goal_types(player_goals, f"{match_id}:{player.id}"),
        })
    return rows


def build_match_stats(match_id, status, minute, home_score, away_score, home_players, away_players):
    """
    Stat rows for every player in a match. Goals add up to the real scoreline, every goal has a
    type, assists never exceed goals, and the same match always produces the same rows. A live
    match is played up to its current minute; a completed one runs the full 90.
    """
    rng = random.Random(f"match:{match_id}")
    minutes = (minute or 0) if status == "live" else MATCH_MINUTES
    return (
        _team_rows(rng, match_id, home_players, home_score or 0, minutes)
        + _team_rows(rng, match_id, away_players, away_score or 0, minutes)
    )


def _classify_untyped_goals():
    """Give a type to goals recorded before types existed. Rows that already have a type are left alone."""
    classified = 0
    for stat in PlayerMatchStat.query.filter(PlayerMatchStat.goals > 0):
        if stat.penalty_goals + stat.headed_goals + stat.right_foot_goals + stat.left_foot_goals > 0:
            continue
        for field, count in split_goal_types(stat.goals, f"{stat.match_id}:{stat.player_id}").items():
            setattr(stat, field, count)
        classified += 1
    return classified


def seed_player_stats(app):
    """Fill in missing heights and goal types, and add stats for every started match that has none yet."""
    with app.app_context():
        heights = 0
        for player in Player.query.filter(Player.height_cm.is_(None)):
            player.height_cm = make_height(player.position, player.name)
            heights += 1

        matches = 0
        for match in Match.query.filter(Match.status != "scheduled"):
            if PlayerMatchStat.query.filter_by(match_id=match.id).first():
                continue
            home = Player.query.filter_by(team_id=match.home_team_id).order_by(Player.id).all()
            away = Player.query.filter_by(team_id=match.away_team_id).order_by(Player.id).all()
            rows = build_match_stats(match.id, match.status, match.minute, match.home_score, match.away_score, home, away)
            db.session.add_all(PlayerMatchStat(match_id=match.id, **row) for row in rows)
            matches += 1

        classified = _classify_untyped_goals()

        db.session.commit()
        print(
            f"  ✓ heights set for {heights} players, stats added for {matches} matches, "
            f"goal types set on {classified} player rows"
        )
