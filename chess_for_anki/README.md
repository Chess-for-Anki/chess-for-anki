# Chess for Anki

Practise a saved chess line on an interactive Anki card. Drag a piece or click its origin and destination; the opponent replies from that line. Maintained by **fernandomec**.

## Get started with the 1.6.0 preview

The preview and its sample are available as separate downloads in [1.6.0-preview](https://github.com/Chess-for-Anki/chess-for-anki/releases/tag/v1.6.0-preview).

1. Install the `.ankiaddon` through **Tools > Add-ons > Install from file**, then restart Anki.
2. Choose **Download free starter deck (.apkg)** on Home. Import **Chess-for-Anki-Free-Sample.apkg** through **File > Import**. Installation itself creates no cards.
3. Open **Chess - Free Sample** and choose a lesson. Use **Next move** to inspect the demonstration, then **Start practice**.

The sample has **22 cards**: five opening lessons for both sides, three Brilliancy, three endgames, three middlegame decisions and three tactics. The openings are Italian Game, Queen's Gambit Declined, Scotch Game, London System and Sicilian Defence. They reach a useful middlegame transition; they are not complete repertoires or forced sequences.

Foundations and Starter remain available through the [earlier free downloads](https://github.com/Chess-for-Anki/chess-for-anki/tree/downloads/decks).

## Practice and recall

A correct move is followed by the saved opponent reply. Another legal move may also be good chess.

- **Show demo:** reopen the explanation.
- **Resume practice:** return to the attempt.
- **Restart:** retry immediately.
- **End round:** end an unfinished attempt and reveal the answer.
- **Repeat later:** use Anki's Again rating.

Hints and demonstrations make an attempt assisted. Rate independent recall: Again for forgotten, Hard for difficult correct recall, Good for normal recall and Easy for immediate confident recall.

Opening levels allow 4, 8, 12, 20 or all saved moves per side. Short lines stop at their actual end. Three different sufficiently long lines completed without assistance and rated Good or Easy advance the level. Custom exercises use the full saved continuation.

A turquoise `!!` can reward a curated key move. It is a teaching annotation, not live engine analysis. Highlight, particles and sound can be disabled separately in Settings; sound also respects **Piece sounds**.

## Starting context and your own cards

**Create cards / Import PGN** remains part of the free core. Choose a deck, title and playing colour. For a normal opening, paste PGN in **Moveset PGN** or use **Manual Input**.

For a custom exercise, choose the colour first. Paste the moves leading to the exercise in **Starting Position PGN/FEN**, stopping after the opponent's last move. The form fills the position and previous-move context automatically.

For FEN or **Manual Edit**, fill the preceding full FEN and the opponent's coordinate move, such as `e7e5`. Choose **Constructed setup move** for a legal composition rather than recorded history. New custom cards require context matching their starting position. Changing the position or colour can clear it.

**Previous move** or **Setup move** highlights the move before the solution. It does not become an extra solution move. Existing imported cards and their scheduling are preserved.

## Speech and settings

System speech requires an installed device voice. Natural [English Michael narration](https://github.com/Chess-for-Anki/chess-for-anki/releases/download/v1.4.2-preview/English-Michael-Voice-Pack.zip) is a separate optional ZIP imported through **Language packs**. Unrecorded phrases can use system speech. Other natural voices are planned; Hindi needs runtime support.

Text and narrator are selected separately. Settings also provides narration speed, first-view demo, notation, piece sounds and completion confetti.

## Help and compatibility

[Project and downloads](https://github.com/Chess-for-Anki/chess-for-anki) · [Report a problem](https://github.com/Chess-for-Anki/chess-for-anki/issues) · [Support the project](https://github.com/Chess-for-Anki/chess-for-anki/blob/downloads/SUPPORT.md)

Extended packs and PRO are being prepared; no sales checkout is active. The free core and previously distributed material remain available. Remove personal information from public bug reports.

Windows with Anki desktop 26.9.4 is the tested environment; this preview passed isolated collection, importer and board checks. macOS, Linux and mobile compatibility have not been established. Install the add-on on each desktop. Cards and media can sync through AnkiWeb.

Source is included. See **LICENSE** and **CREDITS.md** for AGPL-3.0 terms and third-party attribution.
