const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('fs');
const src=fs.readFileSync(__dirname+'/SparkRecruitmentIdentity.gs','utf8');
const headers=['Marca temporal','Nombre completo / Full name','Número de teléfono / Phone number','Correo electrónico / Email address'];
const id='r_11111111-1111-4111-8111-111111111111';
function app(rows){
 const writes=[],docs=new Map();let reads=0;
 const sheet={getDataRange:()=>({getDisplayValues:()=>rows}),getMaxColumns:()=>26,getRange:(r,c)=>({getValue:()=>rows[r-1]?.[c-1]||'',setValue:v=>{rows[r-1][c-1]=v;writes.push([r,c,v])}})};
 const context=vm.createContext({Set,console,Utilities:{getUuid:()=>rows.some(r=>r[4]===id)?'22222222-2222-4222-8222-222222222222':id.slice(2)},SpreadsheetApp:{openById:()=>({getSheetByName:()=>sheet})},
  pagPushConfig_:()=>({sheet:'source',tab:'Answers'}),pagPushOwner_:()=>true,pagPushWithLock_:f=>f(),pagPushHash_:()=> 'source-hash',
  pagPushFirestore_:(c,path,method,data)=>{reads++;if(method)docs.set(path,data);return docs.get(path)||null}});
 vm.runInContext(src,context);return {context,writes,docs,reads:()=>reads};
}
test('identity initialization appends only an ID cell; rerun preserves ID and answers',()=>{
 const rows=[headers.slice(),['date','Ana','555','a@example.test']],a=app(rows),before=JSON.stringify(rows[1]);
 a.context.pagPrepareRecruitmentIdentity();assert.equal(rows[0][4],'PAG_LEAD_ID');assert.equal(rows[1][4],id);
 assert.equal(JSON.stringify(rows[1].slice(0,4)),before);assert.equal(a.docs.size,1);
 a.context.pagPrepareRecruitmentIdentity();assert.equal(a.writes.length,2);assert.equal(a.docs.size,1);
});
test('IDs survive row reorder and duplicates fail before writing',()=>{
 const rows=[[...headers,'PAG_LEAD_ID'],['d','Ana','p','e',id],['d','B','q','f',id]],a=app(rows);
 assert.throws(()=>a.context.pagPrepareRecruitmentIdentity(),/DUPLICATE/);assert.equal(a.writes.length,0);
 rows[2][4]='r_22222222-2222-4222-8222-222222222222';rows.splice(1,2,rows[2],rows[1]);
 a.context.pagPrepareRecruitmentIdentity();assert.equal(rows[2][4],id);assert.equal(a.writes.length,0);
});
test('form trigger provisions only its new row and never rewrites other answers',()=>{
 const rows=[[...headers,'PAG_LEAD_ID'],['d','Ana','p','e',id],['d','B','q','f','']],a=app(rows);
 a.context.pagApplyRecruitmentIdentity_(3);assert.equal(a.writes.length,1);assert.equal(a.writes[0][0],3);assert.equal(a.reads(),2);
});
