"""
Registers the 'Flashcard Chess' note type in Anki.
Embeds chess.js and CSS directly into the card templates so they
work offline and inside Anki's sandboxed webview.
"""

import json
import html
import os

NOTETYPE_NAME = "Chess for Anki"
# Older names this note type has shipped under. On load we rename an existing
# note type from one of these to NOTETYPE_NAME *in place*, so cards created
# before the rebrand keep working (the note type keeps its ID and all its notes).
LEGACY_NOTETYPE_NAMES = ["Flashcard Chess"]
TEMPLATE_NAME = "Chess for Anki"
FIELDS = ["Title", "PlayerColor", "MovesPGN", "Book Notes",
          "Personal Notes", "MovesFEN", "StartFEN"]


def is_chess_notetype(model):
    """Recognise imported '+' copies by schema and our template marker."""
    return isinstance(model,dict) and set(FIELDS)=={f.get('name') for f in model.get('flds',[])} and any('id="studio-fields"' in t.get('qfmt','') for t in model.get('tmpls',[]))


def sync_compatible_models(col, primary):
    # Imports can keep a compatible schema under a suffixed name and another ID.
    # Update templates in place rather than moving notes or changing scheduling.
    for model in col.models.all():
        if model['id']==primary['id'] or not is_chess_notetype(model):
            continue
        changed=model.get('css')!=primary['css'] or model['tmpls'][0]['qfmt']!=primary['tmpls'][0]['qfmt'] or model['tmpls'][0]['afmt']!=primary['tmpls'][0]['afmt']
        if changed:
            model['css']=primary['css']
            for field in ['qfmt','afmt']:
                model['tmpls'][0][field]=primary['tmpls'][0][field]
            col.models.save(model)


_web_cache = {}


def _web(filename: str) -> str:
    # Cache file contents in memory. These bundled assets never change while Anki
    # is running, yet ensure_notetype() reads them on every profile open to diff
    # against the stored note type - re-reading ~88 KB from disk on each profile
    # switch for nothing. (An add-on update requires an Anki restart, which
    # reloads this module and empties the cache, so updates still take effect.)
    cached = _web_cache.get(filename)
    if cached is None:
        path = os.path.join(os.path.dirname(__file__), "web", filename)
        with open(path, "r", encoding="utf-8") as f:
            cached = f.read()
        _web_cache[filename] = cached
    return cached


def _config_prelude() -> str:
    """Build a <style>/<script> prelude that themes the card (colors, texture,
    piece set) and enables the move/capture sounds, from the user's settings."""
    confetti_enabled = True
    notation_language = "auto"
    narration_rate = 1.5
    try:
        from . import config as cfg
        c = cfg.get_config()
        narration_rate = cfg.narration_rate(c.get("narration_rate"))
        confetti_enabled = c.get("confetti_enabled", True)
        notation_language = c.get("notation_language", "auto")
        if notation_language not in ("auto", "en", "pt"):
            notation_language = "auto"
        light, dark = cfg.board_colors(c)
        sound_on = "true" if c.get("sound_enabled", True) else "false"
        if c.get("sound_enabled", True):
            move_uri, cap_uri, chk_uri, cas_uri, mate_uri = cfg.sound_data_uris()
            mistake_uri = cfg.mistake_sound_uri()
        else:
            move_uri, cap_uri, chk_uri, cas_uri, mate_uri = "", "", "", "", ""
            mistake_uri = ""
        piece_set = c.get("piece_set", cfg.DEFAULTS["piece_set"])
        texture = cfg.texture_pattern(c.get("board_texture", "solid"))
        try:
            mistakes_limit = int(c.get("mistakes_limit",
                                       cfg.DEFAULTS["mistakes_limit"]))
        except Exception:
            mistakes_limit = 3
        if not (1 <= mistakes_limit <= 5):
            mistakes_limit = 3
        toggle_one = c.get("toggle_one_key", cfg.DEFAULTS["toggle_one_key"])
        toggle_all = c.get("toggle_all_key", cfg.DEFAULTS["toggle_all_key"])
    except Exception:
        light, dark, sound_on, move_uri, cap_uri = "#f0d9b5", "#b58863", "false", "", ""
        chk_uri, cas_uri, mate_uri, mistake_uri = "", "", "", ""
        piece_set, texture = "cburnett", ""
        toggle_one, toggle_all = "n", ","
        mistakes_limit = 3
    tex_rule = (f".sq-light,.sq-dark{{background-image:{texture};"
                f"background-size:100% 100%;}}" if texture else "")
    return (
        f"<style>:root{{--cot-light:{light};--cot-dark:{dark};}}{tex_rule}</style>\n"
        f"<script>var COT_SOUND_ENABLED={sound_on};"
        f"var COT_CONFETTI_ENABLED={json.dumps(bool(confetti_enabled))};"
        f"var CFA_NOTATION_LANGUAGE={json.dumps(notation_language)};"
        f"var CFA_NARRATION_RATE={narration_rate};"
        f"var COT_MOVE_SRC=\"{move_uri}\";"
        f"var COT_CAPTURE_SRC=\"{cap_uri}\";"
        f"var COT_CHECK_SRC=\"{chk_uri}\";"
        f"var COT_CASTLE_SRC=\"{cas_uri}\";"
        f"var COT_MATE_SRC=\"{mate_uri}\";"
        f"var COT_MISTAKE_SRC=\"{mistake_uri}\";"
        f"var COT_PIECE_SET=\"{piece_set}\";"
        f"var COT_MISTAKES_LIMIT={mistakes_limit};"
        f"var COT_TOGGLE_ONE_KEY={json.dumps(toggle_one)};"
        f"var COT_TOGGLE_ALL_KEY={json.dumps(toggle_all)};</script>\n"
    )


