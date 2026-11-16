"""QA-only real reviewer recording, launched by scripts/capture_video.py."""
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

from aqt import gui_hooks,mw
from aqt.qt import QTimer

base=Path(os.environ['CFA_VIDEO_BASE'])
output=Path(os.environ['CFA_VIDEO_OUTPUT'])
fps=int(os.environ['CFA_VIDEO_FPS'])
frames_dir=output/'frames';frames_dir.mkdir(exist_ok=True)
sample=json.loads((base/'sample.json').read_text(encoding='utf8'))
narration=json.loads((base/'narration.json').read_text(encoding='utf8'))
report={'capture_method':'Real Qt Anki reviewer in disposable non-syncing profile','fps_requested':fps,'frames':[],'scenes':[],'events':[],'checks':{}}
cards={}
started=None
timer=None

def seconds():return time.monotonic()-started if started is not None else 0
def done():
    if timer:timer.stop()
    report['duration']=seconds()
    report['frame_count']=len(report['frames'])
    report['source_sha256']={name:hashlib.sha256((base/'addons21/chess_for_anki/web'/name).read_bytes()).hexdigest() for name in ('card_front.html','card_style.css','previous_move.js','brilliant.js')}
    (output/'native-capture.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    QTimer.singleShot(150,mw.unloadProfileAndExit)
def checked(fn):
    def call(*args):
        try:fn(*args)
        except Exception:
            report['error']=traceback.format_exc()
            done()
    return call
def js(source,callback=None):
    mw.reviewer.web.evalWithCallback(source,checked(callback or (lambda value:None)))
def event(name,value=None):report['events'].append({'time':seconds(),'name':name,'value':value})
def later(delay,fn):QTimer.singleShot(round(delay*1000),checked(fn))
def capture():
    t=seconds();index=len(report['frames'])
    filename='frames/frame-'+str(index).zfill(5)+'.jpg'
    pixmap=mw.reviewer.web.grab()
    assert not pixmap.isNull()
    if not pixmap.save(str(output/filename),'JPG',88):raise RuntimeError('Frame save failed')
    report['frames'].append({'time':t,'file':filename})
    if index==0:report['frame_size']=[pixmap.width(),pixmap.height()]

SUPPRESS_VOICE="""(()=>{localStorage.setItem('chess-studio-voice','off');var v=document.getElementById('studio-voice');if(v && v.textContent==='Voice on')v.click();window.scrollTo(0,0);return true;})()"""
TAP="""function tap(s){var n=document.querySelector('[data-sq="'+s+'"]'),r=n.getBoundingClientRect();n.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,button:0,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));} """
def show_card(key,callback=None):
    mw.reviewer.card=mw.col.get_card(cards[key])
    mw.reviewer._showQuestion()
    later(.22,lambda:js(SUPPRESS_VOICE,lambda value:callback() if callback else None))

def begin():
    assert Path(mw.pm.base).resolve()==base.resolve() and mw.col.card_count()==0
    from chess_for_anki import note_type,config,progression
    from chess_for_anki.faq_dialog import FaqDialog
    for dlg in mw.findChildren(FaqDialog):
        if dlg.isVisible():dlg.accept()
    settings=config.get_config()
    settings.update(voice_pack='system',sound_enabled=True,confetti_enabled=True,narration_rate=1.5)
    config.save_config(settings)
    mw.col.set_config(progression.TUTORIAL_KEY,True)
    mw.col.set_config(progression.DEMO_KEY,{'enabled':False,'seen':[]})
    mw.col.set_config(progression.KEY,{'level':'16','wins':[]})
    selections={
        'opening':next(c for c in sample if c['start']=='' and c['side']=='white' and 'Italian' in c['title']),
        'brilliant':next(c for c in sample if c.get('source_id')=='brilliancy-001' or (c.get('brilliant_moves') and c['moves']==['Qb8+','Nxb8','Rd8#'])),
        'endgame':next(c for c in sample if c['start'] and 'endgame' in str(c.get('kind','')).lower()),
        'middlegame':next(c for c in sample if c['start'] and c['title'].startswith('Middlegame')),
    }
    for key,card in selections.items():
        note=note_type.create_note(mw.col,card['title'],card['side'],card['moves'],start_fen=card['start'],book_notes=card['notes'],brilliant_moves=card.get('brilliant_moves',''),previous_move=card.get('previous_move',''))
        mw.col.add_note(note,mw.col.decks.id('Video QA'))
        cards[key]=note.cards()[0].id
    col=mw.col;col.sched.suspend_cards([cid for cid in cards.values() if cid!=cards['opening']]);col.sched.unsuspend_cards([cards['opening']]);col.decks.select(col.get_card(cards['opening']).did)
    mw.resize(1000,1140)
    mw.moveToState('overview')
    later(.3,lambda:mw.moveToState('review'))
    later(1.4,prepare)

def prepare():
    js(SUPPRESS_VOICE,start_capture)

def start_capture(value):
    global started,timer
    assert value
    started=time.monotonic()
    timer=QTimer(mw);timer.setInterval(round(1000/fps));timer.timeout.connect(checked(capture));timer.start()
    capture()
    cursor=.35
    for index,clip in enumerate(narration['clips']):
        length=clip['1.5x']['duration']+1.2
        report['scenes'].append({'id':clip['id'],'start':cursor,'duration':length,'speech_start':cursor+.15,'speech_duration':clip['1.5x']['duration'],'speech_file':clip['1.5x']['file'],'text':clip['text']})
        later(cursor,lambda i=index:scene(i))
        cursor+=length
    report['planned_duration']=cursor+.5
    later(cursor+.5,finish)

def scene(index):
    event('scene_start',narration['clips'][index]['id'])
    if index==0:
        event('opening_initial')
    elif index==1:
        js("document.getElementById('studio-show-demo').click();")
        for n,delay in enumerate((.7,1.8,2.9,4.0,5.1)):
            later(delay,lambda ply=n+1:demo_next('opening_demo',ply))
    elif index==2:
        show_card('brilliant',check_previous)
    elif index==3:
        js("document.getElementById('studio-show-demo').click();")
        for n,delay in enumerate((.7,2.3,4.1)):
            later(delay,lambda ply=n+1:demo_next('brilliant_demo',ply))
    elif index==4:
        js("document.getElementById('studio-demo-skip').click();window.scrollTo(0,0);")
        later(2.8,practice_queen)
        later(4.45,check_reply)
    elif index==5:
        later(.4,practice_rook)
        later(2.5,check_completion)
    elif index==6:
        show_card('endgame',lambda:event('sample_endgame_visible'))
        later(3.1,lambda:show_card('middlegame',lambda:event('sample_middlegame_visible')))
        later(6.2,lambda:show_card('brilliant',lambda:event('sample_brilliancy_visible')))

def check_previous():
    js("""(()=>{return {last:Array.from(document.querySelectorAll('.sq.lastmove')).map(x=>x.dataset.sq).sort(),caption:document.getElementById('studio-previous-caption').textContent,meter:!!document.getElementById('studio-evaluation')};})()""",previous_result)
def previous_result(value):
    assert value['last']==['d7','f6'] and value['meter'] is False,value
    report['checks']['previous_move']=value
    event('previous_move_highlight',value)
def demo_next(kind,ply):
    js("""(()=>{var b=document.getElementById('studio-demo-next');if(!b||b.disabled)return {error:'No next move'};b.click();window.scrollTo(0,0);return {count:document.getElementById('studio-depth-count').textContent,brilliant:document.querySelectorAll('.brilliant-square').length};})()""",lambda value:demo_result(kind,ply,value))
def demo_result(kind,ply,value):
    assert not value.get('error') and value['brilliant']==0,value
    event(kind,dict(ply=ply,**value))
def practice_queen():
    js("(()=>{"+TAP+"tap('b3');tap('b8');return {badge:document.querySelector('.brilliant-badge')?.textContent,particles:document.querySelectorAll('#studio-brilliant i').length};})()",queen_result)
def queen_result(value):
    assert value['badge']=='!!' and value['particles']>0,value
    report['checks']['brilliant_reward']=value
    event('practice_queen',value)
    mw.reviewer.web.grab().save(str(output/'brilliant-reward.png'))
def check_reply():
    js("""(()=>{return {piece:!!document.querySelector('[data-sq="b8"] .piece'),hint:document.getElementById('attempt-hint').textContent};})()""",lambda value:event('automatic_reply',value))
def practice_rook():
    js("(()=>{"+TAP+"tap('d1');tap('d8');return {complete:window._cotResult?.success,banner:document.getElementById('result-bar').textContent,confetti:document.querySelectorAll('#studio-celebration i').length};})()",rook_result)
def rook_result(value):
    # A rehearsal after demo counts as assisted, so success can be false while
    # the displayed line is complete. Never relabel that as unaided mastery.
    assert value['banner'].startswith('Line complete') and value['confetti']>0,value
    report['checks']['line_finished']=value
    event('practice_rook_mate',value)
    later(.12,lambda:mw.reviewer.web.grab().save(str(output/'brilliancy-complete.png')))
def check_completion():
    js("""(()=>{return {answer:!!document.getElementById('chessline-back'),repeat:!!document.getElementById('studio-repeat')&&!document.getElementById('studio-repeat').hidden};})()""",completion_result)
def completion_result(value):
    assert value['answer'] and value['repeat'],value
    report['checks']['answer_and_repeat']=value
    event('answer_and_repeat',value)
def finish():
    assert report['checks'].get('previous_move') and report['checks'].get('brilliant_reward') and report['checks'].get('line_finished') and report['checks'].get('answer_and_repeat')
    report['personal_profile_accessed']=False
    report['sync_account_present']=False
    done()

gui_hooks.profile_did_open.append(lambda:QTimer.singleShot(1000,checked(begin)))
