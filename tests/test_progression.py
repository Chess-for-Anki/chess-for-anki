import importlib.util,sys,types,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
aqt=sys.modules.setdefault('aqt',types.ModuleType('aqt'));aqt.gui_hooks=types.SimpleNamespace();aqt.mw=None
utils=sys.modules.setdefault('aqt.utils',types.ModuleType('aqt.utils'));utils.tooltip=lambda x:None
spec=importlib.util.spec_from_file_location('progression_test',root/'chess_for_anki/progression.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class ProgressTests(unittest.TestCase):
 def setUp(self):
  self.data={};col=types.SimpleNamespace(get_config=lambda key,default:self.data.get(key,default),set_config=lambda key,value:self.data.update({key:value}));p.mw=types.SimpleNamespace(col=col);p.pending.clear()
 def card(self,ident,moves,start=''):
  return types.SimpleNamespace(id=ident,note=lambda:{'MovesPGN':moves,'StartFEN':start})
 def complete(self,card,level='8',ease=3):p.pending[card.id]=level;p.answer(None,card,ease)
 def test_shared_prefix_does_not_unlock(self):
  self.complete(self.card(1,'e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6 O-O'))
  self.complete(self.card(2,'e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6 c3'))
  self.assertEqual(len(p.state()['wins']),1)
 def test_distinct_clean_lines_promote_only_after_three(self):
  for i,line in enumerate(['e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6','d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7','e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6']):self.complete(self.card(i,line))
  self.assertEqual(p.state(),{'level':'16','wins':[]})
 def test_short_fen_and_again_do_not_promote(self):
  self.complete(self.card(1,'e4 e5'))
  self.complete(self.card(2,'e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6','position'))
  self.complete(self.card(3,'e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6'),ease=1)
  self.assertEqual(p.state()['wins'],[])
 def test_migrates_duplicate_old_full_lines(self):
  self.data[p.KEY]={'level':'8','wins':['e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6 O-O','e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6 c3']}
  self.assertEqual(len(p.state()['wins']),1)
 def test_footer_handles_chess_and_other_cards_without_shadowing_predicate(self):
  previous=p.is_chess
  bottom=[];review=[]
  p.mw.reviewer=types.SimpleNamespace(bottom=types.SimpleNamespace(web=types.SimpleNamespace(eval=bottom.append)),web=types.SimpleNamespace(eval=review.append))
  p.is_chess=lambda card:card=='chess'
  try:
   p.footer('chess');p.footer('other')
  finally:p.is_chess=previous
  self.assertIn('Again',review[0]);self.assertIn('data-ease',bottom[0])
  self.assertIn('remove()',review[1]);self.assertIn('remove()',bottom[1])
if __name__=='__main__':unittest.main()
