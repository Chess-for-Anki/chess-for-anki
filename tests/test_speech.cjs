const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const scope={};vm.createContext(scope);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../chess_for_anki/web/speech.js'),'utf8'),scope);
const speech=scope.CFA_SPEECH;
assert.equal(speech.text('White, knight to F three.','en-US',{}),'White, knight to F three.');
assert.equal(speech.text('White, knight to F three.','pt-BR',{}),'Brancas, cavalo para f3.');
assert.equal(speech.text('Try a pawn.','pt-BR',{}),'Tente peão.');
assert.equal(speech.text('Black, castles kingside.','pt-BR',{}),'Pretas, roque pequeno.');
assert.equal(speech.text('White, pawn from E takes on D five, check.','pt-BR',{}),'Brancas, peão de E captura em d5, xeque.');
for(const locale of ['es-ES','ru-RU','zh-CN','ja-JP','fr-FR','de-DE']){
 assert(!speech.text('White, knight to F three.',locale,{}).includes('knight'));
 assert.notEqual(speech.text('Illegal move.',locale,{}),'Illegal move.');
}
assert.equal(speech.text('Narrator on.','es-ES',{'Narrator on.':'Custom narration'}),'Custom narration');
console.log('Basic speech localization, castling, captures/check, hints and external phrase overrides passed.');
