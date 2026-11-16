# Train with Chess for Anki

The 1.6.0 preview includes a separate free sample of **22 cards**, checked through isolated export, reimport and board tests. Installing the extension creates no cards; import the separate `.apkg` or create your own material.

## Choose a lesson

The sample has five opening lessons for both sides, plus three examples each of Brilliancy, endgames, middlegame decisions and tactics. Opening families are the Italian Game, Queen's Gambit Declined, Scotch Game, London System and Sicilian Defence.

Opening lessons stop at a useful transition to a middlegame plan. There is no universal move that ends an opening. These are prepared examples with explanations, not complete repertoires. Another legal move may also be good chess.

The older 30-card Foundations and 60-card Starter remain available as [earlier free downloads](decks/README.md).

## Understand, then recall

Use **Next move** and **Previous move** to step through the demonstration. Read the explanation and ask what changed: development, central control, a threat, king safety or the pawn structure.

Choose **Start practice**. Select or drag a piece; the opponent supplies the next saved reply. **Show demo** reopens the explanation, and **Resume practice** returns to the attempt. Revealing a move or using a hint makes that attempt assisted.

**Restart** retries now. **End round** ends an unfinished attempt and reveals the answer. **Repeat later** uses Anki's Again rating.

## Starting context

Custom-position exercises show the move that led to the starting position. **Previous move** identifies recorded or user-supplied context; **Setup move** identifies a legal constructed setup, without claiming it was historically played.

The setup move is not part of the solution and does not increase its depth. New custom cards require this context. A setup PGN supplies it automatically; for a FEN or manually placed position, provide the preceding full FEN, the opponent's coordinate move and the appropriate source label. Changing the position or player colour can invalidate the context.

## Levels and rating

| Opening level | Moves per side |
| --- | --- |
| Noobie | 4 |
| Beginner | 8 |
| Intermediate | 12 |
| Advanced | 20 |
| HACKER | Full saved line |

Short lines stop at their actual end. Custom-position exercises use the full continuation. Three different sufficiently long lines, completed without assistance and rated Good or Easy, advance the opening level. Branches with the same rehearsed prefix count once.

- **Again:** you forgot or needed to see the answer.
- **Hard:** correct recall with substantial difficulty.
- **Good:** correct recall with ordinary effort.
- **Easy:** immediate, confident recall.

Rate independent recall. Completing the sequence after hints does not mean you recalled it unaided.

## Brilliancy and other exercises

The turquoise `!!` marks a curated key move. It is an editorial teaching annotation, not automatic analysis of every move you play. Highlight, sound and particles have separate Settings controls; sound also follows the main sound switch.

Some endgame and middlegame exercises accept equivalent moves. The answer can show one model continuation without proving it is unique. Read the task and notes. A short endgame decision does not teach the entire technique.

## Make your own cards

Choose **Chess for Anki > Create cards / Import PGN**. Set a title, deck and playing colour. Use **Opening** for the usual position; paste PGN or use **Manual Input**.

For a custom exercise, choose your colour first and select **Custom**. Paste a setup PGN ending just before your first solution move, or use FEN/**Manual Edit** and fill the previous-move fields. Enter the solution separately in **Moveset PGN**. Only share content you have the right to distribute.

Start with few new lessons. Review missed explanations, play ordinary games and inspect where a prepared line stopped being useful.

## Voice and help

Basic speech depends on installed device voices. Natural English narration is an optional separate import; missing recordings can use system speech. Other natural voices are planned. Adjust speed, sounds, effects and demonstrations in Settings.

[Report a problem](https://github.com/Chess-for-Anki/chess-for-anki/issues) with versions, steps and a screenshot without personal information. Extended packs and PRO are prepared but are not on sale. Creating and importing your own PGN remains part of the free core.
