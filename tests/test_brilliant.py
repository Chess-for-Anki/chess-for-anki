"""Validate untrusted brilliant-move metadata without loading Anki."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "brilliant_metadata_test", ROOT / "chess_for_anki" / "brilliant.py")
brilliant = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brilliant)


class BrilliantMetadataTests(unittest.TestCase):
    def test_blank_field_is_optional_and_serializes_as_blank(self):
        for value in ("", " \n\t", " " * brilliant.MAX_METADATA_BYTES):
            with self.subTest(value_length=len(value)):
                self.assertEqual(brilliant.loads(value, 0), {"schema": 1, "plies": []})
        self.assertEqual(brilliant.dumps({"schema": 1, "plies": []}), "")

    def test_valid_one_based_plies_are_sorted_without_mutating_input(self):
        data = {"schema": 1, "plies": [600, 1, 7]}
        canonical = brilliant.validate(data, 600)
        self.assertEqual(canonical, {"schema": 1, "plies": [1, 7, 600]})
        self.assertEqual(data["plies"], [600, 1, 7])
        self.assertEqual(brilliant.dumps(canonical), '{"schema":1,"plies":[1,7,600]}')
        self.assertEqual(brilliant.loads(brilliant.dumps(canonical), 600), canonical)

    def test_plies_must_be_integers_inside_the_saved_line(self):
        for plies in ([0], [-1], [601], [True], [False], [1.0], ["1"], [None], [{}]):
            with self.subTest(plies=plies):
                with self.assertRaises(ValueError):
                    brilliant.validate({"schema": 1, "plies": plies})
        with self.assertRaises(ValueError):
            brilliant.validate({"schema": 1, "plies": [3]}, 2)
        with self.assertRaises(ValueError):
            brilliant.validate({"schema": 1, "plies": [1]}, 0)

    def test_schema_shape_and_types_are_strict(self):
        invalid = (None, [], {}, {"schema": 1}, {"schema": 2, "plies": []},
                   {"schema": True, "plies": []}, {"schema": 1.0, "plies": []},
                   {"schema": 1, "plies": "1"}, {"schema": 1, "plies": ()},
                   {"schema": 1, "plies": [], "script": "ignored()"})
        for data in invalid:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    brilliant.validate(data)

    def test_duplicates_and_oversized_arrays_are_rejected(self):
        for plies in ([1, 1], list(range(1, 602))):
            with self.subTest(length=len(plies)):
                with self.assertRaises(ValueError):
                    brilliant.validate({"schema": 1, "plies": plies})

    def test_invalid_json_and_duplicate_keys_are_rejected(self):
        for value in (None, {}, "<script>alert(1)</script>", "not JSON",
                      '{"schema":1,"schema":1,"plies":[1]}',
                      '{"schema":1,"plies":[],"plies":[1]}'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    brilliant.loads(value)

    def test_metadata_limit_counts_utf8_bytes(self):
        for value in (" " * (brilliant.MAX_METADATA_BYTES + 1),
                      "\u00e1" * (brilliant.MAX_METADATA_BYTES // 2 + 1)):
            with self.subTest(length=len(value)):
                with self.assertRaises(ValueError):
                    brilliant.loads(value)

    def test_excessively_nested_json_is_a_validation_error(self):
        with self.assertRaises(ValueError):
            brilliant.loads("[" * 1500 + "0" + "]" * 1500)

    def test_move_count_is_a_non_negative_integer(self):
        for count in (-1, True, 1.5, "2"):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    brilliant.validate({"schema": 1, "plies": []}, count)

    def test_full_600_ply_metadata_fits_and_round_trips(self):
        data = {"schema": 1, "plies": list(range(1, 601))}
        encoded = brilliant.dumps(data, 600)
        self.assertLess(len(encoded.encode("utf8")), brilliant.MAX_METADATA_BYTES)
        self.assertEqual(brilliant.loads(encoded, 600), data)


if __name__ == "__main__":
    unittest.main()
