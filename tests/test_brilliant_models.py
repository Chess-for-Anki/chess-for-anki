"""Exercise in-place schema migration using a small Anki model-manager double."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_note_type():
    package_name = "_brilliant_model_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT / "chess_for_anki")]
    sys.modules[package_name] = package
    name = package_name + ".note_type"
    spec = importlib.util.spec_from_file_location(name, ROOT / "chess_for_anki" / "note_type.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._original_build_front = module._build_front
    module._build_front = lambda: '<div id="studio-fields">{{Brilliant Moves}}{{Position Evaluation}}</div>'
    module._build_back = lambda: "updated answer"
    module._build_css = lambda: "updated css"
    module.moves_fen_text = lambda *args: "saved positions"
    return module


def model(module, ident, name, fields=None, marker=True):
    return {
        "id": ident,
        "name": name,
        "flds": [{"name": field, "ord": i}
                 for i, field in enumerate(fields if fields is not None else module.LEGACY_FIELDS)],
        "css": "old css",
        "tmpls": [{"name": "old template", "ord": 0,
                   "qfmt": '<div id="studio-fields"></div>' if marker else "unrelated",
                   "afmt": "old answer"}],
    }


class FakeModels:
    def __init__(self, collection, models):
        self.collection = collection
        self.items = models
        self.saves = []
        self.added_fields = []

    def by_name(self, name):
        return next((item for item in self.items if item["name"] == name), None)

    def all(self):
        return list(self.items)

    def new(self, name):
        return {"id": max((m["id"] for m in self.items), default=0) + 1,
                "name": name, "flds": [], "tmpls": []}

    def new_field(self, name):
        return {"name": name}

    def add_field(self, item, field):
        field["ord"] = len(item["flds"])
        item["flds"].append(field)
        self.added_fields.append((item["id"], field["name"]))
        for note in self.collection.notes:
            if note["mid"] == item["id"]:
                note["fields"].setdefault(field["name"], "")

    def reposition_field(self, item, field, index):
        item["flds"].remove(field)
        item["flds"].insert(index, field)
        for ordinal, entry in enumerate(item["flds"]):
            entry["ord"] = ordinal

    def new_template(self, name):
        return {"name": name, "ord": 0}

    def add_template(self, item, template):
        item["tmpls"].append(template)

    def add(self, item):
        self.items.append(item)

    def save(self, item):
        # A copied template must never reference a missing field.
        for template in item["tmpls"]:
            for field in ("Brilliant Moves", "Position Evaluation"):
                if "{{" + field + "}}" in template["qfmt"]:
                    assert field in {entry["name"] for entry in item["flds"]}
        self.saves.append(item["id"])


class FakeCollection:
    def __init__(self, models, notes=None, cards=None):
        self.notes = notes or []
        self.cards = cards or []
        self.models = FakeModels(self, models)
        self.notes_created = 0

    def new_note(self, item):
        self.notes_created += 1
        return {field["name"]: "" for field in item["flds"]}


class BrilliantModelTests(unittest.TestCase):
    def setUp(self):
        self.module = load_note_type()

    def test_old_new_and_custom_field_models_are_recognized_by_marker(self):
        for fields in (self.module.LEGACY_FIELDS,
                       self.module.LEGACY_FIELDS + ["Brilliant Moves"], self.module.FIELDS,
                       self.module.LEGACY_FIELDS + ["My extra field"]):
            with self.subTest(fields=fields):
                self.assertTrue(self.module.is_chess_notetype(
                    model(self.module, 1, "Imported name+", fields)))
        self.assertFalse(self.module.is_chess_notetype(
            model(self.module, 2, "Chess for Anki", marker=False)))
        self.assertFalse(self.module.is_chess_notetype(
            model(self.module, 3, "Chess for Anki", self.module.LEGACY_FIELDS[:-1])))

    def test_upgrade_preserves_ids_scheduling_and_note_content(self):
        primary = model(self.module, 101, self.module.NOTETYPE_NAME)
        imported = model(self.module, 202, "Chess for Anki+",
                         self.module.LEGACY_FIELDS + ["My extra field"])
        unrelated = model(self.module, 303, "Chess for Anki++", marker=False)
        notes = [{"id": 501, "mid": 101, "guid": "original-guid",
                  "fields": {"Title": "Existing title", "Personal Notes": "Keep this"}},
                 {"id": 502, "mid": 202, "guid": "imported-guid",
                  "fields": {"Title": "Imported title", "My extra field": "Keep extra"}}]
        cards = [{"id": 601, "nid": 501, "queue": 2, "due": 100,
                  "ivl": 14, "reps": 6, "lapses": 1},
                 {"id": 602, "nid": 502, "queue": 2, "due": 104,
                  "ivl": 30, "reps": 12, "lapses": 0}]
        before_notes, before_cards, before_unrelated = deepcopy(notes), deepcopy(cards), deepcopy(unrelated)
        col = FakeCollection([primary, imported, unrelated], notes, cards)
        result = self.module.ensure_notetype(col)
        self.assertIs(result, primary)
        self.assertEqual([item["id"] for item in col.models.all()], [101, 202, 303])
        self.assertEqual(col.cards, before_cards)
        self.assertEqual(col.notes_created, 0)
        for before, after in zip(before_notes, col.notes):
            expected = deepcopy(before)
            expected["fields"]["Brilliant Moves"] = ""
            expected["fields"]["Position Evaluation"] = ""
            self.assertEqual(after, expected)
        self.assertEqual(unrelated, before_unrelated)
        self.assertEqual(col.models.added_fields, [(101, "Brilliant Moves"), (101, "Position Evaluation"),
                                                  (202, "Brilliant Moves"), (202, "Position Evaluation")])
        self.assertEqual(imported["tmpls"][0]["qfmt"], primary["tmpls"][0]["qfmt"])
        first_saves = list(col.models.saves)
        self.module.ensure_notetype(col)
        self.assertEqual(col.models.saves, first_saves)
        self.assertEqual(len(col.models.added_fields), 4)

    def test_missing_primary_migrates_imported_copy_without_moving_its_notes(self):
        imported = model(self.module, 202, "Chess for Anki+")
        col = FakeCollection([imported], [{"id": 502, "mid": 202, "fields": {"Title": "Keep"}}])
        primary = self.module.ensure_notetype(col)
        self.assertNotEqual(primary["id"], imported["id"])
        self.assertEqual(col.notes, [{"id": 502, "mid": 202,
                                      "fields": {"Title": "Keep", "Brilliant Moves": "",
                                                 "Position Evaluation": ""}}])
        self.assertEqual(imported["tmpls"][0]["qfmt"], primary["tmpls"][0]["qfmt"])

    def test_legacy_named_model_is_upgraded_in_place(self):
        legacy = model(self.module, 101, "Flashcard Chess")
        col = FakeCollection([legacy])
        result = self.module.ensure_notetype(col)
        self.assertIs(result, legacy)
        self.assertEqual(result["id"], 101)
        self.assertEqual(result["name"], self.module.NOTETYPE_NAME)
        self.assertEqual(len(col.models.all()), 1)

    def test_intermediate_imported_schema_adds_only_missing_evaluation_field(self):
        primary = model(self.module, 101, self.module.NOTETYPE_NAME, self.module.FIELDS)
        imported = model(self.module, 202, "Chess for Anki+",
                         self.module.LEGACY_FIELDS + ["Brilliant Moves"])
        annotation = '{"schema":1,"plies":[2]}'
        note = {"id": 502, "mid": 202, "fields": {"Brilliant Moves": annotation}}
        col = FakeCollection([primary, imported], [note])
        self.module.ensure_notetype(col)
        self.assertEqual(col.models.added_fields, [(202, "Position Evaluation")])
        self.assertEqual(note, {"id": 502, "mid": 202,
                                "fields": {"Brilliant Moves": annotation,
                                           "Position Evaluation": ""}})

    def test_existing_annotations_and_custom_fields_are_not_overwritten(self):
        primary = model(self.module, 101, self.module.NOTETYPE_NAME, self.module.FIELDS)
        annotation = '{"schema":1,"plies":[2]}'
        note = {"id": 501, "mid": 101,
                "fields": {"Brilliant Moves": annotation, "Personal Notes": "Keep",
                           "Position Evaluation": "existing evaluation"}}
        col = FakeCollection([primary], [note])
        self.module.ensure_notetype(col)
        self.assertEqual(note["fields"]["Brilliant Moves"], annotation)
        self.assertEqual(note["fields"]["Personal Notes"], "Keep")
        self.assertEqual(note["fields"]["Position Evaluation"], "existing evaluation")
        self.assertEqual(col.models.added_fields, [])

    def test_create_note_defaults_to_blank_and_canonicalizes_metadata(self):
        col = FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])
        plain = self.module.create_note(col, "Example", "white", ["e4", "e5"])
        self.assertEqual(plain["Brilliant Moves"], "")
        self.assertEqual(plain["Position Evaluation"], "")
        for value in ({"schema": 1, "plies": [2, 1]}, '{"schema":1,"plies":[2,1]}'):
            with self.subTest(value=value):
                note = self.module.create_note(col, "Example", "white", ["e4", "e5"],
                                               brilliant_moves=value)
                self.assertEqual(note["Brilliant Moves"], '{"schema":1,"plies":[1,2]}')
                self.assertEqual(note["MovesPGN"], "e4 e5")

    def test_invalid_metadata_is_rejected_before_touching_collection(self):
        col = FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])
        with self.assertRaises(ValueError):
            self.module.create_note(col, "Example", "white", ["e4", "e5"],
                                    brilliant_moves={"schema": 1, "plies": [3]})
        self.assertEqual(col.notes_created, 0)
        self.assertEqual(col.models.added_fields, [])
        self.assertEqual(col.models.saves, [])

    def evaluation_data(self, start_fen=""):
        return {"schema": 1, "start_fen": start_fen, "moves": ["e4", "e5"],
                "scores": [None, {"cp": 0}, {"cp": -12}],
                "engine": {"name": "Test engine", "depth": 16}}

    def test_create_note_validates_and_serializes_position_evaluation(self):
        data = self.evaluation_data()
        for value in (data, json.dumps(data)):
            with self.subTest(value_type=type(value).__name__):
                col = FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])
                note = self.module.create_note(col, "Example", "white", ["e4", "e5"],
                                               position_evaluation=value)
                self.assertEqual(json.loads(note["Position Evaluation"]), data)
                self.assertEqual(note["Brilliant Moves"], "")

    def test_mismatched_position_evaluation_is_rejected_before_any_write(self):
        for data in (dict(self.evaluation_data(), moves=["d4", "d5"]),
                     dict(self.evaluation_data(), start_fen="another position")):
            with self.subTest(data=data):
                col = FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])
                with self.assertRaises(ValueError):
                    self.module.create_note(col, "Example", "white", ["e4", "e5"],
                                            position_evaluation=data)
                self.assertEqual(col.notes_created, 0)
                self.assertEqual(col.models.added_fields, [])

    def test_evaluation_uses_exact_fen_that_will_be_saved(self):
        canonical = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        raw = "  " + canonical.replace(" w ", "   w   ") + "  "
        col = FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])
        note = self.module.create_note(col, "Example", "white", ["e4", "e5"], start_fen=raw,
                                       position_evaluation=self.evaluation_data(canonical))
        self.assertEqual(note["StartFEN"], canonical)
        self.assertEqual(json.loads(note["Position Evaluation"])["start_fen"], canonical)
        with self.assertRaises(ValueError):
            self.module.create_note(col, "Example", "white", ["e4", "e5"], start_fen=raw,
                                    position_evaluation=self.evaluation_data(raw))

    def config_double(self, values):
        fake = types.ModuleType(self.module.__package__ + ".config")
        fake.get_config = lambda: values
        fake.narration_rate = lambda value: 1.5
        fake.board_colors = lambda values: ("#ffffff", "#000000")
        fake.sound_data_uris = lambda: ("move", "capture", "check", "castle", "mate")
        fake.mistake_sound_uri = lambda: "mistake"
        fake.brilliant_sound_uri = lambda: "data:audio/wav;base64,brilliant"
        fake.texture_pattern = lambda texture: ""
        fake.DEFAULTS = {"piece_set": "wooden", "mistakes_limit": 3,
                         "toggle_one_key": "n", "toggle_all_key": ","}
        sys.modules[fake.__name__] = fake
        setattr(sys.modules[self.module.__package__], "config", fake)
        return fake

    def test_prelude_transports_independent_brilliant_and_evaluation_preferences(self):
        self.config_double({"sound_enabled": True, "brilliant_effects_enabled": False,
                            "brilliant_particles_enabled": True, "brilliant_sound_enabled": False,
                            "evaluation_enabled": False})
        markup = self.module._config_prelude()
        self.assertIn("COT_SOUND_ENABLED=true;", markup)
        self.assertIn("COT_BRILLIANT_EFFECTS_ENABLED=false;", markup)
        self.assertIn("COT_BRILLIANT_PARTICLES_ENABLED=true;", markup)
        self.assertIn("COT_BRILLIANT_SOUND_ENABLED=false;", markup)
        self.assertIn('COT_BRILLIANT_SRC="";', markup)
        self.assertIn("COT_EVALUATION_ENABLED=false;", markup)

    def test_prelude_mutes_brilliant_audio_with_global_sound_switch(self):
        fake = self.config_double({"sound_enabled": False})
        fake.brilliant_sound_uri = lambda: self.fail("Muted audio must not be loaded")
        markup = self.module._config_prelude()
        self.assertIn("COT_SOUND_ENABLED=false;", markup)
        self.assertIn("COT_BRILLIANT_SOUND_ENABLED=true;", markup)
        self.assertIn('COT_BRILLIANT_SRC="";', markup)

    def test_front_embeds_helpers_before_the_card_runtime(self):
        packs = types.ModuleType(self.module.__package__ + ".language_packs")
        packs.selected = lambda: {"id": "sample", "language": "en", "lines": []}
        packs.selected_voice = lambda: {"id": "system", "language": "en-US", "clips": {}}
        sys.modules[packs.__name__] = packs
        setattr(sys.modules[self.module.__package__], "language_packs", packs)
        self.module._web = lambda name: "asset:" + name
        self.module._config_prelude = lambda: "preferences"
        markup = self.module._original_build_front()
        self.assertLess(markup.index("asset:brilliant.js"), markup.index("asset:card_front.html"))
        self.assertLess(markup.index("asset:evaluation.js"), markup.index("asset:card_front.html"))


if __name__ == "__main__":
    unittest.main()
