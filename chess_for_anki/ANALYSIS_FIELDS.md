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

## Retired analysis metadata

The evaluation meter has been removed. The card template does not load, parse
or display position analysis, and Settings has no evaluation-meter option.

Existing notes keep their `Position Evaluation` field so imports and note-type
updates remain compatible without a destructive schema change. Its validation
API is retained for older callers, but the field has no visible effect.

## Local verification

Run the Python and Node unit tests, then test a curated exercise pack in an
isolated profile:

```text
python -m unittest discover -s tests -p "test_*.py"
node tests/test_brilliant.cjs
python scripts/verify_brilliancy.py --pack PATH_TO_PRIVATE_EXERCISES_JSON --output QA_OUTPUT_FOLDER
```

The native probe never opens a personal collection. It checks real card
rendering, wrong/correct moves, demo rewinds, sound dispatch, preference
switches, final-ply rewards, both board orientations, absence of the retired meter on question/answer
sides, and in-place schema migration. It exports its eight-card
exercise set only to the selected local output folder. Paid exercise content
and engine binaries are separate from the add-on and its source archive.