def _build_front() -> str:
    chess_js = _web("chess_min.js")
    pieces_js = _web("pieces.js")
    notation_js = _web("notation.js")
    speech_js = _web("speech.js")
    css = _web("card_style.css")
    front = _web("card_front.html")
    from pathlib import Path
    builtin = json.loads((Path(__file__).parent / "explanations.en.json").read_text(encoding="utf8"))
    try:
        from .language_packs import selected, selected_voice
        pack = selected()
        voice = selected_voice()
    except ImportError:
        pack = builtin
        voice = {"id":"system","language":"en-US","clips":{},"translations":{}}
    lines = [dict(line, language=pack["language"]) for line in pack["lines"]]
    if pack["id"] != builtin["id"]:
        lines += [dict(line, language=builtin["language"]) for line in builtin["lines"]]
    # Critical corrections supersede older English recordings/text packs.
    corrections = {(line["start_fen"], tuple(line["moves"])): line for line in builtin["lines"]}
    for line in lines:
        original = corrections.get((line["start_fen"], tuple(line["moves"])))
        if original and line["language"].split("-")[0] == "en":
            line["notes"] = [dict(original["notes"][i]) if original["notes"][i].get("review_override") and note["text"] != original["notes"][i]["text"] else dict(note) for i, note in enumerate(line["notes"])]
    commentary = json.dumps({"language": pack["language"], "lines": lines}, ensure_ascii=True).replace("</", "<\\/")
    narration = json.dumps(voice,ensure_ascii=True).replace("</", "<\\/")
    # Embed engine + piece SVGs before the card markup
    return (
        f"<style>{css}</style>\n"
        f"{_config_prelude()}"
        f"<script>{chess_js}</script>\n"
        f"<script>{pieces_js}</script>\n"
        f"<script>{notation_js}</script>\n"
        f"<script>{speech_js}</script>\n"
        f"<script>var CFA_COMMENTARY={commentary};</script>\n"
        f"<script>var CFA_NARRATION={narration};</script>\n"
        f"{front}"
    )


def _build_back() -> str:
    return _web("card_back.html")


def _build_css() -> str:
    return _web("card_style.css")


