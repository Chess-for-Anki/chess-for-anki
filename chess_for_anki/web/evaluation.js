/* Inert, line-bound engine scores. White is always the positive side. */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CFA_EVALUATION = factory();
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  var MAX_BYTES = 256 * 1024, MAX_MOVES = 600, MAX_CP = 1000000, MAX_MATE = 1000;
  var SAN = /^(?:O-O(?:-O)?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?)[+#]?$/;
  function integer(n, low, high) { return typeof n === "number" && isFinite(n) && Math.floor(n) === n && n >= low && n <= high; }
  function keys(value, required, optional) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    var proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) return false;
    var allowed = required.concat(optional || []), own = Object.keys(value);
    return required.every(function (k) { return Object.prototype.hasOwnProperty.call(value, k); }) &&
      own.every(function (k) { var d = Object.getOwnPropertyDescriptor(value, k); return allowed.indexOf(k) >= 0 && d && Object.prototype.hasOwnProperty.call(d, "value"); });
  }
  function bytes(text) {
    var n = 0;
    for (var i = 0; i < text.length; i++) {
      var c = text.charCodeAt(i);
      if (c < 128) n++;
      else if (c < 2048) n += 2;
      else if (c >= 0xD800 && c <= 0xDBFF) {
        var next = text.charCodeAt(++i);
        if (!(next >= 0xDC00 && next <= 0xDFFF)) return Infinity;
        n += 4;
      } else if (c >= 0xDC00 && c <= 0xDFFF) return Infinity;
      else n += 3;
    }
    return n;
  }
  function fen(value) {
    if (typeof value !== "string" || value.length > 128 || /[\x00-\x1f\x7f]/.test(value)) return false;
    if (value === "") return true;
    var parts = value.split(" "), ranks;
    if (parts.length !== 6) return false;
    ranks = parts[0].split("/");
    if (ranks.length !== 8 || (parts[0].match(/K/g) || []).length !== 1 || (parts[0].match(/k/g) || []).length !== 1) return false;
    if (!ranks.every(function (rank) {
      return /^[prnbqkPRNBQK1-8]+$/.test(rank) && !/[1-8]{2}/.test(rank) &&
        rank.split("").reduce(function (sum, c) { return sum + (/[1-8]/.test(c) ? Number(c) : 1); }, 0) === 8;
    })) return false;
    return /^(w|b)$/.test(parts[1]) && /^(?:-|K?Q?k?q?)$/.test(parts[2]) && parts[2] !== "" &&
      /^(?:-|[a-h][36])$/.test(parts[3]) && /^(?:0|[1-9][0-9]{0,5})$/.test(parts[4]) && /^[1-9][0-9]{0,5}$/.test(parts[5]);
  }
  function score(value) {
    if (value === null) return null;
    if (keys(value, ["cp"]) && integer(value.cp, -MAX_CP, MAX_CP)) return {cp: value.cp};
    if (keys(value, ["mate"]) && integer(value.mate, -MAX_MATE, MAX_MATE) && value.mate !== 0) return {mate: value.mate};
    return undefined;
  }
  function validate(data, startFen, moves) {
    try {
      if (!keys(data, ["schema", "start_fen", "moves", "scores", "engine"]) || data.schema !== 1 || !fen(data.start_fen)) return null;
      if (!Array.isArray(data.moves) || data.moves.length > MAX_MOVES || !data.moves.every(function (m) { return typeof m === "string" && !/[\x00-\x1f\x7f]/.test(m) && SAN.test(m); })) return null;
      if (startFen !== undefined && startFen !== null && startFen !== data.start_fen) return null;
      if (moves !== undefined && moves !== null && (!Array.isArray(moves) || moves.length !== data.moves.length || !moves.every(function (m, i) { return m === data.moves[i]; }))) return null;
      if (!Array.isArray(data.scores) || data.scores.length !== data.moves.length + 1) return null;
      var scores = data.scores.map(score);
      if (scores.some(function (s) { return s === undefined; })) return null;
      var e = data.engine;
      if (!keys(e, ["name"], ["nodes", "depth"]) || typeof e.name !== "string" || !e.name.trim() || e.name.length > 120 || /[\x00-\x1f\x7f]/.test(e.name)) return null;
      var engine = {name: e.name};
      if (Object.prototype.hasOwnProperty.call(e, "nodes")) { if (!integer(e.nodes, 1, 9007199254740991)) return null; engine.nodes = e.nodes; }
      if (Object.prototype.hasOwnProperty.call(e, "depth")) { if (!integer(e.depth, 1, 1000)) return null; engine.depth = e.depth; }
      var clean = {schema: 1, start_fen: data.start_fen, moves: data.moves.slice(), scores: scores, engine: engine};
      return bytes(JSON.stringify(clean)) <= MAX_BYTES ? clean : null;
    } catch (_) { return null; }
  }
  function parse(raw, startFen, moves) {
    if (typeof raw !== "string" || bytes(raw) > MAX_BYTES) return null;
    try { return validate(JSON.parse(raw), startFen, moves); } catch (_) { return null; }
  }
  function scoreForPly(data, ply) {
    if (!data || !Array.isArray(data.scores) || !integer(ply, 0, data.scores.length - 1)) return null;
    var result = score(data.scores[ply]);
    return result === undefined ? null : result;
  }
  function scoreLabel(value) {
    var s = score(value);
    if (!s) return ".";
    if (Object.prototype.hasOwnProperty.call(s, "mate")) return (s.mate < 0 ? "-M" : "M") + Math.abs(s.mate);
    var rounded = Math.round(Math.abs(s.cp) / 10) / 10;
    return rounded === 0 ? "0.0" : (s.cp > 0 ? "+" : "-") + rounded.toFixed(1);
  }
  function whiteFraction(value) {
    var s = score(value);
    if (!s) return 0.5;
    if (Object.prototype.hasOwnProperty.call(s, "mate")) return s.mate > 0 ? 0.98 : 0.02;
    return Math.max(0, Math.min(1, 1 / (1 + Math.exp(-s.cp / 300))));
  }
  return {MAX_BYTES: MAX_BYTES, MAX_MOVES: MAX_MOVES, validate: validate, parse: parse, scoreForPly: scoreForPly, scoreLabel: scoreLabel, whiteFraction: whiteFraction};
}));
