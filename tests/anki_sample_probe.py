"""QA-only sample export. Invoked by scripts/verify_free_sample.py."""
import hashlib,json,os,traceback
from pathlib import Path
from aqt import gui_hooks,mw
from aqt.qt import QTimer

base=Path(os.environ['CFA_SAMPLE_BASE']);output=Path(os.environ['CFA_SAMPLE_OUTPUT'])
report={}
cards=json.loads((base/'sample.json').read_text(encoding='utf8'))

def done():
    (output/'sample-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    QTimer.singleShot(100,mw.unloadProfileAndExit)
def checked(fn):
    def call(*args):
        try:fn(*args)
        except Exception:report['error']=traceback.format_exc();done()
    return call
def begin():
    assert Path(mw.pm.base).resolve()==base.resolve() and mw.col.card_count()==0
    from chess_for_anki import note_type,config,progression
    from chess_for_anki.faq_dialog import FaqDialog
    for dlg in mw.findChildren(FaqDialog):
        if dlg.isVisible():dlg.accept()
    settings=config.get_config();settings.update(voice_pack='system',sound_enabled=False);config.save_config(settings)
    mw.col.set_config(progression.TUTORIAL_KEY,True);mw.col.set_config(progression.DEMO_KEY,{'enabled':False,'seen':[]})
    assert len(cards)==22 and len({c['id'] for c in cards})==22
    initial_custom=None
    for card in cards:
        note=note_type.create_note(mw.col,card['title'],card['side'],card['moves'],start_fen=card['start'],book_notes=card['notes'],brilliant_moves=card.get('brilliant_moves',''),previous_move=card.get('previous_move',''))
        note.guid=hashlib.sha256(('cfa:free-sample:'+card['id']).encode()).hexdigest()[:16]
        note.tags=card['tags']+['cfa_free_sample']
        mw.col.add_note(note,mw.col.decks.id('Chess - Free Sample::'+card['group']))
        if card['start'] and initial_custom is None:initial_custom=note.cards()[0]
    assert mw.col.card_count()==22
    assert sum(bool(c['start']) for c in cards)==12
    # Structured context must be rendered as text before its JSON parser runs.
    security_note = note_type.create_note(mw.col,'Temporary rendering check','white',['e4'])
    security_note['Previous Move'] = '</span><img src=x onerror="window.cfaContextInjected=true"><span>'
    mw.col.add_note(security_note,mw.col.decks.id('Temporary QA'))
    assert 'window.cfaContextInjected' not in security_note.cards()[0].question()
    mw.col.remove_notes([security_note.id])
    assert mw.col.card_count()==22
    report['structured_context_html_is_stripped_before_json_parse']=True
    report.update(cards=22,opening_cards=10,unique_openings=5,brilliancy=3,endgames=3,middlegames=3,tactics=3,all_custom_positions_have_previous_move=True)
    from anki.exporting import AnkiPackageExporter
    exporter=AnkiPackageExporter(mw.col);exporter.did=mw.col.decks.id_for_name('Chess - Free Sample');exporter.includeSched=False;exporter.includeMedia=False
    target=output/'Chess-for-Anki-Free-Sample.apkg';exporter.exportInto(str(target))
    report['apkg_bytes']=target.stat().st_size;report['apkg_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    col=mw.col;col.remove_notes(col.find_notes('tag:cfa_free_sample'));assert col.card_count()==0
    from anki.collection import ImportAnkiPackageRequest,ImportAnkiPackageOptions
    col.import_anki_package(ImportAnkiPackageRequest(package_path=str(target),options=ImportAnkiPackageOptions(merge_notetypes=True,with_scheduling=False,with_deck_configs=False)))
    assert col.card_count()==22 and col.db.scalar('select count(*) from revlog')==0
    assert all(col.get_note(n)['Personal Notes']=='' for n in col.find_notes('tag:cfa_free_sample'))
    report['roundtrip_cards']=22;report['no_personal_notes_or_reviews']=True
    custom=next(col.get_note(n).cards()[0] for n in col.find_notes('tag:cfa_free_sample') if col.get_note(n)['StartFEN'])
    col.sched.suspend_cards([cid for cid in col.find_cards('tag:cfa_free_sample') if cid!=custom.id]);col.sched.unsuspend_cards([custom.id]);col.decks.select(custom.did)
    mw.resize(900,1000);mw.moveToState('overview')
    QTimer.singleShot(300,lambda:mw.moveToState('review'))
    QTimer.singleShot(1400,checked(check_render))
def check_render():
    cases=[dict(start=c['start'],moves=c['moves'],fens=c['fens'],previous=c.get('previous_move')) for c in cards]
    script="""(()=>{var cases=CASES,plies=0,contexts=0;for(var c of cases){var g=new Chess(c.start||undefined);if(c.start){if(!CFA_PREVIOUS_MOVE.parse(JSON.stringify(c.previous),c.start,Chess))return {error:'Previous move invalid'};contexts++;}for(var i=0;i<c.moves.length;i++){if(!g.move(c.moves[i]))return {error:'Illegal move',ply:i+1};if(g.fen().split(' ').slice(0,3).join(' ')!==c.fens[i].split(' ').slice(0,3).join(' '))return {error:'Position differs',ply:i+1};plies++;}}return {plies:plies,contexts:contexts,squares:document.querySelectorAll('.sq').length,previousSquares:document.querySelectorAll('.sq.lastmove').length,meterExists:!!document.getElementById('studio-evaluation')};})()""".replace('CASES',json.dumps(cases))
    def finish(result):
        assert result and not result.get('error') and result['contexts']==12 and result['previousSquares']==2 and result['squares']==64 and result['meterExists'] is False,result
        report['native_replay']=result
        mw.reviewer.web.grab().save(str(output/'Free sample - previous move.png'))
        done()
    mw.reviewer.web.evalWithCallback(script,checked(finish))
gui_hooks.profile_did_open.append(lambda:QTimer.singleShot(900,checked(begin)))
