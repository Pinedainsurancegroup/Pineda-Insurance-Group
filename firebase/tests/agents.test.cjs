const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {initializeTestEnvironment,assertSucceeds,assertFails}=require('@firebase/rules-unit-testing');
const {doc,getDoc,getDocs,collection,query,where,setDoc,updateDoc,deleteDoc,serverTimestamp,writeBatch}=require('firebase/firestore');
const envOptions={projectId:'demo-pag-leads',firestore:{host:'127.0.0.1',port:8085,rules:fs.readFileSync(path.join(__dirname,'../firestore.rules'),'utf8')}};
let env,serial=0,passed=0;
const eventId=()=>`event_agents_${String(++serial).padStart(16,'0')}`;
const email=uid=>`${uid}@example.test`;
const db=(uid,verified=true,mail=email(uid))=>env.authenticatedContext(uid,{email:mail,email_verified:verified}).firestore();
async function check(label,fn){await fn();passed++;console.log(`PASS ${label}`)}
async function audited(d,bucket,id,data,actor,expected,beforeOverride){
 const ref=doc(d,`${bucket}/${id}`),old=await getDoc(ref),before=beforeOverride??(old.exists()?old.data():{}),eid=eventId();
 const after={...data,revision:expected??((old.data()?.revision??0)+1),lastEventId:eid,updatedBy:actor,updatedAt:serverTimestamp()};
 const b=writeBatch(d);b.set(ref,after);b.set(doc(d,`${bucket}/${id}/audit/${eid}`),{before,after,actorUid:actor,createdAt:serverTimestamp()});return b.commit();
}
const agent=(uid,scopes={clients:true,recruitment:true})=>({role:'agent',active:true,suspended:false,email:email(uid),name:uid,scopes});
const contact=(assignedTo='a')=>({name:'Ficticio',phone:'+15550000001',email:'ficticio@example.test',region:'CA',assignedTo});
const client=(assignedTo='a')=>({...contact(assignedTo),classification:'LEAD',status:'Nuevo',note:''});
const rid='r_11111111-1111-4111-8111-111111111111';
async function recEdit(d,actor,id,status='Contactado',kind='edit'){
 const stateRef=doc(d,`recruitmentState/${id}`),old=await getDoc(stateRef),before=old.exists()?old.data():{status:'Nuevo',note:'',revision:0},eid=eventId();
 const state={status,note:'Nota sintética',revision:before.revision+1,lastEventId:eid,updatedBy:actor,updatedAt:serverTimestamp()};
 const b=writeBatch(d);b.set(stateRef,state);b.set(doc(d,`recruitmentState/${id}/activity/${eid}`),{actorUid:actor,deviceId:'test_device_1234567890',kind,status,note:state.note,previousStatus:before.status,previousNote:before.note,baseRevision:before.revision,revision:state.revision,createdAt:serverTimestamp(),originalUpdatedAt:''});return b.commit();
}
(async()=>{env=await initializeTestEnvironment(envOptions);try{
 await env.clearFirestore();await env.withSecurityRulesDisabled(async c=>{await setDoc(doc(c.firestore(),'users/owner'),{role:'owner',active:true,suspended:false});});
 const owner=db('owner'),a=db('a'),b=db('b'),rec=db('rec'),fe=db('fe');
 await check('unknown verified identity reads own missing profile but no lists',async()=>{await assertSucceeds(getDoc(doc(a,'users/a')));await assertFails(getDocs(collection(a,'users')));await assertFails(getDocs(collection(a,'clients')));await assertFails(getDocs(collection(a,'accessRequests')));});
 await check('verified email request cannot spoof email, UID, role or unverified account',async()=>{
   const r={email:email('a'),name:'A',createdAt:serverTimestamp()};
   await assertFails(setDoc(doc(db('a',false),'accessRequests/a'),r));
   await assertFails(setDoc(doc(a,'accessRequests/a'),{...r,email:'owner@example.test'}));
   await assertFails(setDoc(doc(a,'accessRequests/b'),r));await assertFails(setDoc(doc(a,'accessRequests/a'),{...r,role:'owner'}));
   await assertSucceeds(setDoc(doc(a,'accessRequests/a'),r));await assertFails(setDoc(doc(a,'accessRequests/a'),r));
 });
 for(const uid of ['b','rec','fe'])await setDoc(doc(db(uid),`accessRequests/${uid}`),{email:email(uid),name:uid,createdAt:serverTimestamp()});
 await check('approval requires owner, request-bound email, valid scopes and atomic audit',async()=>{
   await assertFails(setDoc(doc(a,'users/a'),agent('a')));await assertFails(setDoc(doc(owner,'users/a'),agent('a')));
   await assertFails(audited(owner,'users','a',{...agent('a'),email:email('b')},'owner'));
   await assertFails(audited(owner,'users','a',{...agent('a'),role:'owner'},'owner'));
   await assertFails(audited(owner,'users','a',{...agent('a'),scopes:{clients:true,recruitment:true,admin:true}},'owner'));
   await assertSucceeds(audited(owner,'users','a',agent('a'),'owner'));
   await assertSucceeds(audited(owner,'users','b',agent('b'),'owner'));
   await assertSucceeds(audited(owner,'users','rec',agent('rec',{clients:false,recruitment:true}),'owner'));
   await assertSucceeds(audited(owner,'users','fe',agent('fe',{clients:true,recruitment:false}),'owner'));
 });
 await check('owner cannot alter own owner profile through client API',async()=>{await assertFails(updateDoc(doc(owner,'users/owner'),{active:false}));await assertFails(deleteDoc(doc(owner,'users/owner')));});
 await check('create and assign clients with immutable audit',async()=>{
   await assertFails(setDoc(doc(owner,'clients/c1'),client()));await assertSucceeds(audited(owner,'clients','c1',client(),'owner'));
   await assertSucceeds(audited(owner,'clients','c2',client('b'),'owner'));
   await assertSucceeds(audited(owner,'clients','unassigned',client(''),'owner'));
   await assertFails(audited(owner,'clients','invalid',client('rec'),'owner'));
 });
 await check('agent sees only constrained assignment query; no other contacts or legacy sheet',async()=>{
   await assertSucceeds(getDocs(query(collection(a,'clients'),where('assignedTo','==','a'))));await assertFails(getDocs(collection(a,'clients')));
   await assertFails(getDoc(doc(a,'clients/c2')));await assertFails(getDoc(doc(a,'clients/unassigned')));await assertFails(getDocs(collection(a,'recruitment')));await assertFails(getDocs(collection(a,'recruitmentSources')));
 });
 await check('agent changes status and notes but cannot assign, classify, edit PII or promote',async()=>{
   let c=(await getDoc(doc(a,'clients/c1'))).data();await assertSucceeds(audited(a,'clients','c1',{...c,status:'Contactado',note:'Agente A'},'a'));
   c=(await getDoc(doc(a,'clients/c1'))).data();
   for(const extra of [{assignedTo:'b'},{classification:'B_LEAD'},{phone:'+15550000999'},{status:'INVALID'},{note:'x'.repeat(4001)}])await assertFails(audited(a,'clients','c1',{...c,...extra},'a'));
   await assertFails(audited(a,'users','a',{...(await getDoc(doc(a,'users/a'))).data(),role:'owner'},'a'));
 });
 await check('forged history, stale revision, missing event and delete denied',async()=>{
   const c=(await getDoc(doc(a,'clients/c1'))).data();await assertFails(audited(a,'clients','c1',c,'a',1));await assertFails(audited(a,'clients','c1',c,'a',undefined,{}));
   await assertFails(updateDoc(doc(a,'clients/c1'),{note:'Sin evento'}));
   const history=await getDocs(collection(a,'clients/c1/audit'));assert.equal(history.size,2);
   await assertFails(updateDoc(history.docs[0].ref,{actorUid:'b'}));await assertFails(deleteDoc(history.docs[0].ref));await assertFails(deleteDoc(doc(owner,'clients/c1')));
 });
 await check('reassignment removes old agent, preserves notes and history for new assignee',async()=>{
   const c=(await getDoc(doc(owner,'clients/c1'))).data();await assertSucceeds(audited(owner,'clients','c1',{...c,assignedTo:'b',classification:'B_LEAD'},'owner'));
   await assertFails(getDoc(doc(a,'clients/c1')));await assertFails(getDocs(collection(a,'clients/c1/audit')));
   const current=await getDoc(doc(b,'clients/c1'));assert.equal(current.data().note,'Agente A');assert.equal((await getDocs(collection(b,'clients/c1/audit'))).size,3);
 });
 await check('recruitment assignment never grants full source access; FE-only cannot be assigned',async()=>{
   await assertSucceeds(audited(owner,'recruitmentAssignments',rid,contact('a'),'owner'));
   await assertFails(audited(owner,'recruitmentAssignments','r_22222222-2222-4222-8222-222222222222',contact('fe'),'owner'));
   await assertSucceeds(getDocs(query(collection(a,'recruitmentAssignments'),where('assignedTo','==','a'))));await assertFails(getDocs(collection(a,'recruitmentAssignments')));await assertFails(getDoc(doc(fe,`recruitmentAssignments/${rid}`)));
 });
 await check('assigned recruitment edits share owner state and immutable activity',async()=>{
   await assertSucceeds(recEdit(a,'a',rid));const state=await getDoc(doc(owner,`recruitmentState/${rid}`));assert.equal(state.data().status,'Contactado');
   await assertFails(recEdit(a,'a',rid,'Cita','import'));await assertFails(updateDoc(doc(a,`recruitmentState/${rid}`),{status:'Cita'}));
   await assertSucceeds(recEdit(owner,'owner',rid,'Seguimiento'));assert.equal((await getDoc(doc(a,`recruitmentState/${rid}`))).data().status,'Seguimiento');
 });
 await check('scope withdrawal applies immediately to existing sessions',async()=>{
   let p=(await getDoc(doc(owner,'users/a'))).data();await audited(owner,'users','a',{...p,scopes:{clients:true,recruitment:false}},'owner');
   await assertFails(getDoc(doc(a,`recruitmentAssignments/${rid}`)));await assertFails(getDoc(doc(a,`recruitmentState/${rid}`)));await assertFails(getDocs(collection(a,`recruitmentState/${rid}/activity`)));
   await audited(owner,'users','a',{...p,scopes:{clients:true,recruitment:true}},'owner');await assertSucceeds(getDoc(doc(a,`recruitmentState/${rid}`)));
 });
 await check('suspension denies reads, edits and device registrations with old session',async()=>{
   const p=(await getDoc(doc(owner,'users/b'))).data();await audited(owner,'users','b',{...p,suspended:true},'owner');
   await assertFails(getDoc(doc(b,'clients/c1')));await assertFails(getDocs(query(collection(b,'clients'),where('assignedTo','==','b'))));
   await assertFails(setDoc(doc(b,'users/b/deviceRequests/test_device_12345678'),{fcmToken:'testtoken12345678901234567890',platform:'android',appVersion:'1.9',updatedAt:serverTimestamp()}));
   await assertSucceeds(getDoc(doc(b,'users/b')));await assertFails(audited(owner,'clients','badSuspended',client('b'),'owner'));
 });
 await check('changing email or unverified identity does not retain agent authorization',async()=>{await assertFails(getDoc(doc(db('a',true,email('b')),`recruitmentAssignments/${rid}`)));await assertFails(getDoc(doc(db('a',false),`recruitmentAssignments/${rid}`)));});
 await check('return recruitment to owner inventory removes agent history access',async()=>{
   const d=(await getDoc(doc(owner,`recruitmentAssignments/${rid}`))).data();await audited(owner,'recruitmentAssignments',rid,{...d,assignedTo:''},'owner');
   await assertFails(getDoc(doc(a,`recruitmentState/${rid}`)));await assertFails(getDocs(collection(a,`recruitmentAssignments/${rid}/audit`)));await assertSucceeds(getDocs(collection(owner,`recruitmentState/${rid}/activity`)));
 });
 await check('assignment queue requires a real atomic reassignment; agents cannot send',async()=>{
   const ref=doc(owner,'clients/unassigned'),old=(await getDoc(ref)).data(),eid=eventId();
   const after={...old,assignedTo:'a',revision:old.revision+1,lastEventId:eid,updatedBy:'owner',updatedAt:serverTimestamp()};
   const notice={bucket:'clients',recordId:'unassigned',targetUid:'a',state:'pending',createdAt:serverTimestamp()};
   await assertFails(setDoc(doc(owner,`assignmentNotices/${eid}`),notice));
   const batch=writeBatch(owner);batch.set(ref,after);batch.set(doc(owner,`clients/unassigned/audit/${eid}`),{before:old,after,actorUid:'owner',createdAt:serverTimestamp()});batch.set(doc(owner,`assignmentNotices/${eid}`),notice);await assertSucceeds(batch.commit());
   await assertFails(getDoc(doc(a,`assignmentNotices/${eid}`)));await assertFails(setDoc(doc(a,`assignmentNotices/${eventId()}`),notice));
   await assertFails(updateDoc(doc(owner,`assignmentNotices/${eid}`),{state:'accepted'}));
 });
 await check('only owner can approve a requested agent device with immutable audit',async()=>{
   const id='agent_test_phone_1234567890';await setDoc(doc(a,`users/a/deviceRequests/${id}`),{fcmToken:'synthetic_token_1234567890',platform:'android',appVersion:'1.9-QA2',updatedAt:serverTimestamp()});
   const d={userId:'a',deviceId:id,enabled:true,approvedTokenSha256:'a'.repeat(64)};
   await assertFails(setDoc(doc(a,`agentDevices/${id}`),d));await assertFails(setDoc(doc(owner,`agentDevices/${id}`),d));
   await assertSucceeds(audited(owner,'agentDevices',id,d,'owner'));await assertFails(getDoc(doc(a,`agentDevices/${id}`)));
   await assertSucceeds(audited(owner,'agentDevices',id,{...d,enabled:false},'owner'));
 });
 console.log(`AGENTS SECURITY: ${passed} scenario groups passed`);
}finally{await env.cleanup();}})().catch(e=>{console.error(e);process.exitCode=1;});
