import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('pgn',Path(__file__).resolve().parents[1]/'chess_for_anki/pgn_parser.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class PGNTests(unittest.TestCase):
 def test_results_separate_games(self):
  self.assertEqual(p.expand_variations('1.e4 e5 *\n[Event "second"]\n1.d4 d5 1/2-1/2'),[['e4','e5'],['d4','d5']])
  self.assertEqual(p.parse_pgn_moves('1.e4 e5 * 1.d4 d5 *'),['e4','e5'])
 def test_nested_alternatives_and_comments(self):
  self.assertEqual(p.expand_variations('1.e4 {idea} e5 (1...c5 (1...e6) 2.Nf3) 2.Nf3 ;comment\nNc6 *'),[['e4','e6'],['e4','c5','Nf3'],['e4','e5','Nf3','Nc6']])
 def test_unbalanced_and_oversized_input(self):
  for text in ['1.e4 (e5','1.e4 )','1.e4 {unclosed','e4 ('*33+'e5'+')'*33,'e4 '*601,'x'*(p.MAX_BYTES+1)]:
   with self.subTest(text=text[:30]),self.assertRaises(ValueError):p.expand_variations(text)
 def test_many_variations(self):
  with self.assertRaises(ValueError):p.expand_variations('e4 '+' '.join('(X%d)'%i for i in range(p.MAX_LINES+1)))
 def test_one_megabyte_read_limit(self):
  import tempfile
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'test.pgn';path.write_bytes(b'e4 '*(p.MAX_BYTES//3+1))
   with self.assertRaises(ValueError):p.read_pgn_file(path)
if __name__=='__main__':unittest.main()
