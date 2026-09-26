const fs=require('fs'), path=require('path'), assert=require('node:assert/strict');
const {initializeTestEnvironment,assertSucceeds,assertFails}=require('@firebase/rules-unit-testing');
const {doc,getDoc,getDocs,collection,setDoc,updateDoc,deleteDoc,writeBatch,runTransaction,serverTimestamp,onSnapshot}=require('firebase/firestore');
(async()=>{
 const env=await initializeTestEnvironment({projectId:'demo-pag-leads',firestore:{host:'127.0.0.1',port:8085,rules:fs.readFileSync(path.join(__dirname,'../firestore.rules'),'utf8')}});
 await env.clearFirestore();
 const one='r_11111111-1111-4111-8111-111111111111',two='r_22222222-2222-4222-8222-222222222222',unknown='r_33333333-3333-4333-8333-333333333333';
 const owner=env.authenticatedContext('juan').firestore(), phone2=env.authenticatedContext('juan').firestore();
 const state=(d,id=one)=>doc(d,'recruitmentState',id), event=(d,id,e)=>doc(d,'recruitmentState',id,'activity',e);
 const empty={status:'Nuevo',note:'',revision:0};
 function fields(old,status,note,id,kind='edit'){
  const apply=kind!=='backup',revision=old.revision+(apply?1:0);
  return {current:{status,note,revision,lastEventId:id,updatedBy:'juan',updatedAt:serverTimestamp()},
   event:{actorUid:'juan',deviceId:'synthetic-device-1234',kind,status,note,previousStatus:old.status,previousNote:old.note,
    baseRevision:old.revision,revision,createdAt:serverTimestamp(),originalUpdatedAt:kind==='edit'?'':'2026-09-26T08:00:00Z'}};
 }
 async function save(db,id,op,expected,status,note,importing=false){
  return runTransaction(db,async tx=>{
   const ev=await tx.get(event(db,id,op)),s=await tx.get(state(db,id)),old=s.exists()?s.data():empty;
   if(ev.exists())return 'duplicate';
   if(!importing&&old.revision!==expected)return 'conflict';
   const kind=importing?(s.exists()?'backup':'import'):'edit',f=fields(old,status,note,op,kind);
   tx.set(event(db,id,op),f.event);if(kind!=='backup')tx.set(state(db,id),f.current);return kind;
  });
 }
 try{
  await env.withSecurityRulesDisabled(async c=>{
   for(const [uid,role] of [['juan','owner'],['agent','agent'],['leader','leader']])await setDoc(doc(c.firestore(),'users',uid),{role,active:true,suspended:false,authorizedTeamIds:['team1']});
   for(const id of [one,two])await setDoc(doc(c.firestore(),'recruitmentSources',id),{enabled:true});
  });
  for(const db of [env.unauthenticatedContext().firestore(),env.authenticatedContext('agent').firestore(),env.authenticatedContext('leader').firestore()]){
   await assertFails(getDoc(state(db)));await assertFails(getDocs(collection(db,'recruitmentState')));
   await assertFails(getDoc(doc(db,'recruitmentSources',one)));
   await assertFails(setDoc(state(db),fields(empty,'Contactado','private','event-isolated-01000').current));
  }
  await assertFails(setDoc(doc(owner,'recruitmentSources',unknown),{enabled:true}));
  await assertFails(setDoc(state(owner),fields(empty,'Contactado','private','event-isolated-01000').current));
  await assertFails(save(owner,unknown,'event-unknown-010000',0,'Contactado','private'));
  await assertSucceeds(save(owner,one,'event-initial-010000',0,'Contactado','Nota A'));
  assert.equal((await getDoc(state(phone2))).data().note,'Nota A');
  const observed=new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>{unsubscribe();reject(Error('Live listener timeout'))},15000);
   const unsubscribe=onSnapshot(state(phone2),{includeMetadataChanges:true},snap=>{
    if(snap.exists()&&!snap.metadata.hasPendingWrites&&!snap.metadata.fromCache&&snap.data().note==='Nota B'){clearTimeout(timer);unsubscribe();resolve()}
   },reject);
  });
  await assertSucceeds(save(owner,one,'event-second-0010000',1,'Seguimiento','Nota B'));await observed;
  assert.equal(await save(phone2,one,'event-stale-00010000',1,'Cita','Older edit'),'conflict');
  assert.equal((await getDoc(state(owner))).data().note,'Nota B');
  assert.equal(await save(phone2,one,'event-local-00100000',0,'Nuevo','Nota local antigua',true),'backup');
  assert.equal((await getDoc(state(owner))).data().note,'Nota B');
  assert.equal(await save(phone2,one,'event-local-00100000',0,'Nuevo','Nota local antigua',true),'duplicate');
  assert.equal((await getDocs(collection(owner,'recruitmentState',one,'activity'))).size,3);
  await assertSucceeds(save(owner,two,'event-import-0100000',0,'Cita','Otra nota',true));
  assert.equal((await getDoc(state(owner,two))).data().note,'Otra nota');
  const latest=(await getDoc(state(owner))).data(),f=fields(latest,'Completado','x','event-forged-0100000');
  for(const mutation of [x=>{x.current.revision++},x=>{x.event.actorUid='agent'},x=>{x.event.previousNote='forged'},x=>{x.current.role='owner'},x=>{x.current.note='x'.repeat(4001);x.event.note=x.current.note},x=>{x.event.note='different'}]){
   const broken=fields(latest,'Completado','x','event-forged-0100000');mutation(broken);
   const b=writeBatch(owner);b.set(state(owner),broken.current);b.set(event(owner,one,'event-forged-0100000'),broken.event);await assertFails(b.commit());
  }
  await assertFails(updateDoc(event(owner,one,'event-initial-010000'),{note:'erased'}));
  await assertFails(deleteDoc(event(owner,one,'event-initial-010000')));await assertFails(deleteDoc(state(owner)));
  await env.withSecurityRulesDisabled(c=>updateDoc(doc(c.firestore(),'users/juan'),{suspended:true}));
  await assertFails(getDoc(state(phone2)));await assertFails(getDocs(collection(phone2,'recruitmentState',one,'activity')));
  await assertFails(save(owner,one,'event-suspended10000',2,'Cita','denied'));
  console.log('PASS owner-only sync, two sessions/live listener, CAS, append-only history, idempotent import/backup, source registry and suspended old sessions');
 }finally{await env.cleanup()}
})().catch(e=>{console.error(e);process.exitCode=1});
