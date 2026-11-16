const assert=require('node:assert/strict');
const brilliant=require('../chess_for_anki/web/brilliant.js');
assert.deepEqual(brilliant.parse('{"schema":1,"plies":[3,1]}',3),[1,3]);
for(const raw of ['',null,'{"schema":true,"plies":[1]}','{"schema":1,"plies":[0]}','{"schema":1,"plies":[1,1]}','{"schema":1,"plies":[4]}','{"schema":1,"plies":[true]}','{"schema":1,"plies":[1],"script":"alert(1)"}'])assert.deepEqual(brilliant.parse(raw,3),[]);
const base={mode:'attempt',correct:true,canonical:true,playerMove:true};
assert.equal(brilliant.shouldReward([1,3],1,base),true);
assert.equal(brilliant.shouldReward([1,3],2,base),false);
for(const options of [{mode:'demo'},{mode:'review'},{correct:false},{canonical:false},{playerMove:false}])assert.equal(brilliant.shouldReward([1],1,{...base,...options}),false);
console.log('Brilliant metadata, wrong moves, demos, automatic replies and alternate finishes passed.');
