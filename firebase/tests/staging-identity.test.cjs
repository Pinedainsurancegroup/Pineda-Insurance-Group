'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {initializeTestEnvironment,assertSucceeds,assertFails}=require('@firebase/rules-unit-testing');
const {doc,getDoc,getDocs,collection,setDoc,deleteDoc}=require('firebase/firestore');
(async()=>{
 const env=await initializeTestEnvironment({projectId:'demo-pag-leads',firestore:{host:'127.0.0.1',port:8085,rules:fs.readFileSync(path.join(__dirname,'../staging/firestore.identity-smoke.rules'),'utf8')}});
 let passed=0;
 const check=async(name,fn)=>{await fn();passed++;console.log('PASS '+name)};
 try{
  await env.clearFirestore();
  await env.withSecurityRulesDisabled(async c=>{
   for(const uid of ['test-a','test-b','test-disabled','test-wrong-project']){
    await setDoc(doc(c.firestore(),'users/'+uid),{name:'Fixture',role:'agent',active:true});
    await setDoc(doc(c.firestore(),'stagingTestUsers/'+uid),{enabled:uid!=='test-disabled',environment:uid==='test-wrong-project'?'different':'pag-leads-staging'});
   }
  });
  const db=(uid,verified=true)=>env.authenticatedContext(uid,{email_verified:verified}).firestore();
  const a=db('test-a');
  await check('approved verified fixture reads own profile',()=>assertSucceeds(getDoc(doc(a,'users/test-a'))));
  await check('cross-user read denied',()=>assertFails(getDoc(doc(a,'users/test-b'))));
  await check('unapproved user denied',()=>assertFails(getDoc(doc(db('unknown'),'users/unknown'))));
  await check('disabled fixture denied',()=>assertFails(getDoc(doc(db('test-disabled'),'users/test-disabled'))));
  await check('wrong-project fixture denied',()=>assertFails(getDoc(doc(db('test-wrong-project'),'users/test-wrong-project'))));
  await check('unverified denied',()=>assertFails(getDoc(doc(db('test-a',false),'users/test-a'))));
  await check('anonymous denied',()=>assertFails(getDoc(doc(env.unauthenticatedContext().firestore(),'users/test-a'))));
  await check('user list denied',()=>assertFails(getDocs(collection(a,'users'))));
  await check('self role escalation denied',()=>assertFails(setDoc(doc(a,'users/test-a'),{role:'owner'})));
  await check('self enrollment denied',()=>assertFails(setDoc(doc(a,'stagingTestUsers/test-a'),{enabled:true,environment:'pag-leads-staging'})));
  await check('delete profile denied',()=>assertFails(deleteDoc(doc(a,'users/test-a'))));
  await check('lead data denied',()=>assertFails(getDoc(doc(a,'clients/test-record'))));
  assert.equal(passed,12);console.log('Staging identity smoke rules: '+passed+' checks executed');
 }finally{await env.cleanup()}
})().catch(()=>{console.error('Staging identity rule tests failed; no remote fallback is permitted');process.exitCode=1});
