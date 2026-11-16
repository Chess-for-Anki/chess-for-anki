/* Recorded packs keep stable English keys; system speech is localized separately. */
var CFA_SPEECH = (function () {
  var lexicons = {
    pt: {colors:['Brancas','Pretas'],pieces:['rei','dama','torre','bispo','cavalo','peão'],to:'para',from:'de',takes:'captura em',check:'xeque',mate:'xeque-mate',promote:'promove a',castle:['roque pequeno','roque grande'],try:'Tente {piece}.',illegal:'Lance ilegal.',on:'Narração ativada.',level:'Nível {level}.'},
    es: {colors:['Blancas','Negras'],pieces:['rey','dama','torre','alfil','caballo','peón'],to:'a',from:'de',takes:'captura en',check:'jaque',mate:'jaque mate',promote:'promociona a',castle:['enroque corto','enroque largo'],try:'Prueba con {piece}.',illegal:'Jugada ilegal.',on:'Narración activada.',level:'Nivel {level}.'},
    fr: {colors:['Blancs','Noirs'],pieces:['roi','dame','tour','fou','cavalier','pion'],to:'en',from:'de',takes:'prend en',check:'échec',mate:'échec et mat',promote:'promotion en',castle:['petit roque','grand roque'],try:'Essayez le {piece}.',illegal:'Coup illégal.',on:'Narration activée.',level:'Niveau {level}.'},
    de: {colors:['Weiß','Schwarz'],pieces:['König','Dame','Turm','Läufer','Springer','Bauer'],to:'nach',from:'von',takes:'schlägt auf',check:'Schach',mate:'Schachmatt',promote:'Umwandlung in',castle:['kurze Rochade','lange Rochade'],try:'Versuche {piece}.',illegal:'Ungültiger Zug.',on:'Sprachausgabe aktiviert.',level:'Stufe {level}.'},
    ru: {colors:['Белые','Чёрные'],pieces:['король','ферзь','ладья','слон','конь','пешка'],to:'на',from:'с',takes:'берёт на',check:'шах',mate:'мат',promote:'превращение в',castle:['короткая рокировка','длинная рокировка'],try:'Попробуйте: {piece}.',illegal:'Недопустимый ход.',on:'Озвучивание включено.',level:'Уровень {level}.'},
    zh: {colors:['白方','黑方'],pieces:['王','后','车','象','马','兵'],to:'到',from:'从',takes:'吃子在',check:'将军',mate:'将死',promote:'升变为',castle:['王翼易位','后翼易位'],try:'请移动{piece}。',illegal:'不合法的着法。',on:'语音已开启。',level:'{level}级别。'},
    ja: {colors:['白','黒'],pieces:['キング','クイーン','ルーク','ビショップ','ナイト','ポーン'],to:'へ',from:'から',takes:'で駒を取る',check:'チェック',mate:'チェックメイト',promote:'に昇格',castle:['キングサイドのキャスリング','クイーンサイドのキャスリング'],try:'{piece}を動かしてください。',illegal:'不正な手です。',on:'音声をオンにしました。',level:'レベル{level}。'}
  };
  var names=['king','queen','rook','bishop','knight','pawn'];
  var numbers=['one','two','three','four','five','six','seven','eight'];
  function text(value, locale, overrides) {
    if(overrides && typeof overrides[value]==='string')return overrides[value];
    var dictionary=lexicons[String(locale).split('-')[0]];
    if(!dictionary)return value;
    if(value==='Illegal move.')return dictionary.illegal;
    if(value==='Narrator on.')return dictionary.on;
    var hint=/^Try (?:a|the) (king|queen|rook|bishop|knight|pawn)\.$/.exec(value);
    if(hint)return dictionary.try.replace('{piece}',dictionary.pieces[names.indexOf(hint[1])]);
    var level=/^(Noobie|Beginner|Intermediate|Advanced|Hacker) level\.$/.exec(value);
    if(level)return dictionary.level.replace('{level}',level[1]);
    var move=/^(White|Black), (.+)\.$/.exec(value);
    if(!move)return value;
    var phrase=move[2];
    phrase=phrase.replace(/castles kingside/g,dictionary.castle[0]).replace(/castles queenside/g,dictionary.castle[1]);
    phrase=phrase.replace(/checkmate/g,dictionary.mate).replace(/\bcheck\b/g,dictionary.check);
    phrase=phrase.replace(/promotes to/g,dictionary.promote).replace(/takes on/g,dictionary.takes).replace(/\bfrom\b/g,dictionary.from).replace(/\bto\b/g,dictionary.to);
    phrase=phrase.replace(/\b(king|queen|rook|bishop|knight|pawn)\b/g,function(piece){return dictionary.pieces[names.indexOf(piece)];});
    phrase=phrase.replace(/\b([A-H]) (one|two|three|four|five|six|seven|eight)\b/g,function(_,file,rank){return file.toLowerCase()+(numbers.indexOf(rank)+1);});
    return dictionary.colors[move[1]==='White'?0:1]+', '+phrase+'.';
  }
  return {text:text};
})();
