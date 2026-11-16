"""
Minimal chess logic in pure Python for validating custom positions.

Used by the position editor to check legality on OK:
 - side-not-to-move not in check
 - whether the side to move has any legal move (to detect mate/stalemate)

Board representation: board[rank][file], rank 0 = rank 1, file 0 = a-file.
Each cell is a piece code like 'wK', 'bQ', or None.
"""

KNIGHT_DELTAS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                 (1, -2), (1, 2), (2, -1), (2, 1)]
KING_DELTAS = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
               (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _in_bounds(r, f):
    return 0 <= r < 8 and 0 <= f < 8


def find_king(board, color):
    target = color + "K"
    for r in range(8):
        for f in range(8):
            if board[r][f] == target:
                return (r, f)
    return None


def is_attacked(board, r, f, by_color):
    """Is square (r,f) attacked by any piece of `by_color`?"""
    # Pawns: a pawn of by_color attacks diagonally "forward".
    # White pawns move up (increasing rank), so they attack from rank-1.
    pawn_dir = 1 if by_color == "w" else -1
    for df in (-1, 1):
        pr, pf = r - pawn_dir, f + df
        if _in_bounds(pr, pf):
            p = board[pr][pf]
            if p == by_color + "P":
                return True

    # Knights
    for dr, df in KNIGHT_DELTAS:
        nr, nf = r + dr, f + df
        if _in_bounds(nr, nf) and board[nr][nf] == by_color + "N":
            return True

    # King
    for dr, df in KING_DELTAS:
        nr, nf = r + dr, f + df
        if _in_bounds(nr, nf) and board[nr][nf] == by_color + "K":
            return True

    # Sliding: bishops/queens on diagonals
    for dr, df in BISHOP_DIRS:
        nr, nf = r + dr, f + df
        while _in_bounds(nr, nf):
            p = board[nr][nf]
            if p is not None:
                if p[0] == by_color and p[1] in ("B", "Q"):
                    return True
                break
            nr += dr
            nf += df

    # Sliding: rooks/queens on ranks/files
    for dr, df in ROOK_DIRS:
        nr, nf = r + dr, f + df
        while _in_bounds(nr, nf):
            p = board[nr][nf]
            if p is not None:
                if p[0] == by_color and p[1] in ("R", "Q"):
                    return True
                break
            nr += dr
            nf += df

    return False


def in_check(board, color):
    kp = find_king(board, color)
    if kp is None:
        return False
    opp = "b" if color == "w" else "w"
    return is_attacked(board, kp[0], kp[1], opp)


def _pseudo_moves(board, color):
    """Generate pseudo-legal moves (not filtering self-check) as
    (from_r, from_f, to_r, to_f) tuples. Promotions are treated as a
    normal move to the last rank (sufficient for mate/stalemate test)."""
    opp = "b" if color == "w" else "w"
    moves = []
    for r in range(8):
        for f in range(8):
            p = board[r][f]
            if p is None or p[0] != color:
                continue
            kind = p[1]
            if kind == "P":
                d = 1 if color == "w" else -1
                start_rank = 1 if color == "w" else 6
                # forward one
                nr = r + d
                if _in_bounds(nr, f) and board[nr][f] is None:
                    moves.append((r, f, nr, f))
                    # forward two
                    nr2 = r + 2 * d
                    if r == start_rank and board[nr2][f] is None:
                        moves.append((r, f, nr2, f))
                # captures
                for df in (-1, 1):
                    cr, cf = r + d, f + df
                    if _in_bounds(cr, cf):
                        q = board[cr][cf]
                        if q is not None and q[0] == opp:
                            moves.append((r, f, cr, cf))
            elif kind == "N":
                for dr, df in KNIGHT_DELTAS:
                    nr, nf = r + dr, f + df
                    if _in_bounds(nr, nf):
                        q = board[nr][nf]
                        if q is None or q[0] == opp:
                            moves.append((r, f, nr, nf))
            elif kind == "K":
                for dr, df in KING_DELTAS:
                    nr, nf = r + dr, f + df
                    if _in_bounds(nr, nf):
                        q = board[nr][nf]
                        if q is None or q[0] == opp:
                            moves.append((r, f, nr, nf))
            else:
                dirs = (BISHOP_DIRS if kind == "B"
                        else ROOK_DIRS if kind == "R"
                        else BISHOP_DIRS + ROOK_DIRS)  # Q
                for dr, df in dirs:
                    nr, nf = r + dr, f + df
                    while _in_bounds(nr, nf):
                        q = board[nr][nf]
                        if q is None:
                            moves.append((r, f, nr, nf))
                        else:
                            if q[0] == opp:
                                moves.append((r, f, nr, nf))
                            break
                        nr += dr
                        nf += df
    return moves


def has_legal_move(board, color):
    """Does `color` have at least one legal move (one that doesn't leave
    its own king in check)?"""
    for (fr, ff, tr, tf) in _pseudo_moves(board, color):
        # make the move on a shallow copy
        moved = [row[:] for row in board]
        moved[tr][tf] = moved[fr][ff]
        moved[fr][ff] = None
        if not in_check(moved, color):
            return True
    return False


# ── SAN move application (for validating PGN lines) ─────────────

import re as _re


def board_from_fen(fen):
    """Build a board (and side to move) from a FEN. Returns (board, turn)."""
    board = [[None] * 8 for _ in range(8)]
    parts = fen.strip().split()
    rows = parts[0].split("/")
    for r in range(8):
        rank_idx = 7 - r
        file_idx = 0
        for ch in rows[r]:
            if ch.isdigit():
                file_idx += int(ch)
            else:
                color = "w" if ch.isupper() else "b"
                board[rank_idx][file_idx] = color + ch.upper()
                file_idx += 1
    turn = "b" if (len(parts) > 1 and parts[1] == "b") else "w"
    return board, turn


def _start_board():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    return board_from_fen(fen)


def apply_san(board, turn, san, ep_target):
    """
    Try to apply SAN move `san` for side `turn` on `board`.
    `ep_target` is the en-passant target square as (r, f) or None.

    Returns (new_ep_target,) on success by mutating `board` in place,
    or raises ValueError if the move is illegal/unparseable.
    """
    color = turn
    opp = "b" if color == "w" else "w"
    back_rank = 0 if color == "w" else 7

    raw = san
    s = _re.sub(r"[+#!?]+$", "", san).strip()

    # Castling
    if s in ("O-O", "0-0"):
        # King e->g, rook h->f
        kf, kt = (4, back_rank), (6, back_rank)
        if board[back_rank][4] != color + "K":
            raise ValueError(raw)
        if board[back_rank][5] is not None or board[back_rank][6] is not None:
            raise ValueError(raw)
        if (is_attacked(board, back_rank, 4, opp)
                or is_attacked(board, back_rank, 5, opp)
                or is_attacked(board, back_rank, 6, opp)):
            raise ValueError(raw)
        board[back_rank][6] = board[back_rank][4]
        board[back_rank][4] = None
        board[back_rank][5] = board[back_rank][7]
        board[back_rank][7] = None
        return None
    if s in ("O-O-O", "0-0-0"):
        if board[back_rank][4] != color + "K":
            raise ValueError(raw)
        if (board[back_rank][3] is not None or board[back_rank][2] is not None
                or board[back_rank][1] is not None):
            raise ValueError(raw)
        if (is_attacked(board, back_rank, 4, opp)
                or is_attacked(board, back_rank, 3, opp)
                or is_attacked(board, back_rank, 2, opp)):
            raise ValueError(raw)
        board[back_rank][2] = board[back_rank][4]
        board[back_rank][4] = None
        board[back_rank][3] = board[back_rank][0]
        board[back_rank][0] = None
        return None

    # Promotion suffix (=Q etc.)
    promo = None
    m = _re.search(r"=([QRBN])$", s, _re.IGNORECASE)
    if m:
        promo = m.group(1).upper()
        s = _re.sub(r"=([QRBN])$", "", s, flags=_re.IGNORECASE)

    s = s.replace("x", "")

    if len(s) < 2:
        raise ValueError(raw)
    dest = s[-2:]
    if not _re.match(r"^[a-h][1-8]$", dest):
        raise ValueError(raw)
    to_f = ord(dest[0]) - 97
    to_r = int(dest[1]) - 1
    rest = s[:-2]

    piece_type = "P"
    if rest and rest[0] in "KQRBN":
        piece_type = rest[0]
        rest = rest[1:]

    dis_file = dis_rank = None
    for ch in rest:
        if "a" <= ch <= "h":
            dis_file = ord(ch) - 97
        elif "1" <= ch <= "8":
            dis_rank = int(ch) - 1

    # Find candidate source squares of this piece type that can reach dest
    candidates = []
    for r in range(8):
        for f in range(8):
            p = board[r][f]
            if p is None or p[0] != color or p[1] != piece_type:
                continue
            if dis_file is not None and f != dis_file:
                continue
            if dis_rank is not None and r != dis_rank:
                continue
            if _can_reach(board, p, r, f, to_r, to_f, ep_target):
                candidates.append((r, f))

    # Filter for legality (own king not in check after the move)
    legal = []
    for (fr, ff) in candidates:
        test = [row[:] for row in board]
        _do_raw_move(test, fr, ff, to_r, to_f, promo, color, ep_target)
        if not in_check(test, color):
            legal.append((fr, ff))

    if len(legal) == 0:
        raise ValueError(raw)

    fr, ff = legal[0]
    new_ep = _do_raw_move(board, fr, ff, to_r, to_f, promo, color, ep_target)
    return new_ep


def _can_reach(board, piece, r, f, to_r, to_f, ep_target):
    color = piece[0]
    opp = "b" if color == "w" else "w"
    kind = piece[1]
    dest_piece = board[to_r][to_f]

    if kind == "P":
        d = 1 if color == "w" else -1
        start_rank = 1 if color == "w" else 6
        # straight push
        if f == to_f:
            if to_r == r + d and dest_piece is None:
                return True
            if (r == start_rank and to_r == r + 2 * d
                    and board[r + d][f] is None and dest_piece is None):
                return True
            return False
        # capture
        if abs(f - to_f) == 1 and to_r == r + d:
            if dest_piece is not None and dest_piece[0] == opp:
                return True
            if ep_target is not None and (to_r, to_f) == ep_target:
                return True
        return False

    if kind == "N":
        if (abs(r - to_r), abs(f - to_f)) in ((1, 2), (2, 1)):
            return dest_piece is None or dest_piece[0] == opp
        return False

    if kind == "K":
        if max(abs(r - to_r), abs(f - to_f)) == 1:
            return dest_piece is None or dest_piece[0] == opp
        return False

    # sliding pieces
    if kind == "B":
        dirs = BISHOP_DIRS
    elif kind == "R":
        dirs = ROOK_DIRS
    else:  # Q
        dirs = BISHOP_DIRS + ROOK_DIRS
    for dr, df in dirs:
        nr, nf = r + dr, f + df
        while _in_bounds(nr, nf):
            if (nr, nf) == (to_r, to_f):
                return dest_piece is None or dest_piece[0] == opp
            if board[nr][nf] is not None:
                break
            nr += dr
            nf += df
    return False


def _do_raw_move(board, fr, ff, to_r, to_f, promo, color, ep_target):
    """Apply a move on the board in place. Returns the new ep target (r,f)
    or None."""
    piece = board[fr][ff]
    # en passant capture
    if piece[1] == "P" and ff != to_f and board[to_r][to_f] is None:
        # capturing en passant: remove the pawn on the from-rank, to-file
        board[fr][to_f] = None
    board[to_r][to_f] = piece
    board[fr][ff] = None
    if promo:
        board[to_r][to_f] = color + promo
    # set new ep target if a pawn advanced two squares
    new_ep = None
    if piece[1] == "P" and abs(to_r - fr) == 2:
        new_ep = ((to_r + fr) // 2, ff)
    return new_ep


def board_to_simple_fen(board, turn):
    """Serialize a board to a SIMPLIFIED FEN: piece placement + side to move
    only (no castling rights / en-passant / clocks). This is the searchable
    form stored in the MovesFEN field - enough to identify a position for
    transposition lookup, short enough to search comfortably."""
    rows = []
    for r in range(7, -1, -1):
        empties, row = 0, ""
        for f in range(8):
            p = board[r][f]
            if p is None:
                empties += 1
            else:
                if empties:
                    row += str(empties)
                    empties = 0
                row += p[1].upper() if p[0] == "w" else p[1].lower()
        if empties:
            row += str(empties)
        rows.append(row)
    return "/".join(rows) + " " + turn


def fens_after_each(moves, start_fen=None):
    """Replay SAN `moves` from the start (or `start_fen`) and return the
    simplified FEN after EVERY half-move, in order. Returns None if any move
    is illegal (callers then leave MovesFEN empty rather than store a wrong
    position)."""
    if start_fen:
        board, turn = board_from_fen(start_fen)
    else:
        board, turn = _start_board()
    ep_target = None
    out = []
    for mv in moves:
        try:
            ep_target = apply_san(board, turn, mv, ep_target)
        except ValueError:
            return None
        turn = "b" if turn == "w" else "w"
        out.append(board_to_simple_fen(board, turn))
    return out


def validate_line(moves, start_fen=None):
    """
    Replay a list of SAN moves from the start position (or `start_fen`).
    Returns (ok, index, move) where:
      ok=True  -> all moves legal (index/move are None)
      ok=False -> the move at `index` (0-based) named `move` is illegal.
    """
    if start_fen:
        board, turn = board_from_fen(start_fen)
    else:
        board, turn = _start_board()

    ep_target = None
    for i, mv in enumerate(moves):
        try:
            ep_target = apply_san(board, turn, mv, ep_target)
        except ValueError:
            return (False, i, mv)
        turn = "b" if turn == "w" else "w"
    return (True, None, None)
