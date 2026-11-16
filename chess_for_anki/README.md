# ♟️ Chess for Anki

Maintained by **fernandomec**.

Play a complete line on each flashcard. Move pieces by dragging or clicking. The opponent replies with the next move in the saved line. Use Anki's ratings to schedule the next review.

## Getting started

1. In desktop Anki, open **Tools → Add-ons → Install from file…**, choose the `.ankiaddon` file and restart Anki. This guide opens on your first launch with the add-on. You can read it again under **♟️ Chess for Anki → Guide and credits**.
2. Installation creates no cards or chess deck. Choose **Download free starter deck (.apkg)** on the Home screen, download **Chess-for-Anki-Foundations.apkg** with 30 cards, and import it through **File → Import**. The earlier free **Chess-for-Anki-Starter.apkg** with 60 cards is a separate download from the [community releases](https://github.com/fernandomec/chess-for-anki-community/releases/tag/v1.4.2-preview). Alternatively, choose **Create my own cards** to build your own deck.
3. Open **Chess → 01 - Foundations → 01 - Openings → White → Study Now**. On your first chess card, select **Start round**. If the demo is enabled, choose **Next move** for each move or **Start practice** to play immediately.

Both first-use screens have an **Open settings** button. Later, open **♟️ Chess for Anki → Settings** in Anki’s top menu. Here you can change the starting level, first-view demo, piece sounds and **Confetti on completion**. After a successful round, **Congratulations!** appears. Turning off confetti keeps the message and removes the animation.

### Play your first moves

On the Foundations card **Italian - central break · White**, click the pawn on **e2**, then **e4**. Black replies **e7–e5**. Move your knight **g1–f3**, your bishop **f1–c4**, then your pawn **c2–c3**, waiting for Black's reply each time. At Noobie depth the round ends after Black's fourth move, **Nf6**. Other cards follow their own recorded lines.

If you forget a move, choose **End round**, then **Repeat later** on the answer side. If you want to retry immediately, use **Restart** during the attempt. After a completed round, use the arrows or click the notation to revisit the position, then choose your Anki rating.

### Create a practice card

Choose **Create cards / Import PGN**, select a deck under **Add to Deck**, enter a **Title**, and pick **White** and **Opening**. Paste `1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. Nc3 Nf6` in **Moveset PGN**, then click **Add**. To enter moves by playing both sides, use **Manual Input → Set**. To create a mate exercise, use **Custom → Manual Edit** to set the starting position, then enter its solution.

To load a PGN file from disk, choose **Import** in the **Moveset PGN** section.

## Training

During a demonstration, every move in the earlier 60-card starter collection has an explanation of its purpose and its role in the line. That commentary follows all 551 distinct move positions across the opening lines, historic games and mate exercises. The two playing sides reuse the same explanations. Historic games include imperfect decisions by the players, so their recorded moves are discussed as played continuations.

### Optional languages and spoken commentary

The base add-on starts with **System voice**, using Anki's device speech synthesis. An installed system voice for the selected language is required. No natural recordings are bundled or copied to your collection on startup. English commentary text remains included as a small fallback.

For the natural English narrator and explanations, download **English-Michael-Voice-Pack.zip** and import it under **♟️ Chess for Anki → Language packs**. This optional ZIP contains the recorded move announcements, hints and starter commentary. The saved voice speed applies to all narration.

Select commentary text and narrator separately in that dialog. Basic spoken languages are English, Portuguese, Spanish, Russian, Chinese, Japanese, French and German, subject to installed system voices. Natural recordings for languages other than English are planned and are not yet available. Additional translations and voices use declarative JSON/MP3 ZIPs, without executable installers. Imported audio becomes Anki media and syncs through AnkiWeb. Import a voice ZIP in each profile where you want to use it.

### Message history and notation

**Message history** on the board reopens move announcements, explanations and hints from the current round. It remains available when you restart the attempt or reveal the answer. Opening another card begins a new history.

Choose **Settings → Chess notation language** to use English initials (K Q R B N) or Portuguese initials (R D T B C). **Follow commentary language** uses the selected language pack. The display keeps pawn moves without a piece initial and uses 0-0 / 0-0-0 for castling. PGN files retain standard English SAN for interoperability.

The move list, demonstration labels and history use this setting. Commentary retains the language of the installed text pack. The optional Michael recordings are English.

### Feedback

Open **♟️ Chess for Anki → Feedback / Report an issue** to describe an error and attach an image. The form shows a screenshot preview and normalizes accepted PNG, JPEG or WebP images to PNG. It does not create or send ZIP reports.

**Review and submit on GitHub** opens the project's issue page with your text prepared. If an image is attached, it is copied to the clipboard: paste it into the GitHub editor, review and submit the issue. For a very long report, the full text is copied instead; paste it first, then return to **Copy screenshot**. **View reported issues** opens the reports directly in the browser. The author can read text and view screenshots inline without downloading an archive. Posting a report requires a GitHub account; free downloads are public.

Image size/format checks, re-encoding and plain-text handling reduce risks; they are not antivirus scanning or a guarantee that arbitrary attachments posted directly on GitHub are safe. GitHub notifications and email delivery depend on the repository watch settings and the author's account preferences.

- Noobie - up to 4 moves per side.
- Beginner - up to 8 moves per side.
- Intermediate - up to 12 moves per side.
- Advanced - up to 20 moves per side.
- HACKER - the entire saved line.

Short lines finish at their last available move. Your selected level carries over to the next card. On desktop, three different lines completed at the requested depth without hints and rated Good or Easy promote you to the next level.

**Demo on first view** opens the full line at the starting position. **Next move** reveals one move by White or Black per click. **Previous move** goes back one ply, restoring the board and the explanation for that position. During an attempt, **Show demo** reopens the line from the beginning. **Resume practice** returns to the position you were solving. Revealing a move counts as assistance for that attempt.

**End round** reveals the answer after an incomplete attempt. **Repeat later** submits Again to Anki. **Restart** starts the current attempt over. The move history and arrow buttons replay moves with animation.

Choose **Voice speed** beside **Voice on/off**, or open **♟️ Chess for Anki → Settings → Narration speed**. Available speeds range from 0.5× to 2×, with 1.5× as the default. The choice is saved on this computer and applies to announcements, hints and spoken explanations while preserving the pitch of recorded speech. System speech is the default; the optional natural voice falls back to system speech for unrecorded phrases.

## Sync and compatibility

Cards, audio and collection settings synchronize through AnkiWeb. Install Chess for Anki on each desktop to use automatic progression and collection-backed first-view tracking. The desktop add-on itself runs only in desktop Anki. Mobile rendering and audio have not been validated. This release is tested on Windows with Anki 26.09.4; macOS and Linux have not been validated.

Before migrating from the separate Flashcard Chess and Chess Studio add-ons, disable those two and restart. Chess for Anki upgrades the existing Flashcard Chess note type in place, retaining its note and card IDs.

If using Loadout, exclude the retired add-on folders `228541832` and `fernando_chess_studio` from mirroring on each computer to avoid reactivating them. Install this single package on your other desktop and sync Anki normally.

## Support

[Support the project](https://github.com/fernandomec/chess-for-anki-community/blob/downloads/SUPPORT.md)

Source code is included in the add-on archive. See **CREDITS.md** and **LICENSE** for attribution and redistribution terms.
