"""Native integration probe, loaded only by scripts/verify_brilliancy.py."""
import html
import json
import os
from pathlib import Path
import traceback

from aqt import gui_hooks,mw
from aqt.qt import QTimer

base=Path(os.environ['CFA_BRILLIANCY_BASE'])
output=Path(os.environ['CFA_BRILLIANCY_OUTPUT'])
report={}
case=None
test_cases=[]

def done():
    (output/'native-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    QTimer.singleShot(100,mw.unloadProfileAndExit)

def checked(fn):
    def wrapped(*args):
        try:fn(*args)
        except Exception:
            report['error']=traceback.format_exc()
            done()
    return wrapped

def js(source,callback):
    mw.reviewer.web.evalWithCallback(source,checked(callback))

def begin():
    global case,test_cases
    assert Path(mw.pm.base).resolve()==base.resolve()
    assert mw.col.card_count()==0
    mw.resize(900,1000)
    from chess_for_anki import config,note_type,progression
    from chess_for_anki.faq_dialog import FaqDialog
    for window in mw.findChildren(FaqDialog):
        if window.isVisible():window.accept()
    settings=config.get_config()
    settings.update(voice_pack='system',sound_enabled=True,confetti_enabled=False)
    config.save_config(settings)
    mw.col.set_config(progression.TUTORIAL_KEY,True)
    mw.col.set_config(progression.DEMO_KEY,{'enabled':False,'seen':[]})
    cards=json.loads((base/'pack.json').read_text(encoding='utf8'))['exercises']
    test_cases=cards
    for card in cards:
        commentary=card.get('commentary',{'start_fen':card['start_fen'],'moves':card['moves_san'],'language':'en','notes':[{'san':san,'text':card['solution']} for san in card['moves_san']]})
        notes='<p>'+html.escape(card['solution'])+'</p><div class="cfa-commentary-data" hidden>'+html.escape(json.dumps(commentary))+'</div>'
        note=note_type.create_note(mw.col,card['title'],card['side'],card['moves_san'],start_fen=card['start_fen'],book_notes=notes,brilliant_moves=card['brilliant_moves'],position_evaluation=card['position_evaluation'])
        note.guid='cfa-brilliant-'+card['id']
        mw.col.add_note(note,mw.col.decks.id('Chess::Brilliancy Training'))
        card['cid']=note.card_ids()[0]
    report['imported']=len(cards)
    for card in cards:
        if card['id']!='brilliancy-001':mw.col.sched.suspend_cards([card['cid']])
    case=cards[0]
    mw.col.decks.select(mw.col.get_card(case['cid']).did)
    mw.moveToState('overview')
    QTimer.singleShot(300,checked(lambda:mw.moveToState('review')))
    QTimer.singleShot(1400,checked(check_initial))

def check_initial():
    replay="""(()=>{var cases=CASES,n=0;for(var c of cases){var g=new Chess(c.start_fen);for(var i=0;i<c.moves_san.length;i++){if(!g.move(c.moves_san[i]))return {error:'Illegal replay',id:c.id,ply:i+1};if(g.fen().split(' ').slice(0,3).join(' ')!==c.fens_after_each_ply[i].split(' ').slice(0,3).join(' '))return {error:'Wrong position',id:c.id,ply:i+1};n++;}}return {plies:n,cards:cases.length,squares:document.querySelectorAll('td.sq').length,highlights:document.querySelectorAll('.brilliant-square').length,evaluation:document.getElementById('studio-evaluation').hidden,score:document.querySelector('.evaluation-value').textContent};})()""".replace('CASES',json.dumps(json.loads((base/'pack.json').read_text(encoding='utf8'))['exercises']))
    def next(result):
        assert result and not result.get('error'),result
        assert result['squares']==64 and result['highlights']==0 and result['evaluation'] is False,result
        report['initial']=result
        js("""(()=>{localStorage.setItem('chess-studio-voice','off');var b=document.getElementById('studio-voice');if(b.textContent==='Voice on')b.click();document.getElementById('studio-show-demo').click();document.getElementById('studio-demo-next').click();return {score:document.querySelector('.evaluation-value').textContent,highlights:document.querySelectorAll('.brilliant-square').length};})()""",check_demo)
    js(replay,next)

def check_demo(result):
    assert result['highlights']==0,result
    report['demo']=result
    js("""(()=>{document.getElementById('studio-demo-prev').click();var value=document.querySelector('.evaluation-value').textContent;document.getElementById('studio-demo-skip').click();return {score:value,history:document.querySelector('#studio-depth-count').textContent};})()""",check_rewind)

def check_rewind(result):
    assert result['score']==report['initial']['score'],result
    report['rewind']=result
    wrong_move="""(()=>{function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('b3');tap('b4');return {highlights:document.querySelectorAll('.brilliant-square').length,score:document.querySelector('.evaluation-value').textContent};})()"""
    js(wrong_move,check_wrong)

def check_wrong(result):
    assert result['highlights']==0 and result['score']==report['initial']['score'],result
    report['wrong_move']=result
    js("""(()=>{window.__brilliantAudioPlayed=0;var play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(this.src===COT_BRILLIANT_SRC)window.__brilliantAudioPlayed++;return play.call(this);};function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('b3');tap('b8');return {highlights:document.querySelectorAll('.brilliant-square').length,badge:document.querySelector('.brilliant-badge')?.textContent,score:document.querySelector('.evaluation-value').textContent,sound:window.__brilliantAudioPlayed,particles:document.querySelectorAll('#studio-brilliant i').length};})()""",check_correct)

def check_correct(result):
    assert result['highlights']==1 and result['badge']=='!!' and result['sound']==1 and result['particles']>0,result
    assert result['score']==report['demo']['score'],result
    report['correct_move']=result
    QTimer.singleShot(100,lambda:mw.reviewer.web.grab().save(str(output/'Brilliancy - correct move.png')))
    QTimer.singleShot(1700,checked(check_reply))

def check_reply():
    js("""(()=>{return {score:document.querySelector('.evaluation-value').textContent,sound:window.__brilliantAudioPlayed,played:document.querySelector('[data-sq="b8"] .piece')!==null};})()""",finish_reply)

def finish_reply(result):
    assert result['sound']==1,result
    report['automatic_reply']=result
    js("""(()=>{COT_BRILLIANT_EFFECTS_ENABLED=false;COT_BRILLIANT_PARTICLES_ENABLED=false;COT_BRILLIANT_SOUND_ENABLED=false;COT_EVALUATION_ENABLED=false;document.getElementById('studio-restart').click();function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('b3');tap('b8');return {highlights:document.querySelectorAll('.brilliant-square').length,particles:document.querySelectorAll('#studio-brilliant i').length,sound:window.__brilliantAudioPlayed,evaluationHidden:document.getElementById('studio-evaluation').hidden};})()""",finish_disabled)

def finish_disabled(result):
    assert result['highlights']==0 and result['particles']==0 and result['sound']==1 and result['evaluationHidden'],result
    report['disabled_preferences']=result
    # Re-render the same saved note with only its final move marked. This
    # catches a redraw in conclude() accidentally dropping the reward.
    from chess_for_anki import brilliant
    note=mw.reviewer.card.note()
    note['Brilliant Moves']=brilliant.dumps({'schema':1,'plies':[3]})
    mw.col.update_note(note)
    mw.reviewer.card=mw.col.get_card(case['cid'])
    mw.reviewer._showQuestion()
    QTimer.singleShot(300,checked(play_final_case))

def play_final_case():
    js("""(()=>{localStorage.setItem('chess-studio-voice','off');var b=document.getElementById('studio-voice');if(b.textContent==='Voice on')b.click();function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('b3');tap('b8');return true;})()""",lambda result:QTimer.singleShot(400,checked(play_mate)))

def play_mate():
    js("""(()=>{function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('d1');tap('d8');return {highlights:document.querySelectorAll('.brilliant-square').length,badge:document.querySelector('.brilliant-badge')?.textContent,score:document.querySelector('.evaluation-value').textContent,complete:window._cotResult?.success,brilliantVisible:!document.getElementById('studio-brilliant').hidden};})()""",finish_mate)

def finish_mate(result):
    assert result['highlights']==1 and result['badge']=='!!' and result['score']=='1-0' and result['complete'] and result['brilliantVisible'],result
    report['final_ply_reward']=result
    from chess_for_anki import brilliant
    note=mw.reviewer.card.note()
    note['Brilliant Moves']=brilliant.dumps(case['brilliant_moves'])
    mw.col.update_note(note)
    QTimer.singleShot(100,lambda:mw.reviewer.web.grab().save(str(output/'Brilliancy - final move.png')))
    QTimer.singleShot(220,checked(export_pack))

def export_pack():
    from anki.exporting import AnkiPackageExporter
    exporter=AnkiPackageExporter(mw.col)
    exporter.did=mw.col.decks.id_for_name('Chess::Brilliancy Training')
    exporter.includeSched=False
    exporter.includeMedia=False
    exporter.exportInto(str(output/'Chess for Anki - Brilliancy Training - private.apkg'))
    report['exported_private_apkg']=True
    black=next(card for card in test_cases if card['side']=='black')
    mw.reviewer.card=mw.col.get_card(black['cid'])
    mw.reviewer._showQuestion()
    QTimer.singleShot(300,checked(check_black))

def check_black():
    js("""(()=>{return {flipped:document.getElementById('studio-evaluation').classList.contains('board-flipped'),firstSquare:document.querySelector('td.sq').dataset.sq,score:document.querySelector('.evaluation-value').textContent,highlights:document.querySelectorAll('.brilliant-square').length};})()""",finish_black)

def finish_black(result):
    assert result['flipped'] and result['firstSquare']=='h1' and result['score'].startswith('-') and result['highlights']==0,result
    report['black_orientation']=result
    from chess_for_anki import note_type
    moves=['e4','e5','Nf3','Nf6','Ng1','Ng8','Nf3','Nf6']
    # Deliberately distinct test scores make repeated-position overwrites
    # observable. These synthetic values never leave the disposable QA deck.
    data={'schema':1,'start_fen':'','moves':moves,'scores':[{'cp':n*10} for n in range(9)],'engine':{'name':'Synthetic regression fixture'}}
    note=note_type.create_note(mw.col,'Repeated position QA','white',moves,position_evaluation=data)
    mw.col.add_note(note,mw.col.decks.id('QA fixtures'))
    mw.reviewer.card=note.cards()[0]
    mw.reviewer._showQuestion()
    QTimer.singleShot(300,checked(check_repetition))

def check_repetition():
    js("""(()=>{var show=document.getElementById('studio-show-demo');if(!show.hidden)show.click();var next=document.getElementById('studio-demo-next'),prev=document.getElementById('studio-demo-prev'),values=[];while(!next.disabled){next.click();values.push(document.querySelector('.evaluation-value').textContent);}while(!prev.disabled)prev.click();for(var i=0;i<4;i++)next.click();return {scores:values,rewoundToFour:document.querySelector('.evaluation-value').textContent};})()""",finish_repetition)

def finish_repetition(result):
    assert result['scores']==['+0.1','+0.2','+0.3','+0.4','+0.5','+0.6','+0.7','+0.8'] and result['rewoundToFour']=='+0.4',result
    report['repeated_position_regression']=result
    mw.reviewer._showAnswer()
    QTimer.singleShot(300,checked(check_unknown_branch))

def check_unknown_branch():
    js("""(()=>{var prev=document.getElementById('btn-prev');while(!prev.disabled)prev.click();function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));}tap('d2');tap('d4');return {score:document.querySelector('.evaluation-value').textContent,unknown:document.getElementById('studio-evaluation').classList.contains('not-analyzed')};})()""",finish_unknown)

def finish_unknown(result):
    assert result['score']=='?' and result['unknown'],result
    report['unknown_branch']=result
    from chess_for_anki import note_type
    col=mw.col
    model=col.models.new('Chess for Anki - old imported suffix')
    for name in note_type.LEGACY_FIELDS:col.models.add_field(model,col.models.new_field(name))
    template=col.models.new_template('Original card')
    template['qfmt']='<div id="studio-fields">{{Title}}</div>'
    template['afmt']='{{FrontSide}}'
    col.models.add_template(model,template)
    col.models.add(model)
    note=col.new_note(model)
    note['Title']='Schema migration QA'
    note['PlayerColor']='white'
    note['MovesPGN']='e4 e5'
    col.add_note(note,col.decks.id('QA fixtures'))
    card=note.cards()[0]
    card.type=2;card.queue=2;card.due=321;card.ivl=45;card.reps=7
    col.update_card(card)
    columns='id,nid,did,ord,type,queue,due,ivl,factor,reps,lapses,left,odue,odid,flags'
    before=col.db.first('select '+columns+' from cards where id=?',card.id)
    before_review=col.db.scalar('select count(*) from revlog')
    note_type.ensure_notetype(col)
    after=col.db.first('select '+columns+' from cards where id=?',card.id)
    assert before==after
    assert col.db.scalar('select count(*) from revlog')==before_review
    migrated=col.get_note(note.id)
    assert migrated.note_type()['id']==model['id'] and migrated['Title']=='Schema migration QA'
    assert migrated['Brilliant Moves']=='' and migrated['Position Evaluation']==''
    report['native_schema_migration']={'suffixed_model_id_preserved':True,'note_id_preserved':True,'card_scheduling_preserved':True,'review_history_preserved':True,'optional_fields_added':2}
    done()

gui_hooks.profile_did_open.append(lambda:QTimer.singleShot(900,checked(begin)))
