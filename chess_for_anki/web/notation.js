/* Display notation stays independent from the English SAN used by PGN and the engine. */
var CFA_NOTATION = (function () {
  var languages = {
    en: {pieces:{K:'K',Q:'Q',R:'R',B:'B',N:'N'},white:'White',black:'Black',history:'Message history',empty:'Messages will appear as you play.',hint:'Hint'},
    pt: {pieces:{K:'R',Q:'D',R:'T',B:'B',N:'C'},white:'Brancas',black:'Pretas',history:'Histórico de mensagens',empty:'As mensagens aparecerão conforme você joga.',hint:'Dica'}
  };
  function language(selected, packLanguage) {
    var value = selected === 'auto' ? packLanguage : selected;
    return String(value || 'en').toLowerCase().split('-')[0] === 'pt' ? 'pt' : 'en';
  }
  function san(value, lang) {
    var map = languages[lang].pieces;
    return String(value).replace(/^O-O(?:-O)?/, function(castle){return castle.replace(/O/g,'0');})
      .replace(/^[KQRBN]/,function(piece){return map[piece];})
      .replace(/=([QRBN])/g,function(match,piece){return '='+map[piece];});
  }
  function text(value, lang) {
    return String(value).replace(/\b(?:[KQRBN][a-h1-8]{0,2}x?[a-h][1-8](?:=[QRBN])?[+#]?|[a-h][18]=[QRBN][+#]?|O-O(?:-O)?[+#]?)(?!\w)/g,
      function(move){return san(move,lang);});
  }
  function label(move, side, ply, startFen, lang) {
    var fields = startFen.trim().split(/\s+/);
    var first = startFen ? Number(fields[5] || 1) : 1;
    var offset = startFen && fields[1] === 'b' ? 1 : 0;
    var number = first + Math.floor((ply + offset) / 2);
    return languages[lang][side === 'w' ? 'white' : 'black']+' · '+number+(side === 'w' ? '. ' : '... ')+san(move,lang);
  }
  return {languages:languages,language:language,san:san,text:text,label:label};
})();
