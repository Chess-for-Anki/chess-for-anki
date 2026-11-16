"""Bounded PGN tokenization and variation expansion, without executing input."""
from pathlib import Path
import re

MAX_BYTES = 1024 * 1024
MAX_TOKENS = 60000
MAX_DEPTH = 32
MAX_LINES = 256
MAX_PLIES = 600
RESULTS = frozenset(("1-0", "0-1", "1/2-1/2", "*"))


def read_pgn_file(filename):
    with Path(filename).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("PGN files must be no larger than 1 MB. Split the collection into smaller files.")
    return raw.decode("utf-8-sig", errors="replace")


def _tokens(pgn_text):
    if not isinstance(pgn_text, str) or len(pgn_text) > MAX_BYTES or len(pgn_text.encode("utf8")) > MAX_BYTES:
        raise ValueError("PGN text must be no larger than 1 MB.")
    text = re.sub(r"\{[^}]*\}", " ", pgn_text)
    if "{" in text or "}" in text:
        raise ValueError("Unbalanced PGN comment braces.")
    lines = [line.split(";", 1)[0] for line in text.splitlines() if not line.lstrip().startswith("[")]
    text = re.sub(r"\$\d+", " ", " ".join(lines))
    raw = text.replace("(", " ( ").replace(")", " ) ").split()
    if len(raw) > MAX_TOKENS:
        raise ValueError("The PGN contains too many tokens.")
    tokens, depth = [], 0
    for token in raw:
        if token == "(":
            depth += 1
            if depth > MAX_DEPTH:
                raise ValueError("PGN variations may be nested at most 32 levels.")
        elif token == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced PGN variation parentheses.")
        else:
            token = re.sub(r"^\d+\.+", "", token)
            token = re.sub(r"[!?]+$", "", token)
        if token:
            tokens.append(token)
    if depth:
        raise ValueError("Unbalanced PGN variation parentheses.")
    return tokens


def expand_variations(pgn_text):
    """Return distinct complete branches. Results separate games, never join them."""
    tokens = _tokens(pgn_text)
    lines, seen = [], set()

    def emit(line):
        key = tuple(line)
        if key and key not in seen:
            if len(lines) >= MAX_LINES:
                raise ValueError("Import at most 256 lines at a time.")
            seen.add(key)
            lines.append(list(line))

    def parse(index, prefix, nested=False):
        line = list(prefix)
        while index < len(tokens):
            token = tokens[index]
            if token == "(":
                if not line:
                    raise ValueError("A variation must follow the move it replaces.")
                index = parse(index + 1, line[:-1], True)
                continue
            if token == ")":
                emit(line)
                return index + 1
            if token in RESULTS:
                emit(line)
                if nested:
                    if index + 1 < len(tokens) and tokens[index + 1] == ")":
                        return index + 2
                    raise ValueError("A result must end its PGN variation.")
                line = []
            else:
                line.append(token)
                if len(line) > MAX_PLIES:
                    raise ValueError("A training line may contain at most 600 plies.")
            index += 1
        emit(line)
        return index

    parse(0, [])
    return lines


def parse_pgn_moves(pgn_text):
    """Return only the first game's mainline, ignoring variations."""
    result, depth = [], 0
    for token in _tokens(pgn_text):
        if token == "(":
            depth += 1
        elif token == ")":
            depth -= 1
        elif depth == 0:
            if token in RESULTS:
                break
            result.append(token)
            if len(result) > MAX_PLIES:
                raise ValueError("A training line may contain at most 600 plies.")
    return result


def pgn_to_json(pgn_text, title, player_color):
    moves = parse_pgn_moves(pgn_text)
    if not moves:
        raise ValueError("No moves found in PGN. Please check the format.")
    return dict(title=title, player_color=player_color, moves=moves, pgn_raw=pgn_text.strip())
