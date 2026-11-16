import html
import json
from aqt import gui_hooks, mw
from aqt.utils import tooltip

LEVELS = ['8', '16', '24', '40', 'all']
NAMES = ['Noobie', 'Beginner', 'Intermediate', 'Advanced', 'HACKER']
KEY = 'fernandoChessRepertoireProgress'
DEMO_KEY = 'fernandoChessFirstDemo'
TUTORIAL_KEY = 'chessForAnkiRoundTutorialSeen'
pending = {}

def is_chess(card):
    from .note_type import is_chess_notetype
    return is_chess_notetype(card.note_type())


def state():
    progress=mw.col.get_config(KEY, {'level':'8', 'wins':[]})
    if not isinstance(progress,dict) or progress.get('level') not in LEVELS:
        return {'level':'8','wins':[]}
    level=progress['level']
    limit=int(level) if level!='all' else 600
    wins=progress.get('wins',[])
    wins=list(dict.fromkeys(' '.join(line.split()[:limit]) for line in wins if isinstance(line,str))) if isinstance(wins,list) else []
    return {'level':level,'wins':wins}

def render(markup, card, kind):
    if kind in ('reviewQuestion','reviewAnswer') and not is_chess(card):
        from . import narration
        narration.stop()
        return markup
    if kind not in ('reviewQuestion','reviewAnswer') or not is_chess(card):
        return markup
    if kind == 'reviewQuestion':
        pending.clear()
    demo=mw.col.get_config(DEMO_KEY,{'enabled':True,'seen':[]})
    from . import config
    rate=config.narration_rate(config.get_config()["narration_rate"])
    marker = '<span id="studio-state" hidden data-card="{}" data-demo="{}" data-first="{}" data-speed="{}">{}</span>'.format(
        card.id, 'on' if demo['enabled'] else 'off',
        'yes' if card.reps==0 and str(card.id) not in demo['seen'] else 'no',
        rate,
        html.escape(json.dumps(state())))
    if kind == 'reviewQuestion' and not mw.col.get_config(TUTORIAL_KEY, False):
        from .faq_dialog import uses_portuguese
        language = 'pt' if uses_portuguese() else 'en'
        marker += f'<span id="studio-first-round" hidden lang="{language}"></span>'
    return markup.replace('<div id="studio-fields"',marker+'<div id="studio-fields"',1)

def bridge(handled, message, context):
    if handled[0] or not message.startswith('studio-level:'):
        return handled
    reviewer=mw.reviewer
    card=reviewer.card
    if context is not reviewer or not card or not is_chess(card):
        return True,None
    if len(message)>20000:
        return True,None
    try:
        data=json.loads(message.split(':',1)[1])
    except (ValueError,TypeError):
        return True,None
    if not isinstance(data,dict):
        return True,None
    if str(card.id)!=data.get('card'):
        return True,None
    value=data.get('value')
    if data.get('action') in ('speech','speech-stop'):
        from . import narration
        if data['action']=='speech-stop':
            narration.stop()
        else:
            narration.speak(value)
        return True,None
    if data.get('action') == 'audio-rate':
        from . import config
        if type(value) in (int,float) and value in config.NARRATION_SPEEDS:
            settings=config.get_config()
            settings['narration_rate']=float(value)
            config.save_config(settings)
        return True,None
    if data.get('action') == 'open-settings' and reviewer.state == 'question':
        from .main import settings
        from aqt.qt import QTimer
        QTimer.singleShot(0, settings)
        return True,None
    if data.get('action') == 'tutorial-seen' and reviewer.state == 'question':
        mw.col.set_config(TUTORIAL_KEY, True)
        return True,None
    if data.get('action') in ('demo-toggle','demo-seen'):
        demo=mw.col.get_config(DEMO_KEY,{'enabled':True,'seen':[]})
        if data['action']=='demo-toggle' and isinstance(value,bool):
            demo['enabled']=value
        elif data['action']=='demo-seen' and reviewer.state=='question' and str(card.id) not in demo['seen']:
            demo['seen'].append(str(card.id))
        mw.col.set_config(DEMO_KEY,demo)
        return True,None
    if reviewer.state!='question':
        return True,None
    if data.get('action')=='select' and value in LEVELS:
        pending.clear()
        if state()['level']!=value:
            mw.col.set_config(KEY,{'level':value,'wins':[]})
    elif data.get('action')=='finish':
        pending[card.id]=value
    return True,None

def answer(reviewer, card, ease):
    level=pending.pop(card.id,None)
    if ease<3 or level not in LEVELS[:-1]:
        return
    progress=state()
    if level!=progress['level']:
        return
    note=card.note()
    plies=note['MovesPGN'].split()
    if note['StartFEN'].strip() or len(plies)<int(level):
        return
    # Different long branches with the same rehearsed prefix count only once.
    moves=' '.join(plies[:int(level)])
    if moves in progress['wins']:
        return
    progress['wins'].append(moves)
    if len(progress['wins'])>=3:
        index=LEVELS.index(level)+1
        progress={'level':LEVELS[index],'wins':[]}
        tooltip('Level up · '+NAMES[index])
    mw.col.set_config(KEY,progress)

def footer(card):
    is_chess=is_chess(card)
    # The theme sets the native rating text to font-size zero.
    script="""(()=>{let s=document.getElementById('studio-rating-labels');
    if(!s){s=document.createElement('style');s.id='studio-rating-labels';document.head.append(s);}
    s.textContent='#outer #middle table tr td:not(.stat2) button[data-ease]{font-size:13px!important}';})();"""
    mw.reviewer.bottom.web.eval(script if is_chess else "document.getElementById('studio-rating-labels')?.remove()")
    labels="""(()=>{document.querySelectorAll('.ba-rv-ease-key').forEach(b=>{
      let label=b.querySelector('.studio-rating-label');
      if(!label){label=document.createElement('span');label.className='studio-rating-label';b.prepend(label);}
      label.textContent=['','Again','Hard','Good','Easy'][Number(b.dataset.ease)];
      label.style.cssText='display:block;font-size:13px;line-height:18px;margin-bottom:5px';
    });})();"""
    mw.reviewer.web.eval(labels if is_chess else "document.querySelectorAll('.studio-rating-label').forEach(s=>s.remove())")

def register():
    gui_hooks.card_will_show.append(render)
    gui_hooks.webview_did_receive_js_message.append(bridge)
    gui_hooks.reviewer_did_answer_card.append(answer)
    gui_hooks.reviewer_did_show_answer.append(footer)
