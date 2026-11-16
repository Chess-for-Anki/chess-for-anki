# Language pack format

Import a ZIP containing one UTF-8 pack.json and optional audio/*.mp3 files.
Packs contain declarative data. The add-on validates the archive and loads the explanations as text.

The text-only English pack is a complete example. It includes all 34 distinct starter sequences. Translations can replace each note's text while retaining its matching start_fen, moves and san values.

The root object has schema 1 or 2, an id using lowercase letters, numbers and hyphens, a BCP-47 language code, a short display name, a version and a lines array. Schema 1 remains supported for existing commentary packs.

## Schema 2 - optional recorded narrator

A schema 2 pack may add `narration` with `language` (a locale such as `en-US`), `clips` (a dictionary mapping stable canonical English speech keys to MP3 filenames) and optional `translations` (plain translated text for those keys). A voice-only pack uses an empty `lines` array; a complete pack can include both commentary lines and narration clips.

Canonical keys are the move-announcement phrases, titles, level introductions and short hints used by the card. They identify the content independently of the recorded language. A translated pack retains the keys while supplying its translated recordings and text. System speech localizes standard move/hint phrases for en, pt, es, ru, zh, ja, fr and de; custom phrase translations can be supplied by a pack.

Voice filenames may use `_cfa_voice_<hash>.mp3`; the English Michael pack also accepts the existing `_chess_michael_<hash>.mp3` names. Commentary files retain `_cfa_expl_<hash>.mp3`. All files referenced by either narration or commentary must appear under `audio/`, with no unused files.

The narrator and commentary text are selected independently. `System voice` is the default and creates no media in the collection. A recorded voice becomes selectable only when its media is installed in the current profile. Missing voice media falls back to system speech. The device must have a system voice for the chosen locale; the add-on reports when one is unavailable.

The official natural English narrator is an external ZIP. Portuguese, Spanish, Russian, Chinese, Japanese, French and German natural recordings are planned, not bundled or claimed as finished.

Build the English narrator with `python scripts/build_voice_pack.py`. Use `--commentary path/to/commentary-audio.zip` to combine the separately generated spoken explanations into the complete pack. Output ZIPs go into `dist/optional`, outside the base add-on.

## Commentary lines

Each line contains start_fen, moves and notes. An empty start_fen means the usual opening position. Each note contains san and text, plus an optional audio filename. Notes must match the exact move order and cover every move in that line. Start positions and the full saved move sequence identify the matching commentary, regardless of training depth.

Audio filenames follow _cfa_expl_<16-to-64 lowercase hexadecimal characters>.mp3. Use a hash of the language, voice and spoken text to avoid collisions. Every referenced audio file must exist in the ZIP under audio/, and every supplied audio file must be referenced. Use the same spoken text as the visible explanation.

Limits are 1000 lines, 600 moves per line, 2500 characters per explanation, 8 MB per file, 256 MB expanded per ZIP and 3000 archive entries. Executable files, scripts, absolute paths and parent-directory traversal are rejected.

The selected pack is embedded in the card template. English starter commentary supplies fallback lines when a translation covers only part of the starter collection. A custom imported line needs a matching commentary entry. The add-on displays an availability message when no entry exists.

The import writes MP3s through Anki's media manager, then commits pack metadata atomically. A failure during media installation can leave unreferenced media. The previous selected pack remains active until the new pack has been fully installed.

Installed metadata stays under user_files/language_packs and is excluded from the add-on release. Cards and audio can sync through AnkiWeb. Import the pack ZIP on each desktop to select and rebuild its commentary there.
