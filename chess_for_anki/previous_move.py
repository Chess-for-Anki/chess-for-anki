"""Bounded setup context for a custom-position card, separate from its solution."""
import json
import re

MAX_BYTES=2048
SOURCES=('historical','constructed','user')

def _fen(value):
    if not isinstance(value,str) or len(value)>128 or any(ord(ch)<32 for ch in value):
        return False
    parts=value.split()
    if len(parts)!=6 or parts[1] not in ('w','b'):
        return False
    rows=parts[0].split('/')
    if len(rows)!=8 or parts[0].count('K')!=1 or parts[0].count('k')!=1:
        return False
    for row in rows:
        if not re.fullmatch('[prnbqkPRNBQK1-8]+',row) or sum(int(ch) if ch.isdigit() else 1 for ch in row)!=8:
            return False
    return bool(re.fullmatch(r'-|K?Q?k?q?',parts[2]) and parts[2] and
                re.fullmatch(r'-|[a-h][36]',parts[3]) and
                re.fullmatch(r'0|[1-9][0-9]{0,5}',parts[4]) and
                re.fullmatch(r'[1-9][0-9]{0,5}',parts[5]))

def validate(data,start_fen=None):
    if (type(data) is not dict or set(data)-{'schema','before_fen','uci','source'} or
            not {'schema','before_fen','uci'}<=set(data) or type(data['schema']) is not int or data['schema']!=1 or
            not _fen(data['before_fen']) or type(data['uci']) is not str or
            not re.fullmatch(r'[a-h][1-8][a-h][1-8][qrbn]?',data['uci']) or data['uci'][:2]==data['uci'][2:4] or
            data.get('source','user') not in SOURCES):
        raise ValueError('Previous move needs a valid preceding FEN and UCI move, such as e7e5.')
    clean={'schema':1,'before_fen':' '.join(data['before_fen'].split()),'uci':data['uci'],'source':data.get('source','user')}
    if start_fen is not None:
        _verify_transition(clean,start_fen)
    return clean

def _verify_transition(data,start_fen):
    from . import chess_logic as chess
    parts=(start_fen or '').split()
    if len(parts)<2 or parts[1] not in ('w','b'):
        raise ValueError('A previous move belongs to a custom starting position.')
    before=data['before_fen'].split()
    board,turn=chess.board_from_fen(data['before_fen'])
    target,target_turn=chess.board_from_fen(start_fen)
    if turn==target_turn or chess.in_check(board,'b' if turn=='w' else 'w'):
        raise ValueError('The previous move must be the opponent\'s legal move.')
    uci=data['uci'];origin,dest=uci[:2],uci[2:4]
    fr,ff=int(origin[1])-1,ord(origin[0])-97
    tr,tf=int(dest[1])-1,ord(dest[0])-97
    piece=board[fr][ff]
    if not piece or piece[0]!=turn:
        raise ValueError('No opponent piece on the previous move\'s origin square.')
    promotion=uci[4:].upper()
    if promotion and (piece[1]!='P' or tr not in (0,7)):
        raise ValueError('Only a pawn reaching the last rank can promote.')
    if piece[1]=='P' and tr in (0,7) and not promotion:
        raise ValueError('Specify the promotion piece in the previous move.')
    ep=None if before[3]=='-' else (int(before[3][1])-1,ord(before[3][0])-97)
    if piece[1]=='P' and ff!=tf and board[tr][tf] is None and board[fr][tf]!=(('b' if turn=='w' else 'w')+'P'):
        raise ValueError('Invalid previous en passant capture.')
    if piece[1]=='K' and ff==4 and abs(tf-ff)==2:
        right=('K' if tf==6 else 'Q') if turn=='w' else ('k' if tf==6 else 'q')
        if tr!=fr or right not in before[2] or board[fr][7 if tf==6 else 0]!=turn+'R':
            raise ValueError('The previous castling move has no castling right or rook.')
        san='O-O' if tf==6 else 'O-O-O'
    else:
        san=('' if piece[1]=='P' else piece[1])+origin+dest+('='+promotion if promotion else '')
    moved_piece=piece
    try:new_ep=chess.apply_san(board,turn,san,ep)
    except ValueError as exc:raise ValueError('The previous move is illegal.') from exc
    if board!=target:
        raise ValueError('The previous move does not produce this starting position.')
    if len(parts)>=6:
        rights=before[2]
        if moved_piece[1]=='K':
            for char in ('KQ' if turn=='w' else 'kq'):rights=rights.replace(char,'')
        for square,right in [('a1','Q'),('h1','K'),('a8','q'),('h8','k')]:
            if origin==square or dest==square:rights=rights.replace(right,'')
        if (rights or '-')!=parts[2]:
            raise ValueError('Previous move castling rights do not match this position.')
        target_ep=None if parts[3]=='-' else (int(parts[3][1])-1,ord(parts[3][0])-97)
        def legal_ep(ep_square):
            if ep_square is None:return None
            r,f=ep_square;row=r-1 if target_turn=='w' else r+1
            for file in (f-1,f+1):
                if not (0<=row<8 and 0<=file<8) or board[row][file]!=target_turn+'P':continue
                attempt=[rank[:] for rank in board]
                try:
                    token=chr(97+file)+str(row+1)+chr(97+f)+str(r+1)
                    chess.apply_san(attempt,target_turn,token,ep_square)
                    return ep_square
                except ValueError:pass
            return None
        if legal_ep(new_ep)!=legal_ep(target_ep):
            raise ValueError('Previous move en passant state does not match this position.')

