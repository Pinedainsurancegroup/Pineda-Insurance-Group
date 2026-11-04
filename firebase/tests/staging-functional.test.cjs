// Real Auth+Firestore emulators, candidate actually supplied to initializeTestEnvironment.
const assert=require('node:assert/strict');
const {initializeTestEnvironment,assertFails}=require('@firebase/rules-unit-testing');
const {getFirestore,connectFirestoreEmulator,doc,getDoc,getDocs,collection,query,where,runTransaction,serverTimestamp,updateDoc,setDoc}=require('firebase/firestore');
const {phone,loginByLink,projectId}=require('./auth-links-local.cjs');
const {randomUUID}=require('node:crypto');
const rules=require('./rules-under-test.cjs');
const scopes={clients:true,recruitment:false};
async function save(db,actor,bucket,id,values){
 const ref=doc(db,bucket,id),eventId=randomUUID();
 return runTransaction(db,async tx=>{
  const before=await tx.get(ref);const old=before.exists()?before.data():{};
  const after={...values,revision:(old.revision||0)+1,lastEventId:eventId,updatedBy:actor,updatedAt:serverTimestamp()};
  tx.set(ref,after);tx.set(doc(db,`${bucket}/${id}/audit/${eventId}`),{before:old,after,actorUid:actor,createdAt:serverTimestamp()});
  if(['clients','recruitmentAssignments'].includes(bucket)&&after.assignedTo&&old.assignedTo!==after.assignedTo)
   tx.set(doc(db,'assignmentNotices',eventId),{bucket,recordId:id,targetUid:after.assignedTo,state:'pending',createdAt:serverTimestamp()});
 });
}
(async()=>{
 assert.equal(process.env.FIRESTORE_EMULATOR_HOST,'127.0.0.1:8085');
 const env=await initializeTestEnvironment({projectId,firestore:{host:'127.0.0.1',port:8085,rules}});
 const phones=[];
 try{
  await env.clearFirestore();
  async function identity(label){const p=phone(label);phones.push(p);const {user}=await loginByLink(p,label+'@example.test');const db=getFirestore(p.app);connectFirestoreEmulator(db,'127.0.0.1',8085);return {user,db};}
  const owner=await identity('qa-owner'),agent=await identity('qa-agent'),other=await identity('qa-unapproved');
  const ownerProfile={role:'owner',active:true,suspended:false};
  await env.withSecurityRulesDisabled(c=>setDoc(doc(c.firestore(),'users',owner.user.uid),ownerProfile));
  const email=agent.user.email;
  await save(owner.db,owner.user.uid,'agentInvitations',email,{email,name:'Synthetic agent',scopes,active:true,claimedUid:'',claimedAt:null});
  console.log('PASS owner invitation transaction + immutable audit');
  // Mirrors EmailInvitationAccess.redeem: all reads precede atomic profile/request/claim/audit writes.
  const eventId=randomUUID();await runTransaction(agent.db,async tx=>{
   const invite=doc(agent.db,'agentInvitations',email),profile=doc(agent.db,'users',agent.user.uid),req=doc(agent.db,'accessRequests',agent.user.uid);
   const i=await tx.get(invite),p=await tx.get(profile),r=await tx.get(req);
   assert.equal(p.exists(),false);assert.equal(i.data().claimedUid,'');
   const after={role:'agent',active:true,suspended:false,email,name:i.data().name,scopes:i.data().scopes,revision:1,lastEventId:eventId,updatedBy:agent.user.uid,updatedAt:serverTimestamp()};
   if(!r.exists())tx.set(req,{email,name:i.data().name,createdAt:serverTimestamp()});
   tx.set(profile,after);tx.set(doc(agent.db,`users/${agent.user.uid}/audit/${eventId}`),{before:{},after,actorUid:agent.user.uid,createdAt:serverTimestamp()});
   tx.update(invite,{claimedUid:agent.user.uid,claimedAt:serverTimestamp()});
  });
  assert.equal((await getDoc(doc(agent.db,'users',agent.user.uid))).data().role,'agent');
  console.log('PASS invited verified Auth identity redeems atomically and reads profile');
  const contact={name:'Synthetic prospect',phone:'',email:'prospect@example.test',region:'QA',assignedTo:'',classification:'LEAD',status:'Nuevo',note:''};
  await save(owner.db,owner.user.uid,'clients','qa-contact',contact);
  await save(owner.db,owner.user.uid,'clients','qa-other',contact);
  await save(owner.db,owner.user.uid,'clients','qa-contact',{...contact,assignedTo:agent.user.uid});
  const visible=await getDocs(query(collection(agent.db,'clients'),where('assignedTo','==',agent.user.uid)));assert.equal(visible.size,1);
  await assertFails(getDoc(doc(agent.db,'clients','qa-other')));
  await assertFails(getDocs(collection(agent.db,'clients')));
  await assertFails(getDocs(query(collection(agent.db,'recruitmentAssignments'),where('assignedTo','==',agent.user.uid))));
  await assertFails(updateDoc(doc(agent.db,'users',agent.user.uid),{role:'owner'}));
  await assertFails(save(agent.db,agent.user.uid,'clients','qa-contact',{...contact,assignedTo:other.user.uid}));
  await assertFails(getDocs(collection(other.db,'clients')));
  console.log('PASS assignment, module restrictions, foreign contacts, role/assignment escalation rejected');
  const p=(await getDoc(doc(owner.db,'users',agent.user.uid))).data();
  await save(owner.db,owner.user.uid,'users',agent.user.uid,{...p,suspended:true});
  await assertFails(getDoc(doc(agent.db,'clients','qa-contact')));
  await assertFails(save(agent.db,agent.user.uid,'clients','qa-contact',{...contact,assignedTo:agent.user.uid,note:'forbidden'}));
  assert.deepEqual((await getDoc(doc(owner.db,'users',owner.user.uid))).data(),ownerProfile);
  console.log('PASS suspended agent denied; owner profile unchanged');
 }finally{for(const p of phones)await p.close();await env.cleanup();}
})().catch(e=>{console.error('FAIL functional emulator:',e.code||e.name);process.exitCode=1;});
