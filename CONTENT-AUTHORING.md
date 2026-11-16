# Lesson authoring rules

Every exercise that starts after the initial position must include the
opponent's preceding move. Save its full preceding FEN and UCI move in the
`Previous Move` field. Replaying it must produce the exercise's initial
position, with the correct side, castling rights and legal en passant state.

The card highlights both origin and destination before the first attempt,
at the start of the demo, after rewinding to the start, and when reviewing the
starting position. It does not include a solution move in that highlight.

When a PGN setup is available, retain its actual mainline and final move. A
bare FEN does not identify the preceding move. For a composed position, author
a legal one-move setup and select `constructed`; the card labels it **Setup
move** rather than presenting it as a historical game record. Never invent
an unlabelled history for an existing position.

New custom-position cards must pass this check before saving. Updating old
models preserves their IDs and scheduling; an empty legacy field must not
cause a fabricated highlight. The maintained lesson catalogue is checked
separately so each custom-position exercise has validated context.

Every lesson also needs legal SAN, the correct learner side, an explanation
of the objective, and a statement of known limitations. A brilliant marker
is curated teaching metadata, not an automatic engine classification.
Preserve source and license notices. Do not copy book annotations or diagrams
into a commercial package without permission.

Opening lessons contain a selected complete training line through a stated
transition to the middlegame. They do not claim to cover every opening branch
or to be forced against every possible reply. Card counts include both-side
perspectives where offered; distinguish those from unique lessons.
