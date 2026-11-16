"""Build reviewable source for the free runtime, without paid content or private files."""
from pathlib import Path
import hashlib,zipfile,json
root=Path(__file__).resolve().parents[1];out=root/'dist/optional';out.mkdir(parents=True,exist_ok=True)
files=[p for p in (root/'chess_for_anki').rglob('*') if p.is_file() and not {'user_files','__pycache__'}&set(p.parts) and p.suffix!='.pyc' and p.name!='meta.json']
files += [root/'LICENSE',root/'CREDITS.md',root/'scripts/build_addon.py',Path(__file__)]
target=out/'Chess-for-Anki-Source.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
 for path in sorted(set(files)):archive.write(path,path.relative_to(root).as_posix())
 archive.writestr('README.md','''# Chess for Anki - runtime source

Maintained by fernandomec. This source distribution contains the free add-on runtime, its build script, license and third-party notices. Paid training data, downloaded books, user settings and development history are excluded.

Requires Python 3 to build. From this directory, run:

    python scripts/build_addon.py

The resulting dist/Chess for Anki.ankiaddon can be installed through Anki Tools > Add-ons > Install from file. The desktop add-on requires Anki26.9.4 or newer. Reproducing the voice recordings is optional; recordings and training decks are separate downloads. Build packaging uses standard-library Python only.

The current build scripts preserve local file modification timestamps in ZIP metadata, so archive byte hashes can differ after extraction and rebuilding; runtime files are unchanged.

See LICENSE and CREDITS.md for redistribution and corresponding-source terms. The distributed runtime is readable source; the separate development repository being private does not make runtime code secret.
''')
print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