def loads(raw,start_fen=None):
    if not isinstance(raw,str) or len(raw.encode('utf8'))>MAX_BYTES:
        raise ValueError('Previous move metadata exceeds 2 KiB.')
    def unique(pairs):
        data={}
        for key,value in pairs:
            if key in data:raise ValueError('Duplicate previous move JSON key.')
            data[key]=value
        return data
    try:data=json.loads(raw,object_pairs_hook=unique)
    except (ValueError,RecursionError) as exc:raise ValueError('Invalid previous move JSON.') from exc
    return validate(data,start_fen)

def dumps(data,start_fen=None):
    return json.dumps(validate(data,start_fen),ensure_ascii=True,separators=(',',':'))

def setup_from_pgn(text):
    """Return (final full FEN, last-move context) from a complete setup mainline."""
    from . import chess_logic as chess
    from .pgn_parser import parse_pgn_moves
    standard='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    tag=re.search(r'\[FEN\s+"([^"]+)"\]',text)
    fen=tag.group(1).strip() if tag else standard
    if not _fen(fen):raise ValueError('The setup PGN needs a complete valid starting FEN.')
    moves=parse_pgn_moves(text)
    if not moves:
        if tag:return fen,None
        raise ValueError('No setup moves found.')
    context=None
    for san in moves:
        board,turn=chess.board_from_fen(fen)
        parts=fen.split();old=[row[:] for row in board]
        ep=None if parts[3]=='-' else (int(parts[3][1])-1,ord(parts[3][0])-97)
        new_ep=chess.apply_san(board,turn,san,ep)
        sources=[(r,f) for r in range(8) for f in range(8) if old[r][f] and old[r][f][0]==turn and board[r][f]!=old[r][f]]
        if san.replace('0','O').startswith('O-O'):
            fr,ff=(0 if turn=='w' else 7),4;tr,tf=fr,(2 if san.replace('0','O').startswith('O-O-O') else 6)
        else:
            origins=[(r,f) for r,f in sources if board[r][f] is None]
            destinations=[(r,f) for r in range(8) for f in range(8) if board[r][f] and board[r][f][0]==turn and board[r][f]!=old[r][f]]
            if len(origins)!=1 or len(destinations)!=1:raise ValueError('Cannot identify the setup move.')
            fr,ff=origins[0];tr,tf=destinations[0]
        def name(r,f):return chr(97+f)+str(r+1)
        promotion=board[tr][tf][1].lower() if old[fr][ff][1]=='P' and board[tr][tf][1]!='P' else ''
        uci=name(fr,ff)+name(tr,tf)+promotion
        rights=parts[2]
        if old[fr][ff][1]=='K':
            for char in ('KQ' if turn=='w' else 'kq'):rights=rights.replace(char,'')
        for square,right in [('a1','Q'),('h1','K'),('a8','q'),('h8','k')]:
            if name(fr,ff)==square or name(tr,tf)==square:rights=rights.replace(right,'')
        captured=old[tr][tf] is not None or (old[fr][ff][1]=='P' and ff!=tf)
        half=0 if old[fr][ff][1]=='P' or captured else int(parts[4])+1
        full=int(parts[5])+(turn=='b')
        next_turn='b' if turn=='w' else 'w'
        ep_name=name(*new_ep) if new_ep else '-'
        after=chess.board_to_simple_fen(board,next_turn)+' '+(rights or '-')+' '+ep_name+' '+str(half)+' '+str(full)
        context=validate({'schema':1,'before_fen':fen,'uci':uci,'source':'user'},after)
        fen=after
    return fen,context
