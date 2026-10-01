from models import Player

MAX_TEXT_LENGTH = 120
TEXT_FIELDS = ("nickname", "stadium")


def _clean_text(field, value):
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, f"{field} must be text"
    text = value.strip()
    if len(text) > MAX_TEXT_LENGTH:
        return None, f"{field} must be {MAX_TEXT_LENGTH} characters or fewer"
    return (text or None), None


def _clean_capacity(value):
    if value is None:
        return None, None
    # bool is an int subclass, so rule it out explicitly
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None, "capacity must be a positive whole number"
    return value, None


def _clean_captain(value, team_id):
    if value is None:
        return None, None
    if isinstance(value, bool) or not isinstance(value, int):
        return None, "captain_id must be a player id"
    player = Player.query.get(value)
    if player is None or player.team_id != team_id:
        return None, "The captain must be a player on this team"
    return value, None


def parse_team_profile(data, team_id=None):
    """Validate the optional club profile fields present in `data`.

    Returns (updates, None) where `updates` holds only the fields that were sent, or (None, error_message).
    A captain can only be set on an existing team (`team_id`), since a new club has no players yet.
    """
    updates = {}

    for field in TEXT_FIELDS:
        if field in data:
            updates[field], error = _clean_text(field, data[field])
            if error:
                return None, error

    if "capacity" in data:
        updates["capacity"], error = _clean_capacity(data["capacity"])
        if error:
            return None, error

    if "captain_id" in data and team_id is not None:
        updates["captain_id"], error = _clean_captain(data["captain_id"], team_id)
        if error:
            return None, error

    return updates, None
