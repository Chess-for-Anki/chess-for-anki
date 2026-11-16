import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluation_test", ROOT / "chess_for_anki/evaluation.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = {"schema": 1, "start_fen": "", "moves": ["e4", "e5"],
                     "scores": [{"cp": 0}, None, {"mate": -3}],
                     "engine": {"name": "Stockfish 19", "nodes": 100000, "depth": 18}}

    def test_round_trip_and_exact_line_identity(self):
        raw = evaluation.dumps(self.data, start_fen="", moves=["e4", "e5"])
        self.assertEqual(evaluation.loads(raw.encode("utf-8")), self.data)
        self.assertEqual(evaluation.loads(raw)["scores"][0], {"cp": 0})
        for context in ({"moves": ["e4", "c5"]}, {"start_fen": "other"}):
            with self.assertRaises(ValueError):
                evaluation.loads(raw, **context)

    def test_score_indexing_requires_initial_position(self):
        self.data["scores"].pop(0)
        with self.assertRaises(ValueError):
            evaluation.validate(self.data)

    def test_unknown_is_null_and_ambiguous_mate_zero_rejected(self):
        for score in ({"cp": True}, {"cp": 1.5}, {"cp": float("nan")},
                      {"mate": 0}, {"cp": 20, "mate": 2}, {"mate": -1001}):
            bad = copy.deepcopy(self.data)
            bad["scores"][0] = score
            with self.subTest(score=score), self.assertRaises(ValueError):
                evaluation.validate(bad)

    def test_inert_json_and_strict_engine_fields(self):
        for raw in ('__import__("os").system("anything")',
                    '{"schema":1,"schema":2}', "[" * 1200 + "]" * 1200):
            with self.assertRaises(ValueError):
                evaluation.loads(raw)
        self.data["engine"]["command"] = "execute"
        with self.assertRaises(ValueError):
            evaluation.validate(self.data)

    def test_bounds_and_safe_html_embedding(self):
        with self.assertRaises(ValueError):
            evaluation.loads(" " * (evaluation.MAX_BYTES + 1))
        self.data["moves"] = ["e4"] * 601
        self.data["scores"] = [None] * 602
        with self.assertRaises(ValueError):
            evaluation.validate(self.data)
        self.setUp()
        self.data["engine"]["name"] = "</script><script>never run</script>"
        raw = evaluation.dumps(self.data)
        self.assertNotIn("<", raw)
        self.assertEqual(json.loads(raw)["engine"]["name"], self.data["engine"]["name"])

    def test_custom_fen_and_canonical_copy(self):
        self.data["start_fen"] = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"
        result = evaluation.validate(self.data, start_fen=self.data["start_fen"])
        result["scores"][0]["cp"] = 9
        self.assertEqual(self.data["scores"][0]["cp"], 0)
        for fen in ("8/8/8/8/8/8/8/8 w - - 0 1", self.data["start_fen"] + "\n"):
            self.data["start_fen"] = fen
            with self.assertRaises(ValueError):
                evaluation.validate(self.data)


if __name__ == "__main__":
    unittest.main()