def ensure_notetype(col):
    existing = col.models.by_name(NOTETYPE_NAME)
    front = _build_front()
    back = _build_back()
    css = _build_css()

    # Rebrand migration: if the note type doesn't exist under the current name but
    # does under an older name, rename it in place. This keeps the same note type
    # ID, so every card the user already created stays attached and keeps working.
    renamed = False
    if existing is None:
        for legacy_name in LEGACY_NOTETYPE_NAMES:
            legacy_model = col.models.by_name(legacy_name)
            if legacy_model is not None:
                existing = legacy_model
                existing["name"] = NOTETYPE_NAME
                renamed = True
                break

    if existing is None:
        model = col.models.new(NOTETYPE_NAME)
        model["css"] = css
        for field_name in FIELDS:
            col.models.add_field(model, col.models.new_field(field_name))
        tmpl = col.models.new_template(TEMPLATE_NAME)
        tmpl["qfmt"] = front
        tmpl["afmt"] = back
        col.models.add_template(model, tmpl)
        col.models.add(model)
        sync_compatible_models(col,model)
        return model
    else:
        # IMPORTANT: only persist when something actually changed. This hook runs
        # on every profile open; unconditionally calling col.models.save() would
        # bump the note type's modification time each launch, dirtying the
        # collection so every sync has changes to push and Anki re-generates
        # cards/does DB work needlessly - which makes the whole app (and other
        # add-ons) feel slower. Comparing first keeps a steady-state launch free
        # of any collection write. (A rebrand rename above counts as a change.)
        changed = renamed

        # One-time migration: the single legacy notes field ("Extra" in the
        # oldest versions, then "Note") becomes "Book Notes". Rename it in place
        # so existing notes keep their content (Anki matches fields by name); the
        # new "Personal Notes" field is then added by the missing-fields loop.
        names = {f["name"]: f for f in existing["flds"]}
        if "Book Notes" not in names:
            legacy = names.get("Note") or names.get("Extra")
            if legacy is not None:
                try:
                    col.models.rename_field(existing, legacy, "Book Notes")
                    changed = True
                except Exception:
                    pass
        # v1_2_12 rename: "Moves" -> "MovesPGN". Same in-place mechanism as
        # the notes migration above: existing note content is preserved and
        # Anki rewrites any template references automatically.
        names = {f["name"]: f for f in existing["flds"]}
        for old_name, new_name in (("Moves", "MovesPGN"),):
            if new_name not in names and old_name in names:
                try:
                    col.models.rename_field(existing, names[old_name], new_name)
                    changed = True
                except Exception:
                    pass
        # v1_2_14: the raw-PGN field is removed entirely. It was write-only
        # provenance that no feature reads, and its full variation text made
        # move searches match every card in a family. Removed under either
        # historical name, so any old version migrates straight here.
        for dead in ("RawPGN", "PGNRaw"):
            try:
                by_name = {f["name"]: f for f in existing["flds"]}
                if dead in by_name and len(existing["flds"]) > 1:
                    col.models.remove_field(existing, by_name[dead])
                    changed = True
            except Exception:
                pass
        # Add any fields introduced by addon updates (e.g. StartFEN)
        existing_field_names = {f["name"] for f in existing["flds"]}
        for field_name in FIELDS:
            if field_name not in existing_field_names:
                col.models.add_field(existing, col.models.new_field(field_name))
                changed = True

        # Enforce FIELDS order on existing note types (v1_2_13). Repositioning
        # is content-safe: Anki remaps each field's data with it. Unknown
        # legacy fields, if any, drift to the end untouched.
        for idx, fname in enumerate(FIELDS):
            try:
                by_name = {f["name"]: f for f in existing["flds"]}
                fld = by_name.get(fname)
                if fld is not None and existing["flds"].index(fld) != idx:
                    col.models.reposition_field(existing, fld, idx)
                    changed = True
            except Exception:
                pass

        # Rewrite template/CSS only if they differ from the bundled version.
        if existing.get("css") != css:
            existing["css"] = css
            changed = True
        if existing["tmpls"][0].get("qfmt") != front:
            existing["tmpls"][0]["qfmt"] = front
            changed = True
        if existing["tmpls"][0].get("afmt") != back:
            existing["tmpls"][0]["afmt"] = back
            changed = True
        # Rebrand the card template's display name too (shown in Browse → Cards…).
        # Cards are tied to the template's position, not its name, so this is just
        # a label change and is safe for existing notes.
        if existing["tmpls"][0].get("name") != TEMPLATE_NAME:
            existing["tmpls"][0]["name"] = TEMPLATE_NAME
            changed = True

        if changed:
            col.models.save(existing)
        sync_compatible_models(col,existing)
        return existing


def simplify_start_fen(fen):
    """StartFEN storage form: placement + side to move only. Castling rights
    are assumed from placement by every consumer, so trailing fields would be
    misleading. Pasted full FENs are trimmed here so every card stores the
    same clean shape."""
    parts = (fen or "").strip().split()
    if not parts:
        return ""
    side = parts[1] if len(parts) > 1 and parts[1] in ("w", "b") else "w"
    return " ".join(parts) if len(parts)>=6 else parts[0] + " " + side


def moves_fen_text(moves, start_fen=""):
    """The MovesFEN field body: one simplified FEN per half-move, joined with
    <br> so the note editor shows one position per line. Pure searchable
    text - the card template never reads it. Empty on any replay problem
    (never store a wrong position)."""
    try:
        from . import chess_logic
        fens = chess_logic.fens_after_each(list(moves),
                                           (start_fen or "").strip() or None)
        return "<br>".join(fens) if fens else ""
    except Exception:
        return ""


def backfill_moves_fen(col):
    """One-time fill of MovesFEN on notes that predate the field. Only notes
    with an EMPTY MovesFEN are touched, so after the first pass this matches
    nothing and costs one no-op search per profile load."""
    try:
        nids = col.find_notes(f'note:"{NOTETYPE_NAME}" "MovesFEN:"')
    except Exception:
        return 0
    updated = []
    for nid in nids:
        try:
            note = col.get_note(nid)
            mv = (note["MovesPGN"] or "").split()
            if not mv:
                continue
            txt = moves_fen_text(mv, note["StartFEN"])
            if txt:
                note["MovesFEN"] = txt
                updated.append(note)
        except Exception:
            continue
    if updated:
        try:
            col.update_notes(updated)
        except Exception:
            for n2 in updated:
                try:
                    col.update_note(n2)
                except Exception:
                    pass
    return len(updated)


def create_note(col, title: str, player_color: str, moves: list,
                start_fen: str = "", book_notes: str = "", personal_notes: str = ""):
    model = ensure_notetype(col)
    note = col.new_note(model)
    note["Title"] = html.escape(title)
    note["PlayerColor"] = "black" if player_color == "black" else "white"
    note["MovesPGN"] = html.escape(" ".join(moves))
    note["MovesFEN"] = moves_fen_text(moves, start_fen)
    note["StartFEN"] = html.escape(simplify_start_fen(start_fen) or "")
    note["Book Notes"] = book_notes or ""
    note["Personal Notes"] = personal_notes or ""
    return note
