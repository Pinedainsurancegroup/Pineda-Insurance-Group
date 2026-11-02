const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../app/src/main/java/com/pinedaagencygroup/leads/MainActivity.java'),'utf8');
const match=source.match(/String migration = "([^"]*)" \+ JSONObject.quote\(oldStorage\[0\]\) \+ "([^"]*)";/);
assert.ok(match,'migration script must remain testable');
function migrate(old,existing){
 const storage=new Map(Object.entries(existing));
 const script=match[1]+JSON.stringify(JSON.stringify(old))+match[2];
 vm.runInNewContext(script,{localStorage:{getItem:k=>storage.has(k)?storage.get(k):null,setItem:(k,v)=>storage.set(k,v)}});
 return Object.fromEntries(storage);
}
test('migration preserves notes and account drafts without overwriting newer state',()=>{
 const old={pagov:'old notes','pagcloud:owner:drafts':'pending',pagset12:'{"auto":false}'};
 const result=migrate(old,{pagov:'new notes'});
 assert.equal(result.pagov,'new notes');assert.equal(result['pagcloud:owner:drafts'],'pending');
 assert.deepEqual(migrate(old,result),result);
});
test('stored values remain data, including quotes and script-looking text',()=>{
 const payload='"; throw new Error("injection"); //</script>\u2028';
 assert.equal(migrate({pagov:payload},{}).pagov,payload);
});
test('migration reports success explicitly and does not hide storage write failures',()=>{
 const script=match[1]+JSON.stringify(JSON.stringify({pagov:'notes'}))+match[2];
 assert.equal(vm.runInNewContext(script,{localStorage:{getItem:()=>null,setItem(){}}}),true);
 assert.throws(()=>vm.runInNewContext(script,{localStorage:{getItem:()=>null,setItem(){throw Error('quota')}}}),/quota/);
});
