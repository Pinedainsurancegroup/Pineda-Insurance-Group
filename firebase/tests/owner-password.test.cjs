// Synthetic identities/passwords only, restricted to the local Auth and Firestore emulators.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {initializeApp, deleteApp} = require('firebase/app');
const {getAuth, connectAuthEmulator, GoogleAuthProvider, EmailAuthProvider, signInWithCredential,
  linkWithCredential, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut} = require('firebase/auth');
const {getFirestore, connectFirestoreEmulator, doc, getDocFromServer, setDoc} = require('firebase/firestore');
const {initializeTestEnvironment, assertFails} = require('@firebase/rules-unit-testing');

(async () => {
  assert.equal(process.env.FIREBASE_AUTH_EMULATOR_HOST, '127.0.0.1:9099');
  const projectId = 'demo-pag-leads';
  const env = await initializeTestEnvironment({projectId, firestore:{host:'127.0.0.1',port:8085,
    rules:fs.readFileSync(path.join(__dirname,'../firestore.rules'),'utf8')}});
  const apps=[];
  function phone(name) {
    const app=initializeApp({projectId, apiKey:'fake-emulator-key',appId:'emulator-only'},name);apps.push(app);
    const auth=getAuth(app);connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});
    const db=getFirestore(app);connectFirestoreEmulator(db,'127.0.0.1',8085);
    return {auth,db};
  }
  try {
    const first=phone('google-phone'),second=phone('password-phone'),outsider=phone('unauthorized-phone');
    const email='owner-password-test@example.test', password='Synthetic-only-PAG-test-13!';
    const encoded=value=>Buffer.from(JSON.stringify(value)).toString('base64url');
    const now=Math.floor(Date.now()/1000);
    const googleToken=encoded({alg:'none',typ:'JWT'})+'.'+encoded({sub:'synthetic-owner-google',email,email_verified:true,
      iss:'https://accounts.google.com',aud:'fake-google-client',iat:now,exp:now+3600})+'.';
    const before=await signInWithCredential(first.auth,GoogleAuthProvider.credential(googleToken));
    const uid=before.user.uid;
    await env.withSecurityRulesDisabled(async c=>{
      await setDoc(doc(c.firestore(),'users',uid),{role:'owner',active:true,suspended:false});
      await setDoc(doc(c.firestore(),'recruitmentState','password-test-lead'),{status:'Contactado',note:'Conservar mi nota',revision:3});
      await setDoc(doc(c.firestore(),'recruitmentState','password-test-lead','activity','earlier'),{kind:'edit',note:'Historial previo'});
    });
    const linked=await linkWithCredential(before.user,EmailAuthProvider.credential(email,password));
    assert.equal(linked.user.uid,uid,'adding a password must preserve the Google UID');
    assert.equal(linked.user.emailVerified,true);
    assert.deepEqual(linked.user.providerData.map(p=>p.providerId).sort(),['google.com','password']);
    const manual=await signInWithEmailAndPassword(second.auth,email,password);
    assert.equal(manual.user.uid,uid,'both phones must identify the same account');
    assert.equal((await getDocFromServer(doc(second.db,'recruitmentState','password-test-lead'))).data().note,'Conservar mi nota');
    assert.equal((await getDocFromServer(doc(second.db,'recruitmentState','password-test-lead','activity','earlier'))).data().note,'Historial previo');
    await assert.rejects(signInWithEmailAndPassword(outsider.auth,email,'intentionally-wrong-password'));
    const unapproved=await createUserWithEmailAndPassword(outsider.auth,'unapproved@example.test',password);
    await assertFails(getDocFromServer(doc(outsider.db,'recruitmentState','password-test-lead')));
    await assertFails(setDoc(doc(outsider.db,'users',unapproved.user.uid),{role:'owner',active:true,suspended:false}));
    await env.withSecurityRulesDisabled(c=>setDoc(doc(c.firestore(),'users',uid),{role:'owner',active:false,suspended:true}));
    await assertFails(getDocFromServer(doc(second.db,'recruitmentState','password-test-lead')));
    await assertFails(getDocFromServer(doc(first.db,'recruitmentState','password-test-lead')));
    await signOut(first.auth);
    assert.equal((await signInWithCredential(first.auth,GoogleAuthProvider.credential(googleToken))).user.uid,uid,'Google remains linked');
    console.log('Owner password: same UID, metadata/history preserved, Google retained, unapproved and suspended access denied.');
  } finally {
    await Promise.all(apps.map(deleteApp));await env.cleanup();
  }
})().catch(error=>{console.error(error);process.exit(1)});
