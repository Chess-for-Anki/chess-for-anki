from pathlib import Path
import ast, hashlib, json, zipfile

root = Path(__file__).resolve().parents[1]
source = root / "chess_for_anki"
target = root / "dist"
target.mkdir(exist_ok=True)
files = sorted(p for p in source.rglob("*") if p.is_file() and not ({"__pycache__", "user_files"} & set(p.parts)) and p.suffix != ".pyc" and p.name != "meta.json")
assert not any(p.name == "starter.json" or p.name.startswith("_chess_michael_") for p in files), "Starter content and narrator recordings must stay external."
for path in files:
    if path.suffix == ".py":
        ast.parse(path.read_text(encoding="utf8"), filename=str(path))
manifest = json.loads((source / "manifest.json").read_text(encoding="utf8"))
archive = target / "Chess for Anki.ankiaddon"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
    for path in files:
        bundle.write(path, path.relative_to(source).as_posix())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(target / "SHA256.txt").write_text(digest + "  " + archive.name + "\n", encoding="utf8")
print(json.dumps({"version": manifest["version"], "files": len(files), "bytes": archive.stat().st_size, "sha256": digest}))
