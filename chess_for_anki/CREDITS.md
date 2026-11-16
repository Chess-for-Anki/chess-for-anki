# Credits and license

Chess for Anki is maintained by fernandomec. The independent integration, physical-board design, recorded narrator, level progression, demonstration mode and additional controls were developed for this distribution.

The PGN importer, board editor, chess rules implementation, base card templates and configuration utilities derive from **Flashcard Chess**, AnkiWeb add-on 228541832. Original authors retain copyright in their contributions. Source package obtained from AnkiWeb. Its distributed files contained no explicit license notice. AnkiWeb's published terms state that shared add-ons without an explicit license are assumed to be AGPL3.

- Original add-on - https://ankiweb.net/shared/info/228541832
- Original project - https://flashcardchess.net
- AnkiWeb terms - https://ankiweb.net/account/terms

This derivative distribution is provided under **GNU Affero General Public License version 3**. Its complete corresponding source is included as Python, JavaScript, HTML and CSS files in the archive. The Flashcard Chess code retains its original comments and structure where applicable.

The physical Staunton piece images are by **CubesAndPi**, from the Lichess project, under **AGPLv3+**. The supplied opening definitions are from **lichess-org/chess-openings**, under **CC0-1.0**.

- Pieces - https://github.com/lichess-org/lila/tree/master/public/images/staunton/piece/CubesAndPi
- Lichess resource licenses - https://github.com/lichess-org/lila/blob/master/COPYING.md
- Opening database - https://github.com/lichess-org/chess-openings

Bundled piece sounds come from the Flashcard Chess distribution. The optional English narration MP3s were generated locally using **Kokoro-en-v0_19**, voice **Michael**, through Sherpa-ONNX. The speech model is distributed under Apache-2.0. Recordings are delivered as a separate voice pack; the base add-on contains neither these recordings nor the model or speech runtime.

The brilliant-move celebration chime is an original synthesized sound. Its reproducible generator is included as `scripts/build_brilliant_sound.py` in the source repository. No Witty Alien, Street Fighter or other third-party voice sample is bundled. The turquoise highlight and `!!` badge are drawn in CSS and text; no Chess.com badge artwork is included.

- Kokoro model and voices - https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/kokoro.html

Classic game scores are Anderssen–Kieseritzky (1851), Anderssen–Dufresne (1852), and Donald Byrne–Bobby Fischer (1956). Source links for the historical move records are included in the starter notes. Their explanatory practice notes were written for this collection.
