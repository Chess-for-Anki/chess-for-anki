# Curated tactics and prepared evaluations

These optional fields extend the existing note type in place. Existing note IDs,
card IDs and scheduling are preserved. Old cards leave both fields empty.

## Brilliant Moves

```json
{"schema":1,"plies":[1,3]}
```

Plies are one-based half-moves from this card's starting position. The importer
provides **Brilliant move numbers** for authoring this field. Mark only checked
learner moves with a clear explanation. The label is a teaching choice, not an
automatic Chess.com classification. Wrong moves, demonstrations, automatic
replies and equivalent alternate finishes do not receive this reward.

The field accepts at most 600 unique in-range integers and 8 KiB of JSON.
Invalid imported metadata silently disables its effects in the card; the
authoring API rejects invalid metadata before writing a note.

## Position Evaluation

```json
{"schema":1,"start_fen":"","moves":["e4","e5"],"scores":[{"cp":0},null,{"cp":15}],"engine":{"name":"Example engine","nodes":60000}}
```

The numbers above illustrate the format, not actual engine analysis. A real
author must run an engine and record its results. This optional field is
limited to 256 KiB, 600 moves and one score for the initial position plus each
half-move. SAN and the stored starting FEN must match the card exactly.

All scores use White's perspective. A pawn is 100 centipawns (`cp`). A positive
`mate` is a forced mate for White; a negative value is a forced mate for Black.
Use `null` for an unanalysed position. Mate zero has no winner sign and is
rejected. The local authoring workflow encodes terminal checkmates as signed
100000 cp, and the card displays `1-0` or `0-1` only for a canonical SAN mate.

The displayed bar is a bounded visualization of the evaluation. It is neither
a win probability nor a database success percentage. Analysis budgets and
depth affect reliability. An absent field hides the bar. A missing score,
changed line, unknown branch or mismatched position never produces an invented
score. Repeated positions are indexed by half-move as well as FEN.

JSON is parsed as data. Engine names and labels are rendered with textContent.
Use `note_type.create_note(..., position_evaluation=data)` to validate and
serialize data safely; do not insert arbitrary note text into a script.

## Local verification

Run the Python and Node unit tests, then test a curated exercise pack in an
isolated profile:

```text
python -m unittest discover -s tests -p "test_*.py"
node tests/test_brilliant.cjs
node tests/test_evaluation.cjs
python scripts/verify_brilliancy.py --pack PATH_TO_PRIVATE_EXERCISES_JSON --output QA_OUTPUT_FOLDER
```

The native probe never opens a personal collection. It checks real card
rendering, wrong/correct moves, demo rewinds, sound dispatch, preference
switches, final-ply rewards, both board orientations, repeated positions,
unanalysed branches and in-place schema migration. It exports its eight-card
exercise set only to the selected local output folder. Paid exercise content
and engine binaries are separate from the add-on and its source archive.
