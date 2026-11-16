"""Bounded, inert position evaluations, indexed before move 0 and after each ply.

Scores always use White's perspective. This validates transport data and exact
line identity; chess legality and engine strength belong to the authoring tool.
"""

import json
import re

MAX_BYTES = 256 * 1024
MAX_MOVES = 600
MAX_CP = 1_000_000
MAX_MATE = 1000
_SAN = re.compile(r"^(?:O-O(?:-O)?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?)[+#]?$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _keys(value, required, optional=()):
    return (type(value) is dict and set(required) <= set(value)
            and set(value) <= set(required) | set(optional))


def _fen(value):
    if type(value) is not str or len(value) > 128:
        return False
    if value == "":
        return True
    parts = value.split(" ")
    if len(parts) != 6:
        return False
    board, turn, castle, ep, halfmove, fullmove = parts
    ranks = board.split("/")
    if len(ranks) != 8 or board.count("K") != 1 or board.count("k") != 1:
        return False
    for rank in ranks:
        if not rank or not re.fullmatch(r"[prnbqkPRNBQK1-8]+", rank):
            return False
        if sum(int(c) if c.isdigit() else 1 for c in rank) != 8:
            return False
        if re.search(r"[1-8]{2}", rank):
            return False
    return (turn in ("w", "b") and re.fullmatch(r"-|K?Q?k?q?", castle) is not None
            and bool(castle) and re.fullmatch(r"-|[a-h][36]", ep) is not None
            and re.fullmatch(r"0|[1-9][0-9]{0,5}", halfmove) is not None
            and re.fullmatch(r"[1-9][0-9]{0,5}", fullmove) is not None)


def _size(text):
    try:
        if len(text.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Position evaluation exceeds 256 KiB")
    except UnicodeError as exc:
        raise ValueError("Position evaluation contains invalid Unicode") from exc


def validate(data, *, start_fen=None, moves=None):
    """Return a canonical copy, or raise ValueError. Optional identity is exact."""
    if not _keys(data, ("schema", "start_fen", "moves", "scores", "engine")):
        raise ValueError("Invalid position evaluation fields")
    if type(data["schema"]) is not int or data["schema"] != 1:
        raise ValueError("Unsupported position evaluation schema")
    if not _fen(data["start_fen"]):
        raise ValueError("Invalid evaluation start FEN")
    line = data["moves"]
    if type(line) is not list or len(line) > MAX_MOVES:
        raise ValueError("Evaluation needs at most 600 moves")
    if any(type(move) is not str or not _SAN.fullmatch(move) for move in line):
        raise ValueError("Invalid evaluation SAN move")
    if start_fen is not None and data["start_fen"] != start_fen:
        raise ValueError("Evaluation start FEN does not match the card")
    if moves is not None and line != list(moves):
        raise ValueError("Evaluation moves do not match the card")
    scores = data["scores"]
    if type(scores) is not list or len(scores) != len(line) + 1:
        raise ValueError("Evaluation scores must include the initial position")
    clean_scores = []
    for score in scores:
        if score is None:
            clean_scores.append(None)
        elif _keys(score, ("cp",)) and _integer(score["cp"], -MAX_CP, MAX_CP):
            clean_scores.append({"cp": score["cp"]})
        elif (_keys(score, ("mate",)) and _integer(score["mate"], -MAX_MATE, MAX_MATE)
              and score["mate"] != 0):
            clean_scores.append({"mate": score["mate"]})
        else:
            raise ValueError("Invalid evaluation score; mate zero has no winner sign")
    engine = data["engine"]
    if not _keys(engine, ("name",), ("nodes", "depth")):
        raise ValueError("Invalid evaluation engine fields")
    name = engine["name"]
    if type(name) is not str or not name.strip() or len(name) > 120 or _CONTROL.search(name):
        raise ValueError("Invalid evaluation engine name")
    clean_engine = {"name": name}
    for field, maximum in (("nodes", 2**53 - 1), ("depth", 1000)):
        if field in engine:
            if not _integer(engine[field], 1, maximum):
                raise ValueError("Invalid evaluation engine " + field)
            clean_engine[field] = engine[field]
    result = {"schema": 1, "start_fen": data["start_fen"], "moves": list(line),
              "scores": clean_scores, "engine": clean_engine}
    _size(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate evaluation JSON key")
        result[key] = value
    return result


def loads(raw, *, start_fen=None, moves=None):
    """Parse JSON only, with no expression evaluation or executable payloads."""
    if not isinstance(raw, (str, bytes)):
        raise ValueError("Position evaluation must be JSON text")
    if isinstance(raw, bytes):
        if len(raw) > MAX_BYTES:
            raise ValueError("Position evaluation exceeds 256 KiB")
        try:
            raw = raw.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("Position evaluation must be UTF-8") from exc
    _size(raw)
    try:
        data = json.loads(raw, object_pairs_hook=_unique_object)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid position evaluation JSON") from exc
    return validate(data, start_fen=start_fen, moves=moves)


def dumps(data, *, start_fen=None, moves=None):
    """Serialize validated data; escape HTML delimiters for safe text embedding."""
    result = json.dumps(validate(data, start_fen=start_fen, moves=moves),
                        ensure_ascii=True, separators=(",", ":"))
    result = result.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    _size(result)
    return result
