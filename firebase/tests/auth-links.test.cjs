// Real Auth Emulator only. No external email, real account or production credentials.
const assert=require('node:assert/strict');
const {signInWithEmailLink}=require('firebase/auth');
const {phone,loginByLink}=require('./auth-links-local.cjs');
(async()=>{const a=phone('email-link-alone'),b=phone('email-link-replay');try{
 const email='link-qa@example.test';const {user,link}=await loginByLink(a,email);
 assert.equal(user.email,email);
 await assert.rejects(signInWithEmailLink(b.auth,email,link));
 console.log('PASS Auth Emulator: verified email identity and consumed-link replay rejected. Android App Links not exercised.');
}finally{await a.close();await b.close();}})().catch(e=>{console.error('FAIL Auth Emulator:',e.code||e.name);process.exitCode=1;});
