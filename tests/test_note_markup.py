from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'chess_for_anki'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class MarkupTests(unittest.TestCase):
 def test_literal_title_does_not_create_markup(self):
  m=load('note_type');m.ensure_notetype=lambda col:{};m.moves_fen_text=lambda *args:''
  class Col:
   def new_note(self,model):return {}
  note=m.create_note(Col(),'<img src=x onerror=alert(1)>','white',['e4'],book_notes='<p>Trusted formatted notes</p>')
  self.assertNotIn('<img',note['Title']);self.assertIn('&lt;img',note['Title']);self.assertEqual(note['Book Notes'],'<p>Trusted formatted notes</p>')
 def test_imported_suffix_is_recognized_without_trusting_name(self):
  m=load('note_type');model={'name':'Chess for Anki+','flds':[{'name':f} for f in m.FIELDS],'tmpls':[{'qfmt':'<div id="studio-fields"></div>'}]}
  self.assertTrue(m.is_chess_notetype(model))
  model['tmpls'][0]['qfmt']='<div>unrelated</div>'
  self.assertFalse(m.is_chess_notetype(model))
 def test_board_color_rejects_markup(self):
  m=load('config');light,dark=m.board_colors({'board_light':'</style><script>alert(1)</script>'})
  self.assertRegex(light,r'^#[0-9a-fA-F]{6}$');self.assertRegex(dark,r'^#[0-9a-fA-F]{6}$')
  self.assertEqual(m.board_colors({'board_light':'#aAbBcC'})[0],'#aAbBcC')
if __name__=='__main__':unittest.main()
