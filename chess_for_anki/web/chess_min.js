/**
 * Minimal chess engine for Chess Line Trainer.
 * Replays SAN moves and produces FEN board positions.
 * Supports: pawn moves/captures, promotion, en passant, castling,
 * all piece moves, and SAN disambiguation. Legality-checked.
 *
 * API:  var g = new Chess();  g.move("e4");  g.fen();
 */
function Chess(startFen) {
  "use strict";

  var W = "w", B = "b";

  // 0x88 board. Index = rank*16 + file. rank 0 = rank1, file 0 = a-file.
  var board, turn, castle, ep;

  function sq(file, rank) { return rank * 16 + file; }
  function fileOf(s) { return s & 7; }
  function rankOf(s) { return s >> 4; }
  function onBoard(s) { return (s & 0x88) === 0; }
  function nameToSq(n) { return sq(n.charCodeAt(0) - 97, n.charCodeAt(1) - 49); }
  function sqToName(s) { return String.fromCharCode(97 + fileOf(s)) + String.fromCharCode(49 + rankOf(s)); }

  var KNIGHT = [-33, -31, -18, -14, 14, 18, 31, 33];
  var KING   = [-17, -16, -15, -1, 1, 15, 16, 17];
  var BISHOP = [-17, -15, 15, 17];
  var ROOK   = [-16, 16, -1, 1];
  var QUEEN  = BISHOP.concat(ROOK);

  function reset() {
    board = new Array(128).fill(null);
    var back = ["r","n","b","q","k","b","n","r"];
    for (var f = 0; f < 8; f++) {
      board[sq(f, 0)] = { t: back[f], c: W };
      board[sq(f, 1)] = { t: "p", c: W };
      board[sq(f, 6)] = { t: "p", c: B };
      board[sq(f, 7)] = { t: back[f], c: B };
    }
    turn = W;
    castle = { w: { k: true, q: true }, b: { k: true, q: true } };
    ep = null;
  }

  function loadFen(fen) {
    board = new Array(128).fill(null);
    var parts = fen.trim().split(/\s+/);
    var rows = parts[0].split("/");   // rows[0] = rank 8
    for (var r = 0; r < 8; r++) {
      var rankIdx = 7 - r;            // FEN first row is rank 8
      var fileIdx = 0;
      for (var i = 0; i < rows[r].length; i++) {
        var ch = rows[r][i];
        if (ch >= "1" && ch <= "8") {
          fileIdx += parseInt(ch, 10);
        } else {
          var color = (ch === ch.toUpperCase()) ? W : B;
          board[sq(fileIdx, rankIdx)] = { t: ch.toLowerCase(), c: color };
          fileIdx++;
        }
      }
    }
    turn = (parts[1] === "b") ? B : W;
    /* Castling rights are ASSUMED whenever the king and rook stand on their
       home squares. Pasted FENs often arrive with the rights field stripped
       ("-" or missing entirely), which would wrongly forbid O-O / O-O-O on
       custom-position cards — so the field is ignored and rights are derived
       from the placement itself. A genuine "can't castle" state still arises
       honestly from the line's own moves: the engine revokes rights the
       moment the king or rook moves. */
    function homePiece(f, r, t, c) {
      var p = board[sq(f, r)];
      return !!p && p.t === t && p.c === c;
    }
    castle = {
      w: { k: homePiece(4, 0, "k", W) && homePiece(7, 0, "r", W),
           q: homePiece(4, 0, "k", W) && homePiece(0, 0, "r", W) },
      b: { k: homePiece(4, 7, "k", B) && homePiece(7, 7, "r", B),
           q: homePiece(4, 7, "k", B) && homePiece(0, 7, "r", B) }
    };
    var rights=parts[2] || ((castle.w.k?'K':'')+(castle.w.q?'Q':'')+(castle.b.k?'k':'')+(castle.b.q?'q':''));
    castle={w:{k:rights.indexOf('K')>=0,q:rights.indexOf('Q')>=0},
            b:{k:rights.indexOf('k')>=0,q:rights.indexOf('q')>=0}};
    ep = (parts[3] && parts[3] !== "-") ? nameToSq(parts[3]) : null;
  }

  function opp(c) { return c === W ? B : W; }

  // Is square `s` attacked by color `by`?
  function attacked(s, by) {
    // pawns
    var pd = by === W ? -1 : 1; // attacker pawns sit on rank below(for white attacking upward)
    for (var i = 0; i < 2; i++) {
      var df = i === 0 ? -1 : 1;
      var from = sq(fileOf(s) + df, rankOf(s) + pd);
      if (onBoard(from) && board[from] && board[from].c === by && board[from].t === "p") return true;
    }
    // knights
    for (var k = 0; k < KNIGHT.length; k++) {
      var ks = s + KNIGHT[k];
      if (onBoard(ks) && board[ks] && board[ks].c === by && board[ks].t === "n") return true;
    }
    // king
    for (var g = 0; g < KING.length; g++) {
      var gs = s + KING[g];
      if (onBoard(gs) && board[gs] && board[gs].c === by && board[gs].t === "k") return true;
    }
    // sliders
    function slide(dirs, types) {
      for (var d = 0; d < dirs.length; d++) {
        var cur = s + dirs[d];
        while (onBoard(cur)) {
          if (board[cur]) {
            if (board[cur].c === by && types.indexOf(board[cur].t) !== -1) return true;
            break;
          }
          cur += dirs[d];
        }
      }
      return false;
    }
    if (slide(BISHOP, ["b", "q"])) return true;
    if (slide(ROOK, ["r", "q"])) return true;
    return false;
  }

  function findKing(c) {
    for (var s = 0; s < 128; s++) {
      if (onBoard(s) && board[s] && board[s].t === "k" && board[s].c === c) return s;
    }
    return -1;
  }

  function inCheck(c) { return attacked(findKing(c), opp(c)); }

  // Apply a fully-specified move object. Returns undo info.
  function doMove(m) {
    var undo = {
      from: m.from, to: m.to,
      piece: board[m.from],
      captured: board[m.to],
      ep: ep,
      castle: JSON.parse(JSON.stringify(castle)),
      epCapSq: null, epCap: null,
      isCastle: m.castle || null
    };

    var p = board[m.from];
    board[m.to] = p;
    board[m.from] = null;

    // en passant capture
    if (p.t === "p" && m.to === undo.ep && fileOf(m.from) !== fileOf(m.to)) {
      var capSq = sq(fileOf(m.to), rankOf(m.from));
      undo.epCapSq = capSq;
      undo.epCap = board[capSq];
      board[capSq] = null;
    }

    // promotion
    if (m.promo) board[m.to] = { t: m.promo, c: p.c };

    // castling rook move
    if (m.castle === "k") {
      var r1 = sq(7, rankOf(m.from)), r1to = sq(5, rankOf(m.from));
      board[r1to] = board[r1]; board[r1] = null;
    } else if (m.castle === "q") {
      var r2 = sq(0, rankOf(m.from)), r2to = sq(3, rankOf(m.from));
      board[r2to] = board[r2]; board[r2] = null;
    }

    // set new ep square
    if (p.t === "p" && Math.abs(rankOf(m.to) - rankOf(m.from)) === 2) {
      ep = sq(fileOf(m.from), (rankOf(m.from) + rankOf(m.to)) / 2);
    } else {
      ep = null;
    }

    // update castle rights
    if (p.t === "k") { castle[p.c].k = false; castle[p.c].q = false; }
    if (p.t === "r") {
      if (m.from === sq(0, p.c === W ? 0 : 7)) castle[p.c].q = false;
      if (m.from === sq(7, p.c === W ? 0 : 7)) castle[p.c].k = false;
    }
    // capturing a rook removes opponent's rights
    if (undo.captured && undo.captured.t === "r") {
      var oc = undo.captured.c;
      if (m.to === sq(0, oc === W ? 0 : 7)) castle[oc].q = false;
      if (m.to === sq(7, oc === W ? 0 : 7)) castle[oc].k = false;
    }

    return undo;
  }

  function undoMove(u) {
    board[u.from] = u.piece;
    board[u.to] = u.captured;
    if (u.epCapSq !== null) board[u.epCapSq] = u.epCap;
    if (u.isCastle === "k") {
      var r1to = sq(5, rankOf(u.from)), r1 = sq(7, rankOf(u.from));
      board[r1] = board[r1to]; board[r1to] = null;
    } else if (u.isCastle === "q") {
      var r2to = sq(3, rankOf(u.from)), r2 = sq(0, rankOf(u.from));
      board[r2] = board[r2to]; board[r2to] = null;
    }
    ep = u.ep;
    castle = u.castle;
  }

  // Generate candidate destination squares a piece at `from` can move to.
  function genFrom(from) {
    var p = board[from], dests = [];
    if (!p) return dests;
    var c = p.c;

    if (p.t === "p") {
      var dir = c === W ? 1 : -1;
      var start = c === W ? 1 : 6;
      var one = sq(fileOf(from), rankOf(from) + dir);
      if (onBoard(one) && !board[one]) {
        dests.push(one);
        var two = sq(fileOf(from), rankOf(from) + 2 * dir);
        if (rankOf(from) === start && !board[two]) dests.push(two);
      }
      for (var i = 0; i < 2; i++) {
        var df = i === 0 ? -1 : 1;
        var cap = sq(fileOf(from) + df, rankOf(from) + dir);
        if (onBoard(cap)) {
          if (board[cap] && board[cap].c === opp(c)) dests.push(cap);
          else if (cap === ep) dests.push(cap);
        }
      }
    } else if (p.t === "n") {
      for (var k = 0; k < KNIGHT.length; k++) {
        var t = from + KNIGHT[k];
        if (onBoard(t) && (!board[t] || board[t].c === opp(c))) dests.push(t);
      }
    } else if (p.t === "k") {
      for (var g = 0; g < KING.length; g++) {
        var kt = from + KING[g];
        if (onBoard(kt) && (!board[kt] || board[kt].c === opp(c))) dests.push(kt);
      }
    } else {
      var dirs = p.t === "b" ? BISHOP : p.t === "r" ? ROOK : QUEEN;
      for (var d = 0; d < dirs.length; d++) {
        var cur = from + dirs[d];
        while (onBoard(cur)) {
          if (!board[cur]) dests.push(cur);
          else { if (board[cur].c === opp(c)) dests.push(cur); break; }
          cur += dirs[d];
        }
      }
    }
    return dests;
  }

  // Parse SAN and return a fully-specified, legal move object, or null.
  function parseSan(san) {
    san = san.replace(/[+#!?]+$/g, "").replace(/[+#!?]/g, "").trim();
    var c = turn;
    var rank0 = c === W ? 0 : 7;

    // castling
    if (san === "O-O" || san === "0-0") {
      var kf = sq(4, rank0), kt = sq(6, rank0);
      if (!castle[c].k) return null;
      if (board[sq(5, rank0)] || board[sq(6, rank0)]) return null;
      if (attacked(sq(4, rank0), opp(c)) || attacked(sq(5, rank0), opp(c)) || attacked(sq(6, rank0), opp(c))) return null;
      return { from: kf, to: kt, castle: "k" };
    }
    if (san === "O-O-O" || san === "0-0-0") {
      var kf2 = sq(4, rank0), kt2 = sq(2, rank0);
      if (!castle[c].q) return null;
      if (board[sq(3, rank0)] || board[sq(2, rank0)] || board[sq(1, rank0)]) return null;
      if (attacked(sq(4, rank0), opp(c)) || attacked(sq(3, rank0), opp(c)) || attacked(sq(2, rank0), opp(c))) return null;
      return { from: kf2, to: kt2, castle: "q" };
    }

    // promotion suffix
    var promo = null;
    var pm = san.match(/=([QRBN])$/i);
    if (pm) { promo = pm[1].toLowerCase(); san = san.replace(/=([QRBN])$/i, ""); }

    san = san.replace(/x/g, "");

    var dest = san.slice(-2);
    if (!/^[a-h][1-8]$/.test(dest)) return null;
    var to = nameToSq(dest);
    var rest = san.slice(0, -2);

    var type = "p";
    if (rest.length && /[KQRBN]/.test(rest[0])) { type = rest[0].toLowerCase(); rest = rest.slice(1); }

    var dFile = null, dRank = null;
    for (var r = 0; r < rest.length; r++) {
      var ch = rest[r];
      if (ch >= "a" && ch <= "h") dFile = ch.charCodeAt(0) - 97;
      else if (ch >= "1" && ch <= "8") dRank = ch.charCodeAt(0) - 49;
    }

    // find all pieces of `type` & color that can reach `to`
    var candidates = [];
    for (var s = 0; s < 128; s++) {
      if (!onBoard(s) || !board[s] || board[s].c !== c || board[s].t !== type) continue;
      if (dFile !== null && fileOf(s) !== dFile) continue;
      if (dRank !== null && rankOf(s) !== dRank) continue;
      if (genFrom(s).indexOf(to) === -1) continue;
      candidates.push(s);
    }

    // legality filter
    var legal = [];
    for (var ci = 0; ci < candidates.length; ci++) {
      var mv = { from: candidates[ci], to: to, promo: promo };
      var u = doMove(mv);
      var ok = !inCheck(c);
      undoMove(u);
      if (ok) legal.push(mv);
    }
    if (legal.length === 0) return null;
    return legal[0];
  }

  function fen() {
    var rows = [];
    for (var r = 7; r >= 0; r--) {
      var row = "", empty = 0;
      for (var f = 0; f < 8; f++) {
        var p = board[sq(f, r)];
        if (!p) empty++;
        else {
          if (empty) { row += empty; empty = 0; }
          row += p.c === W ? p.t.toUpperCase() : p.t;
        }
      }
      if (empty) row += empty;
      rows.push(row);
    }
    var cr = (castle.w.k ? "K" : "") + (castle.w.q ? "Q" : "") +
             (castle.b.k ? "k" : "") + (castle.b.q ? "q" : "");
    return rows.join("/") + " " + turn + " " + (cr || "-") + " " +
           (ep !== null ? sqToName(ep) : "-") + " 0 1";
  }

  if (startFen) loadFen(startFen); else reset();

  // ── Additions for manual move entry (do not affect SAN replay above) ──

  // Castling destination squares available to the king at `from` (king-safe,
  // path clear, not castling through check). Returns array of dest squares.
  function castleDests(from) {
    var p = board[from], out = [];
    if (!p || p.t !== "k") return out;
    var c = p.c, rank0 = c === W ? 0 : 7;
    if (from !== sq(4, rank0)) return out;
    if (castle[c].k && !board[sq(5, rank0)] && !board[sq(6, rank0)] &&
        !attacked(sq(4, rank0), opp(c)) && !attacked(sq(5, rank0), opp(c)) &&
        !attacked(sq(6, rank0), opp(c))) {
      out.push(sq(6, rank0));
    }
    if (castle[c].q && !board[sq(3, rank0)] && !board[sq(2, rank0)] &&
        !board[sq(1, rank0)] && !attacked(sq(4, rank0), opp(c)) &&
        !attacked(sq(3, rank0), opp(c)) && !attacked(sq(2, rank0), opp(c))) {
      out.push(sq(2, rank0));
    }
    return out;
  }

  // All king-safe destination squares for the piece on `from`.
  function legalFrom(from) {
    var p = board[from];
    if (!p || p.c !== turn) return [];
    var cand = genFrom(from), out = [];
    for (var i = 0; i < cand.length; i++) {
      var to = cand[i];
      var mv = { from: from, to: to };
      if (p.t === "p" && (rankOf(to) === 7 || rankOf(to) === 0)) mv.promo = "q";
      var u = doMove(mv);
      var ok = !inCheck(p.c);
      undoMove(u);
      if (ok) out.push(to);
    }
    var cs = castleDests(from);
    for (var k = 0; k < cs.length; k++) out.push(cs[k]);
    return out;
  }

  function hasAnyLegalMove(c) {
    for (var s = 0; s < 128; s++) {
      if (!onBoard(s) || !board[s] || board[s].c !== c) continue;
      var cand = genFrom(s);
      for (var i = 0; i < cand.length; i++) {
        var mv = { from: s, to: cand[i] };
        if (board[s].t === "p" && (rankOf(cand[i]) === 7 || rankOf(cand[i]) === 0)) mv.promo = "q";
        var u = doMove(mv);
        var ok = !inCheck(c);
        undoMove(u);
        if (ok) return true;
      }
    }
    return false;
  }

  // Build SAN for a from/to(/promo) move in the CURRENT position (pre-apply).
  function buildSan(from, to, promo) {
    var p = board[from], c = p.c;
    // castling
    if (p.t === "k" && fileOf(from) === 4 && Math.abs(fileOf(to) - 4) === 2) {
      return fileOf(to) === 6 ? "O-O" : "O-O-O";
    }
    var capture = !!board[to] || (p.t === "p" && fileOf(from) !== fileOf(to));
    var san = "";
    if (p.t === "p") {
      if (capture) san += String.fromCharCode(97 + fileOf(from)) + "x";
      san += sqToName(to);
      if (promo) san += "=" + promo.toUpperCase();
      return san;
    }
    san = p.t.toUpperCase();
    // disambiguation: other same-type, same-colour pieces that could also
    // legally land on `to`.
    var rivals = [];
    for (var s = 0; s < 128; s++) {
      if (!onBoard(s) || s === from || !board[s]) continue;
      if (board[s].c !== c || board[s].t !== p.t) continue;
      if (genFrom(s).indexOf(to) === -1) continue;
      var mv = { from: s, to: to };
      var u = doMove(mv);
      var ok = !inCheck(c);
      undoMove(u);
      if (ok) rivals.push(s);
    }
    if (rivals.length) {
      var sameFile = rivals.some(function (s) { return fileOf(s) === fileOf(from); });
      var sameRank = rivals.some(function (s) { return rankOf(s) === rankOf(from); });
      if (!sameFile) san += String.fromCharCode(97 + fileOf(from));
      else if (!sameRank) san += String.fromCharCode(49 + rankOf(from));
      else san += sqToName(from);
    }
    if (capture) san += "x";
    san += sqToName(to);
    return san;
  }

  return {
    move: function (san) {
      var m = parseSan(san);
      if (!m) return null;
      doMove(m);
      turn = opp(turn);
      return m;
    },
    fen: fen,
    reset: reset,
    load: loadFen,

    // ── Manual-entry API ──
    turnColor: function () { return turn; },
    // Is the side to move in check? (In a legal position only the side to
    // move can be in check.) Used for the red king-in-check glow.
    inCheck: function () { return inCheck(turn); },
    pieceAt: function (name) {
      var s = nameToSq(name);
      return board[s] ? { color: board[s].c, type: board[s].t } : null;
    },
    legalDests: function (fromName) {
      return legalFrom(nameToSq(fromName)).map(sqToName);
    },
    // Returns { san, fen } if the move is legal, else null.
    moveFromTo: function (fromName, toName, promo) {
      var from = nameToSq(fromName), to = nameToSq(toName);
      var p = board[from];
      if (!p || p.c !== turn) return null;
      if (legalFrom(from).indexOf(to) === -1) return null;
      var mv = { from: from, to: to };
      if (p.t === "p" && (rankOf(to) === 7 || rankOf(to) === 0)) {
        mv.promo = (promo || "q").toLowerCase();
      }
      if (p.t === "k" && fileOf(from) === 4 && Math.abs(fileOf(to) - 4) === 2) {
        mv.castle = fileOf(to) === 6 ? "k" : "q";
      }
      var san = buildSan(from, to, mv.promo);
      doMove(mv);
      turn = opp(turn);
      // check / mate suffix
      if (inCheck(turn)) san += hasAnyLegalMove(turn) ? "+" : "#";
      return { san: san, fen: fen() };
    }
  };
}
