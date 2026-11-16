/* Declarative, per-note brilliant moves. No engine or code is loaded from notes. */
(function (root) {
  'use strict';
  function parse(raw, moveCount) {
    if (typeof raw !== 'string' || raw.length > 8192 || !Number.isInteger(moveCount) || moveCount < 0 || moveCount > 600) return [];
    if (!raw.trim()) return [];
    try {
      var value=JSON.parse(raw);
      if (!value || Array.isArray(value) || typeof value !== 'object' || value.schema !== 1 ||
          Object.keys(value).some(function(key){return key!=='schema' && key!=='plies';}) ||
          !Array.isArray(value.plies) || value.plies.length > 600) return [];
      var seen=new Set();
      for (var i=0;i<value.plies.length;i++) {
        var ply=value.plies[i];
        if (!Number.isInteger(ply) || ply<1 || ply>moveCount || seen.has(ply)) return [];
        seen.add(ply);
      }
      return Array.from(seen).sort(function(a,b){return a-b;});
    } catch(error) { return []; }
  }
  function shouldReward(plies, ply, options) {
    return !!(options && options.mode==='attempt' && options.correct===true &&
      options.canonical===true && options.playerMove===true && plies.indexOf(ply)>=0);
  }
  var api={parse:parse,shouldReward:shouldReward};
  if (typeof module==='object' && module.exports) module.exports=api;
  else root.CFA_BRILLIANT=api;
})(typeof window==='object'?window:globalThis);
