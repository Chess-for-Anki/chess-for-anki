const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const web = path.join(__dirname, '..', 'chess_for_anki', 'web');
const previous = require(path.join(web, 'previous_move.js'));
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(web, 'chess_min.js'), 'utf8'), context);
const Chess = context.Chess;

const initial = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const afterE4 = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1';
const metadata = {schema: 1, before_fen: initial, uci: 'e2e4', source: 'user'};
const parse = (data = metadata, target = afterE4) => previous.parse(JSON.stringify(data), target, Chess);

test('replays one preceding move and returns display metadata only', () => {
  for (const source of ['user', 'historical', 'constructed']) {
    assert.deepEqual(parse({...metadata, source}), {from: 'e2', to: 'e4', san: 'e4', source});
  }
  const {source, ...withoutSource} = metadata;
  assert.deepEqual(parse(withoutSource), {from: 'e2', to: 'e4', san: 'e4', source: 'user'});
  assert.deepEqual(parse(metadata, afterE4.replace('0 1', '82 99')),
    {from: 'e2', to: 'e4', san: 'e4', source: 'user'});
});

test('rejects malformed, executable, oversized and duplicate-key input', () => {
  for (const raw of [null, false, 1, {}, [], '', 'null', '[]', '[1]',
    'globalThis.previousMoveExecuted = true', '<script>alert(1)</script>',
    '{"schema":1', ' '.repeat(2049), JSON.stringify(metadata) + ' '.repeat(2049),
    '{"schema":0,"schema":1,"before_fen":' + JSON.stringify(initial) + ',"uci":"e2e4"}',
    '{"schema":1,"before_fen":' + JSON.stringify(initial) + ',"uci":"e2e3","uci":"e2e4"}',
    '{"schema":0,"\\u0073chema":1,"before_fen":' + JSON.stringify(initial) + ',"uci":"e2e4"}',
    '{"schema":1,"before_fen":' + JSON.stringify(initial) + ',"uci":"e2e3","\\u0075ci":"e2e4"}',
  ]) {
    assert.equal(previous.parse(raw, afterE4, Chess), null, String(raw));
  }
  assert.equal(globalThis.previousMoveExecuted, undefined);
  assert.equal(previous.parse(JSON.stringify(metadata), '', Chess), null);
  assert.equal(previous.parse(JSON.stringify(metadata), afterE4, null), null);
});

test('requires strict known keys, value types and a complete bounded FEN', () => {
  const invalid = [
    {...metadata, schema: true}, {...metadata, schema: '1'}, {...metadata, schema: null},
    {...metadata, schema: 2}, {...metadata, before_fen: null}, {...metadata, before_fen: 1},
    {...metadata, before_fen: false},
    {...metadata, before_fen: [initial]}, {...metadata, before_fen: initial.split(' ').slice(0, 2).join(' ')},
    {...metadata, before_fen: initial + '\n'}, {...metadata, before_fen: initial + '\0'},
    {...metadata, before_fen: initial + '\x7f'}, {...metadata, before_fen: initial.replace('rnbqkbnr', 'rnbqkbn7')},
    {...metadata, before_fen: initial.replace(' w ', ' x ')},
    {...metadata, before_fen: initial.replace(' KQkq ', ' KK ')},
    {...metadata, before_fen: initial.replace(' - ', ' e4 ')},
    {...metadata, before_fen: initial.replace(' 0 1', ' -1 1')},
    {...metadata, before_fen: initial.replace(' 0 1', ' 0 0')},
    {...metadata, before_fen: '8/8/8/8/8/8/8/8 w - - 0 1'},
    {...metadata, before_fen: ' '.repeat(129)},
    {...metadata, uci: null}, {...metadata, uci: 1234}, {...metadata, uci: false}, {...metadata, uci: ['e2e4']},
    {...metadata, uci: 'e2e2'}, {...metadata, uci: 'e2e9'}, {...metadata, uci: 'e2e4Q'},
    {...metadata, uci: 'e2e4;alert(1)'}, {...metadata, source: ''}, {...metadata, source: null},
    {...metadata, source: false}, {...metadata, source: 0}, {...metadata, source: {}}, {...metadata, source: ['user']},
    {...metadata, source: 'engine'}, {...metadata, command: 'alert(1)'},
    {...metadata, before_fen: '</script><script>alert(1)</script>'},
    JSON.parse('{"schema":1,"before_fen":' + JSON.stringify(initial) + ',"uci":"e2e4","__proto__":{"polluted":true}}'),
  ];
  for (const data of invalid) assert.equal(parse(data), null, JSON.stringify(data));
  for (const key of ['schema', 'before_fen', 'uci']) {
    const incomplete = {...metadata};
    delete incomplete[key];
    assert.equal(parse(incomplete), null, 'missing ' + key);
  }
  assert.equal({}.polluted, undefined);
});

