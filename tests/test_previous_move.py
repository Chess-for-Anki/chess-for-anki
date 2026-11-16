"""Previous-move metadata is bounded, inert, and independent of the solution."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

from test_brilliant_models import FakeCollection, load_note_type, model


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "_previous_move_tests"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "chess_for_anki")]
sys.modules[PACKAGE] = package
spec = importlib.util.spec_from_file_location(
    PACKAGE + ".previous_move", ROOT / "chess_for_anki" / "previous_move.py")
previous = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = previous
spec.loader.exec_module(previous)

INITIAL = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
BEFORE = "5k2/5ppp/8/8/8/8/5PPP/4R1K1 b - - 0 1"
TARGET = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 1 2"
CASTLE_BEFORE = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 5 7"
CASTLE_AFTER = "r3k2r/8/8/8/8/8/8/R4RK1 b kq - 6 7"
EP_BEFORE = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 5"
EP_AFTER = "4k3/8/3P4/8/8/8/8/4K3 b - - 0 5"
PROMOTION_BEFORE = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
PROMOTION_AFTER = "Q3k3/8/8/8/8/8/8/4K3 b - - 0 1"


def context(before=BEFORE, uci="f8g8", source="constructed"):
    return {"schema": 1, "before_fen": before, "uci": uci, "source": source}


class PreviousMoveTests(unittest.TestCase):
    def test_canonical_round_trip_is_an_independent_copy(self):
        data = context()
        data["before_fen"] = "  " + BEFORE.replace(" b ", "   b   ") + "  "
        snapshot = deepcopy(data)
        canonical = previous.validate(data, TARGET)
        self.assertEqual(canonical, context())
        self.assertEqual(data, snapshot)
        self.assertIsNot(canonical, data)
        self.assertEqual(previous.loads(previous.dumps(data, TARGET), TARGET), context())
        for source in previous.SOURCES:
            with self.subTest(source=source):
                self.assertEqual(previous.validate(context(source=source))["source"], source)
        data.pop("source")
        self.assertEqual(previous.validate(data)["source"], "user")

    def test_rejects_unknown_fields_missing_fields_and_wrong_types(self):
        invalid = [None, [], True, "{}", dict(context(), extra="ignored"),
                   dict(context(), schema=True), dict(context(), schema=1.0),
                   dict(context(), schema=2), dict(context(), before_fen=None),
                   dict(context(), before_fen=[]), dict(context(), uci=None),
                   dict(context(), uci=1234)]
        invalid.extend(dict(context(), source=value)
                       for value in (None, False, 0, "", "engine", [], {}))
        for key in ("schema", "before_fen", "uci"):
            data = context()
            del data[key]
            invalid.append(data)
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                previous.validate(data)

    def test_invalid_fen_and_uci_never_become_executable_markup(self):
        for fen in ("8/8/8/8/8/8/8/8 w - - 0 1", BEFORE.replace(" b ", " x "),
                    BEFORE.replace("5k2", "5k3"), BEFORE.replace(" b - ", " b qK "),
                    BEFORE.replace(" - - ", " - e4 "), BEFORE + "\n",
                    "</script><script>alert(1)</script>", "x" * 129):
            with self.subTest(fen=fen), self.assertRaises(ValueError):
                previous.validate(context(before=fen))
        for uci in ("f8f8", "F8G8", "f8g9", "f8g8k", "f8-g8", "f8g8\n",
                    "f8g8<script>alert(1)</script>"):
            with self.subTest(uci=uci), self.assertRaises(ValueError):
                previous.validate(context(uci=uci))

    def test_json_is_strict_bounded_and_inert(self):
        raw = previous.dumps(context())
        duplicate = raw.replace('"schema":1', '"schema":0,"schema":1')
        escaped_duplicate = raw.replace('"schema":1', '"sch\\u0065ma":1,"schema":1')
        for value in (None, b"{}", "", "null", "[]", "{}", "__import__('os')",
                      "</script><script>alert(1)</script>", duplicate, escaped_duplicate,
                      "[" * 1200 + "]" * 1200,
                      " " * (previous.MAX_BYTES + 1), "é" * (previous.MAX_BYTES // 2 + 1)):
            with self.subTest(value=repr(value)[:90]), self.assertRaises(ValueError):
                previous.loads(value)
        self.assertEqual(previous.loads(raw + " " * (previous.MAX_BYTES - len(raw))), context())

    def test_rejects_wrong_side_origin_illegal_move_and_wrong_destination(self):
        for data, target in ((context(), TARGET.replace(" w ", " b ")),
                             (context(uci="e8g8"), TARGET),
                             (context(uci="f8g6"), TARGET),
                             (context(uci="f8e8"), TARGET),
                             (context(), "")):
            with self.subTest(data=data, target=target), self.assertRaises(ValueError):
                previous.validate(data, target)

    def test_rejects_self_check_and_a_predecessor_with_the_other_king_in_check(self):
        invalid = [
            ("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1", "e2a2",
             "4r1k1/8/8/8/8/8/R7/4K3 b - - 1 1"),
            ("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1", "e2a2",
             "4k3/8/8/8/8/8/R7/4K3 b - - 1 1"),
        ]
        for before, uci, after in invalid:
            with self.subTest(uci=uci, before=before), self.assertRaises(ValueError):
                previous.validate(context(before, uci), after)

    def test_castling_en_passant_and_promotion_replay(self):
        for before, uci, after in ((CASTLE_BEFORE, "e1g1", CASTLE_AFTER),
                                   (EP_BEFORE, "e5d6", EP_AFTER),
                                   (PROMOTION_BEFORE, "a7a8q", PROMOTION_AFTER),
                                   (PROMOTION_BEFORE, "a7a8n", PROMOTION_AFTER.replace("Q3", "N3"))):
            with self.subTest(uci=uci):
                self.assertEqual(previous.validate(context(before, uci), after)["uci"], uci)

    def test_rejects_missing_right_rook_ep_pawn_and_invalid_promotion(self):
        invalid = [
            (CASTLE_BEFORE.replace(" KQkq ", " Qkq "), "e1g1", CASTLE_AFTER),
            (CASTLE_BEFORE.replace("R3K2R", "R3K3"), "e1g1", CASTLE_AFTER),
            (EP_BEFORE.replace(" d6 ", " - "), "e5d6", EP_AFTER),
            (EP_BEFORE.replace("3pP3", "4P3"), "e5d6", EP_AFTER),
            (PROMOTION_BEFORE, "a7a8", PROMOTION_AFTER),
            (INITIAL, "e2e4q", AFTER_E4),
            (BEFORE, "f8g8q", TARGET),
        ]
        for before, uci, after in invalid:
            with self.subTest(uci=uci, before=before), self.assertRaises(ValueError):
                previous.validate(context(before, uci), after)

    def test_position_identity_preserves_castling_and_legal_ep_but_ignores_clocks(self):
        self.assertEqual(previous.validate(context(), TARGET.replace("1 2", "0 1")), context())
        with self.assertRaises(ValueError):
            previous.validate(context(CASTLE_BEFORE, "e1g1"), CASTLE_AFTER.replace(" kq ", " - "))
        # A double push's EP square is relevant only if the opponent can capture legally.
        previous.validate(context(INITIAL, "e2e4"), AFTER_E4.replace(" e3 ", " - "))
        before = "4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1"
        after = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2"
        previous.validate(context(before, "d7d5"), after)
        with self.assertRaises(ValueError):
            previous.validate(context(before, "d7d5"), after.replace(" d6 ", " - "))

    def test_setup_pgn_uses_the_first_mainline_and_returns_complete_fen(self):
        fen, data = previous.setup_from_pgn(
            '1. e4 {comment} (1. d4 d5) e5 2. Nf3 Nc6 * 1. d4 d5 *')
        self.assertEqual(fen, "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
        self.assertEqual(data["uci"], "b8c6")
        self.assertEqual(data["before_fen"], "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
        self.assertEqual(data["source"], "user")
        previous.validate(data, fen)

    def test_setup_pgn_preserves_castling_ep_clocks_and_promotion(self):
        for before, san, uci, after in ((CASTLE_BEFORE, "O-O", "e1g1", CASTLE_AFTER),
                                        (EP_BEFORE, "exd6", "e5d6", EP_AFTER),
                                        (PROMOTION_BEFORE, "a8=Q+", "a7a8q", PROMOTION_AFTER),
                                        (INITIAL, "e4", "e2e4", AFTER_E4)):
            with self.subTest(san=san):
                fen, data = previous.setup_from_pgn('[SetUp "1"]\n[FEN "' + before + '"]\n' + san + ' *')
                self.assertEqual(fen, after)
                self.assertEqual(data, context(before, uci, "user"))
        self.assertEqual(previous.setup_from_pgn('[FEN "' + TARGET + '"]\n*'), (TARGET, None))

    def test_setup_pgn_rejects_empty_illegal_and_incomplete_start_fen(self):
        for text in ("", "*", "1. e5 *", '[FEN "8/8/8/8/8/8/8/8 w - - 0 1"]\n*',
                     '[FEN "' + BEFORE.rsplit(" ", 4)[0] + '"]\n*'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                previous.setup_from_pgn(text)


class PreviousMoveNoteTests(unittest.TestCase):
    def setUp(self):
        self.module = load_note_type()

    def collection(self):
        return FakeCollection([model(self.module, 101, self.module.NOTETYPE_NAME)])

    def test_custom_note_requires_context_before_any_collection_write(self):
        col = self.collection()
        with self.assertRaises(ValueError):
            self.module.create_note(col, "Mate", "white", ["Re8#"], start_fen=TARGET)
        self.assertEqual(col.notes_created, 0)
        self.assertEqual(col.models.added_fields, [])
        self.assertEqual(col.models.saves, [])

    def test_custom_note_serializes_context_without_adding_a_solution_ply(self):
        for value in (context(), previous.dumps(context())):
            with self.subTest(value_type=type(value).__name__):
                note = self.module.create_note(self.collection(), "Mate", "white", ["Re8#"],
                                               start_fen=TARGET, previous_move=value,
                                               brilliant_moves={"schema": 1, "plies": [1]})
                self.assertEqual(note["StartFEN"], TARGET)
                self.assertEqual(note["MovesPGN"], "Re8#")
                self.assertEqual(json.loads(note["Previous Move"]), context())
                self.assertEqual(json.loads(note["Brilliant Moves"])["plies"], [1])

    def test_legacy_setup_flag_allows_blank_context_and_standard_start_is_unchanged(self):
        for fen, legacy in ((TARGET, True), ("", False), (INITIAL, False)):
            with self.subTest(fen=fen):
                note = self.module.create_note(self.collection(), "Example", "white", ["e4"],
                                               start_fen=fen, legacy_setup=legacy)
                self.assertEqual(note["Previous Move"], "")
        with self.assertRaises(ValueError):
            self.module.create_note(self.collection(), "Mate", "white", ["Re8#"],
                                    start_fen=TARGET, legacy_setup=True,
                                    previous_move=context(uci="f8g6"))

    def test_migration_preserves_existing_context_note_ids_and_review_history(self):
        item = model(self.module, 101, self.module.NOTETYPE_NAME)
        notes = [{"id": 501, "mid": 101, "guid": "stable-guid", "fields": {
            "Title": "Existing", "StartFEN": TARGET, "MovesPGN": "Re8#"}}]
        cards = [{"id": 601, "nid": 501, "due": 100, "ivl": 30, "reps": 12,
                  "lapses": 1, "queue": 2}]
        col = FakeCollection([item], notes, cards)
        col.review_history = [{"id": 701, "cid": 601, "ease": 3, "ivl": 30, "time": 8000}]
        before_notes, before_cards, before_history = map(deepcopy, (notes, cards, col.review_history))
        self.module.ensure_notetype(col)
        expected = deepcopy(before_notes)
        expected[0]["fields"].update({"Brilliant Moves": "", "Position Evaluation": "", "Previous Move": ""})
        self.assertEqual(col.notes, expected)
        self.assertEqual(col.cards, before_cards)
        self.assertEqual(col.review_history, before_history)
        self.assertEqual(item["id"], 101)
        self.assertEqual(col.notes_created, 0)
        notes[0]["fields"]["Previous Move"] = previous.dumps(context())
        existing = deepcopy(notes)
        self.module.ensure_notetype(col)
        self.assertEqual(col.notes, existing)


if __name__ == "__main__":
    unittest.main()
