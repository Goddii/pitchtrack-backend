import re

OUTFIELD_PLAYERS = 10

# Three or four lines of one to nine players each, like 4-3-3 or 4-2-3-1.
_SHAPE = re.compile(r"^[1-9](-[1-9]){2,3}$")


def parse_formation(value):
    """Validate a formation such as "4-3-3". Returns (clean_text, None) or (None, error_message).

    Nothing, or blank text, means "no formation set" and comes back as (None, None).
    """
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, "Formation must be text like 4-4-2"

    text = value.strip()
    if not text:
        return None, None
    if not _SHAPE.match(text):
        return None, "Formation must look like 4-4-2: three or four lines of 1 to 9 players"
    if sum(int(line) for line in text.split("-")) != OUTFIELD_PLAYERS:
        return None, f"A formation must add up to {OUTFIELD_PLAYERS} outfield players"
    return text, None
