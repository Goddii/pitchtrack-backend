from collections import Counter

from sqlalchemy import and_, case, func

from extensions import db
from models import Match, Player, PlayerMatchStat

MAX_MINUTES = 120
MAX_STARTERS = 11  # per team in one match
MAX_COUNT = 30  # sanity ceiling for goals, assists and cards in one match
COUNT_FIELDS = ("goals", "assists", "yellow_cards", "red_cards")
GOAL_TYPE_FIELDS = ("penalty_goals", "headed_goals", "right_foot_goals", "left_foot_goals")
LINEUP_ONLY_FIELDS = ("minutes_played", *COUNT_FIELDS, *GOAL_TYPE_FIELDS)  # must all be 0 before kickoff
TOTAL_FIELDS = (
    "appearances", "starts", "minutes", "goals", "assists", "yellow_cards", "red_cards",
    *GOAL_TYPE_FIELDS,
)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _total_columns():
    """Season-total aggregates, in TOTAL_FIELDS order.

    An appearance is a match with at least one minute played, and a start is an appearance that began
    in the starting eleven. A lineup announced before kickoff has no minutes yet, so it counts as neither.
    """
    return (
        func.coalesce(func.sum(case((PlayerMatchStat.minutes_played > 0, 1), else_=0)), 0),
        func.coalesce(
            func.sum(case((and_(PlayerMatchStat.started.is_(True), PlayerMatchStat.minutes_played > 0), 1), else_=0)),
            0,
        ),
        func.coalesce(func.sum(PlayerMatchStat.minutes_played), 0),
        func.coalesce(func.sum(PlayerMatchStat.goals), 0),
        func.coalesce(func.sum(PlayerMatchStat.assists), 0),
        func.coalesce(func.sum(PlayerMatchStat.yellow_cards), 0),
        func.coalesce(func.sum(PlayerMatchStat.red_cards), 0),
        func.coalesce(func.sum(PlayerMatchStat.penalty_goals), 0),
        func.coalesce(func.sum(PlayerMatchStat.headed_goals), 0),
        func.coalesce(func.sum(PlayerMatchStat.right_foot_goals), 0),
        func.coalesce(func.sum(PlayerMatchStat.left_foot_goals), 0),
    )


def _totals_from(values):
    return dict(zip(TOTAL_FIELDS, (int(v) for v in values)))


def aggregate_player_stats(player_id):
    """Season totals for one player."""
    row = db.session.query(*_total_columns()).filter(PlayerMatchStat.player_id == player_id).one()
    return {"player_id": player_id, **_totals_from(row)}


def team_player_totals(team_id):
    """Season totals for every player at a club in one query, including players with no stats yet."""
    rows = (
        db.session.query(Player, *_total_columns())
        .outerjoin(PlayerMatchStat, PlayerMatchStat.player_id == Player.id)
        .filter(Player.team_id == team_id)
        .group_by(Player.id)
        .order_by(Player.name.asc())
        .all()
    )
    return [
        {
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "jersey_number": player.jersey_number,
                "photo_url": player.photo_url,
            },
            **_totals_from(values),
        }
        for player, *values in rows
    ]


def player_match_log(player):
    """One row per match the player has stats for, newest first, from the player's own side."""
    rows = (
        db.session.query(PlayerMatchStat, Match)
        .join(Match, Match.id == PlayerMatchStat.match_id)
        .filter(PlayerMatchStat.player_id == player.id)
        .order_by(Match.match_date.desc())
        .all()
    )

    log = []
    for stat, match in rows:
        was_home = match.home_team_id == player.team_id
        opponent = match.away_team if was_home else match.home_team
        log.append({
            "match_id": match.id,
            "match_date": match.match_date.isoformat() if match.match_date else None,
            "status": match.status,
            "venue": match.venue,
            "minute": match.minute,
            "home_team": match.home_team.to_summary() if match.home_team else None,
            "away_team": match.away_team.to_summary() if match.away_team else None,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "was_home": was_home,
            "opponent": opponent.to_summary() if opponent else None,
            "stats": {
                "started": stat.started,
                "minutes_played": stat.minutes_played,
                "goals": stat.goals,
                "assists": stat.assists,
                "yellow_cards": stat.yellow_cards,
                "red_cards": stat.red_cards,
            },
        })
    return log


