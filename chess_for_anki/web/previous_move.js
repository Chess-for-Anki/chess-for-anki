(function(root){
  'use strict';
  function validFen(fen){
    if(typeof fen!=='string' || fen.length>128 || /[\x00-\x1f\x7f]/.test(fen))return false;
    var p=fen.trim().split(/\s+/),rows=p[0].split('/');
    return p.length===6 && rows.length===8 && (p[0].match(/K/g)||[]).length===1 && (p[0].match(/k/g)||[]).length===1 && rows.every(function(row){
      return /^[prnbqkPRNBQK1-8]+$/.test(row) && row.split('').reduce(function(n,c){return n+(/[1-8]/.test(c)?Number(c):1);},0)===8;
    }) && /^(w|b)$/.test(p[1]) && /^(?:-|K?Q?k?q?)$/.test(p[2]) && !!p[2] && /^(?:-|[a-h][36])$/.test(p[3]) && /^(0|[1-9][0-9]{0,5})$/.test(p[4]) && /^[1-9][0-9]{0,5}$/.test(p[5]);
  }
  function positionKey(game){
    var parts=game.fen().split(/\s+/),ep=parts[3];
    if(ep && ep!=='-'){
      var side=parts[1],rank=Number(ep[1])+(side==='w'?-1:1),canCapture=false;
      [-1,1].forEach(function(offset){
        var file=ep.charCodeAt(0)+offset;
        if(file<97 || file>104)return;
        var from=String.fromCharCode(file)+rank,piece=game.pieceAt(from);
        if(piece && piece.color===side && piece.type==='p' && game.legalDests(from).indexOf(ep)>=0)canCapture=true;
      });
      if(!canCapture)parts[3]='-';
    }
    return parts.slice(0,4).join(' ');
  }
  function parse(raw,startFen,ChessClass){
    if(typeof raw!=='string' || raw.length>2048 || !raw.trim() || !startFen || typeof ChessClass!=='function')return null;
    try{
      var keyTokens=/"((?:\\.|[^"\\])*)"\s*:/g,match,seenKeys=new Set();
      while((match=keyTokens.exec(raw))!==null){
        var key=JSON.parse('"'+match[1]+'"');
        if(seenKeys.has(key))return null;
        seenKeys.add(key);
      }
      var data=JSON.parse(raw);
      if(!data || Array.isArray(data) || data.schema!==1 || Object.keys(data).some(function(k){return ['schema','before_fen','uci','source'].indexOf(k)<0;}) ||
          !validFen(data.before_fen) ||
          typeof data.uci!=='string' || !/^[a-h][1-8][a-h][1-8][qrbn]?$/.test(data.uci) ||
          (Object.prototype.hasOwnProperty.call(data,'source') && ['historical','constructed','user'].indexOf(data.source)<0))return null;
      var before=new ChessClass(data.before_fen),target=new ChessClass(startFen);
      if(before.turnColor()===target.turnColor())return null;
      var checkParts=data.before_fen.split(/\s+/);checkParts[1]=before.turnColor()==='w'?'b':'w';
      if(new ChessClass(checkParts.join(' ')).inCheck())return null;
      var from=data.uci.slice(0,2),to=data.uci.slice(2,4),piece=before.pieceAt(from);
      if(piece && piece.type==='p' && from[0]!==to[0] && !before.pieceAt(to)){
        var captured=before.pieceAt(to[0]+from[1]);
        if(checkParts[3]!==to || !captured || captured.type!=='p' || captured.color===piece.color)return null;
      }
      var promotes=piece && piece.type==='p' && /[18]$/.test(to);
      if(promotes!==(data.uci.length===5))return null;
      var move=before.moveFromTo(from,to,data.uci.slice(4));
      if(!move || positionKey(before)!==positionKey(target))return null;
      return {from:from,to:to,san:move.san,source:data.source || 'user'};
    }catch(error){return null;}
  }
  var api={parse:parse,positionKey:positionKey};
  if(typeof module==='object' && module.exports)module.exports=api;
  else root.CFA_PREVIOUS_MOVE=api;
})(typeof window==='object'?window:globalThis);