test('rejects illegal replay, wrong side, different target and self-check', () => {
  assert.equal(parse({...metadata, uci: 'e2e5'}), null);
  assert.equal(parse({...metadata, uci: 'e7e5'}), null);
  assert.equal(parse(metadata, initial), null);
  assert.equal(parse(metadata, afterE4.replace('4P3', '3P4')), null);
  const pinned = {schema: 1, before_fen: '4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1', uci: 'e2a2'};
  assert.equal(parse(pinned, '4r1k1/8/8/8/8/8/R7/4K3 b - - 1 1'), null);
  const wrongCheck = {schema: 1, before_fen: '4k3/8/8/8/8/8/4R3/4K3 w - - 0 1', uci: 'e2a2'};
  assert.equal(parse(wrongCheck, '4k3/8/8/8/8/8/R7/4K3 b - - 1 1'), null);
});

test('replays castling and respects rights in both positions', () => {
  const data = {schema: 1, before_fen: 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 5 7', uci: 'e1g1'};
  const target = 'r3k2r/8/8/8/8/8/8/R4RK1 b kq - 6 7';
  assert.deepEqual(parse(data, target), {from: 'e1', to: 'g1', san: 'O-O', source: 'user'});
  assert.equal(parse({...data, before_fen: data.before_fen.replace(' KQkq ', ' Qkq ')}, target), null);
  assert.equal(parse({...data, before_fen: data.before_fen.replace('R3K2R', 'R3K3')}, target), null);
  assert.equal(parse(data, target.replace(' kq ', ' - ')), null);
  const throughCheck = {...data, before_fen: 'r3k2r/8/8/8/8/8/5r2/R3K2R w KQkq - 5 7'};
  assert.equal(parse(throughCheck, 'r3k2r/8/8/8/8/8/5r2/R4RK1 b kq - 6 7'), null);
});

test('replays en passant and compares only legally available EP state', () => {
  const data = {schema: 1, before_fen: '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 5', uci: 'e5d6'};
  const target = '4k3/8/3P4/8/8/8/8/4K3 b - - 0 5';
  assert.deepEqual(parse(data, target), {from: 'e5', to: 'd6', san: 'exd6', source: 'user'});
  assert.equal(parse({...data, before_fen: data.before_fen.replace(' d6 ', ' - ')}, target), null);
  assert.equal(parse({...data, before_fen: data.before_fen.replace('3pP3', '4P3')}, target), null);
  const before = '4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 4';
  const after = '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 5';
  assert.ok(parse({schema: 1, before_fen: before, uci: 'd7d5'}, after));
  assert.equal(parse({schema: 1, before_fen: before, uci: 'd7d5'}, after.replace(' d6 ', ' - ')), null);
  assert.equal(previous.positionKey(new Chess(afterE4)), previous.positionKey(new Chess(afterE4.replace(' e3 ', ' - '))));
  assert.notEqual(previous.positionKey(new Chess(after)), previous.positionKey(new Chess(after.replace(' d6 ', ' - '))));
  const pinnedEp = 'k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 5';
  assert.equal(previous.positionKey(new Chess(pinnedEp)), previous.positionKey(new Chess(pinnedEp.replace(' d6 ', ' - '))));
});

test('requires explicit legal promotion and forbids stray promotion suffixes', () => {
  const data = {schema: 1, before_fen: '4k3/P7/8/8/8/8/8/4K3 w - - 0 1', uci: 'a7a8q'};
  assert.deepEqual(parse(data, 'Q3k3/8/8/8/8/8/8/4K3 b - - 0 1'),
    {from: 'a7', to: 'a8', san: 'a8=Q+', source: 'user'});
  assert.ok(parse({...data, uci: 'a7a8n'}, 'N3k3/8/8/8/8/8/8/4K3 b - - 0 1'));
  assert.equal(parse({...data, uci: 'a7a8'}, 'Q3k3/8/8/8/8/8/8/4K3 b - - 0 1'), null);
  assert.equal(parse({...metadata, uci: 'e2e4q'}), null);
  const king = {schema: 1, before_fen: '5k2/8/8/8/8/8/8/4K3 b - - 0 1', uci: 'f8g8q'};
  assert.equal(parse(king, '6k1/8/8/8/8/8/8/4K3 w - - 1 2'), null);
});

// Pass a local sidecar as the first argument to smoke-test external contexts.
// No user content is copied into the public test fixtures.
if (process.argv[2]) {
  test('validates all 73 external setup contexts', () => {
    const sidecar = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
    assert.equal(sidecar.entries.length, 73);
    for (const entry of sidecar.entries) {
      const display = parse(entry.previous_move, entry.start);
      assert.ok(display, entry.title);
      assert.equal(display.from + display.to, entry.previous_move.uci.slice(0, 4), entry.title);
      assert.equal(display.source, entry.previous_move.source, entry.title);
    }
  });
}
