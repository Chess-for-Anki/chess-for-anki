"""Strict, declarative brilliant-move metadata for an individual note."""

import json

SCHEMA = 1
MAX_PLIES = 600
MAX_METADATA_BYTES = 8192


def validate(data, move_count=None):
    """Return a canonical copy; ply 1 is the first move from the note's FEN."""
    if not isinstance(data, dict) or set(data) != {"schema", "plies"}:
        raise ValueError("Brilliant Moves needs only schema and plies.")
    if type(data["schema"]) is not int or data["schema"] != SCHEMA:
        raise ValueError("Unsupported Brilliant Moves schema.")
    if move_count is not None and (type(move_count) is not int or move_count < 0):
        raise ValueError("The move count must be a non-negative integer.")
    plies = data["plies"]
    if not isinstance(plies, list) or len(plies) > MAX_PLIES:
        raise ValueError("Brilliant Moves needs an array of up to 600 plies.")
    maximum = min(MAX_PLIES, move_count) if move_count is not None else MAX_PLIES
    if any(type(ply) is not int or not 1 <= ply <= maximum for ply in plies):
        raise ValueError("Brilliant move plies must be integers within the saved line.")
    if len(set(plies)) != len(plies):
        raise ValueError("Brilliant move plies must not be duplicated.")
    return {"schema": SCHEMA, "plies": sorted(plies)}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Brilliant Moves must not contain duplicate JSON keys.")
        result[key] = value
    return result


def loads(text, move_count=None):
    """Read plain JSON; an empty optional field means no brilliant moves."""
    if not isinstance(text, str):
        raise ValueError("Brilliant Moves must be plain JSON text.")
    if len(text) > MAX_METADATA_BYTES or len(text.encode("utf8")) > MAX_METADATA_BYTES:
        raise ValueError("Brilliant Moves exceeds the 8 KiB metadata limit.")
    if not text.strip():
        return validate({"schema": SCHEMA, "plies": []}, move_count)
    try:
        data = json.loads(text, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Brilliant Moves must be valid JSON.") from error
    return validate(data, move_count)


def dumps(data, move_count=None):
    """Serialize canonical JSON, leaving a note's unused field empty."""
    canonical = validate(data, move_count)
    return json.dumps(canonical, separators=(",", ":")) if canonical["plies"] else ""
