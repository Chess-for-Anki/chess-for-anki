const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const evaluation = require('../chess_for_anki/web/evaluation.js');
function payload() {
  return {schema: 1, start_fen: '', moves: ['e4', 'e5'], scores: [{cp: 0}, null, {mate: -3}], engine: {name: 'Stockfish 19', nodes: 100000, depth: 18}};
}
const raw = JSON.stringify(payload());
const data = evaluation.parse(raw, '', ['e4', 'e5']);
assert.deepEqual(data, payload());
assert.equal(evaluation.parse(raw, '', ['e4', 'c5']), null);
assert.equal(evaluation.parse(raw, 'mismatched FEN', ['e4', 'e5']), null);
assert.deepEqual(evaluation.scoreForPly(data, 0), {cp: 0});
assert.equal(evaluation.scoreForPly(data, 1), null);
assert.deepEqual(evaluation.scoreForPly(data, 2), {mate: -3});
for (const ply of [-1, 3, 0.5, NaN]) assert.equal(evaluation.scoreForPly(data, ply), null);
for (const [score, label] of [[{cp: 120}, '+1.2'], [{cp: -50}, '-0.5'], [{cp: 0}, '0.0'], [{mate: 3}, 'M3'], [{mate: -3}, '-M3'], [null, '.']]) assert.equal(evaluation.scoreLabel(score), label);
assert.equal(evaluation.whiteFraction({cp: 0}), 0.5);
assert(evaluation.whiteFraction({cp: 300}) > 0.5);
assert(evaluation.whiteFraction({cp: -300}) < 0.5);
assert.equal(evaluation.whiteFraction({mate: 3}), 0.98);
assert.equal(evaluation.whiteFraction({mate: -3}), 0.02);
assert.equal(evaluation.whiteFraction({cp: 1000000}), 1);
assert.equal(evaluation.whiteFraction(null), 0.5);
for (const score of [{cp: true}, {cp: 1.5}, {cp: NaN}, {mate: 0}, {cp: 2, mate: 3}]) {
  const bad = payload(); bad.scores[0] = score;
  assert.equal(evaluation.validate(bad), null);
}
for (const change of [d => d.scores.pop(), d => d.engine.command = 'execute', d => d.engine.nodes = -1, d => d.moves[0] = 'e4\n', d => d.start_fen = '<script>']) {
  const bad = payload(); change(bad); assert.equal(evaluation.validate(bad), null);
}
const tooLong = payload(); tooLong.moves = Array(601).fill('e4'); tooLong.scores = Array(602).fill(null);
assert.equal(evaluation.validate(tooLong), null);
assert.equal(evaluation.parse(' '.repeat(evaluation.MAX_BYTES + 1)), null);
assert.equal(evaluation.parse('globalThis.injected = true'), null);
assert.equal(evaluation.parse('{"__proto__":{"polluted":true}}'), null);
assert.equal({}.polluted, undefined);
const copy = evaluation.validate(data); copy.scores[0].cp = 50;
assert.equal(data.scores[0].cp, 0);
const scope = {}; vm.createContext(scope);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../chess_for_anki/web/evaluation.js'), 'utf8'), scope);
assert(scope.CFA_EVALUATION.parse(raw, '', ['e4', 'e5']));
console.log('Evaluation identity, score indexing, labels, fractions, limits and inert JSON passed.');