def parse_stat_row(raw):
    """Validate one submitted row. Returns (clean_row, None) or (None, error_message)."""
    if not isinstance(raw, dict):
        return None, "Each stat must be an object"

    player_id = raw.get("player_id")
    if not _is_int(player_id):
        return None, "player_id must be a whole number"

    started = raw.get("started", False)
    if not isinstance(started, bool):
        return None, "started must be true or false"

    minutes = raw.get("minutes_played", 0)
    if not _is_int(minutes) or not 0 <= minutes <= MAX_MINUTES:
        return None, f"minutes_played must be a whole number from 0 to {MAX_MINUTES}"

    row = {"player_id": player_id, "started": started, "minutes_played": minutes}
    for field in COUNT_FIELDS + GOAL_TYPE_FIELDS:
        value = raw.get(field, 0)
        if not _is_int(value) or not 0 <= value <= MAX_COUNT:
            return None, f"{field} must be a whole number from 0 to {MAX_COUNT}"
        row[field] = value

    if sum(row[field] for field in GOAL_TYPE_FIELDS) > row["goals"]:
        return None, "The goal types cannot add up to more than the goals scored"
    return row, None


def _lineup_only_problem(match, rows):
    """Before kickoff only the starting lineup can be saved: who starts, with nothing played yet."""
    if match.status != "scheduled":
        return None
    if any(row[field] for row in rows for field in LINEUP_ONLY_FIELDS):
        return "Only the starting lineup can be set for a scheduled match: no minutes, goals, assists or cards"
    return None


def _roster_problem(match, rows):
    """Every submitted player must exist and play for one of the two teams."""
    players = {p.id: p for p in Player.query.filter(Player.id.in_([r["player_id"] for r in rows])).all()}
    team_ids = {match.home_team_id, match.away_team_id}

    for row in rows:
        player = players.get(row["player_id"])
        if player is None:
            return f"Player {row['player_id']} does not exist"
        if player.team_id not in team_ids:
            return f"{player.name} does not play for either team in this match"
    return None


def _starters_problem(after, team_of):
    """A team cannot start more than eleven players."""
    starters = Counter(team_of[player_id] for player_id, row in after.items() if row["started"])
    if any(count > MAX_STARTERS for count in starters.values()):
        return f"A team cannot start more than {MAX_STARTERS} players"
    return None


def _goals_problem(match, after, team_of):
    """Goals per team across the whole match cannot beat the score."""
    scores = {match.home_team_id: match.home_score or 0, match.away_team_id: match.away_score or 0}
    goals = Counter()
    for player_id, row in after.items():
        goals[team_of[player_id]] += row["goals"]

    for team_id, score in scores.items():
        if goals[team_id] > score:
            return f"Goals for a team cannot exceed the team's score ({score})"
    return None


def validate_match_stats(match, rows):
    """Check a batch of parsed rows against the match. Returns an error message or None."""
    error = _lineup_only_problem(match, rows) or _roster_problem(match, rows)
    if error:
        return error

    # The match as it would stand after saving: rows already saved, overridden by this batch
    after = {s.player_id: {"started": s.started, "goals": s.goals} for s in PlayerMatchStat.query.filter_by(match_id=match.id)}
    after.update({r["player_id"]: {"started": r["started"], "goals": r["goals"]} for r in rows})
    team_of = {p.id: p.team_id for p in Player.query.filter(Player.id.in_(list(after))).all()}

    return _starters_problem(after, team_of) or _goals_problem(match, after, team_of)
