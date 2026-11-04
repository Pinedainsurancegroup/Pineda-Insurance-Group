const assert=require('node:assert/strict');
const {initializeApp,deleteApp}=require('firebase/app');
const {getAuth,connectAuthEmulator,sendSignInLinkToEmail,signInWithEmailLink}=require('firebase/auth');
const projectId='demo-pag-leads';
function phone(name){
 assert.equal(process.env.FIREBASE_AUTH_EMULATOR_HOST,'127.0.0.1:9099');
 const app=initializeApp({projectId,apiKey:'emulator-only',appId:'emulator-only'},name);
 const auth=getAuth(app);connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});
 return {app,auth,close:()=>deleteApp(app)};
}
async function loginByLink(p,email){
 await sendSignInLinkToEmail(p.auth,email,{url:'http://127.0.0.1/qa',handleCodeInApp:true,android:{packageName:'com.pinedaagencygroup.leads.staging',installApp:false}});
 const r=await fetch(`http://127.0.0.1:9099/emulator/v1/projects/${projectId}/oobCodes`);
 assert.equal(r.status,200);
 const {oobCodes=[]}=await r.json();const code=oobCodes.filter(c=>c.email===email&&c.requestType==='EMAIL_SIGNIN').at(-1);
 assert.ok(code);const result=await signInWithEmailLink(p.auth,email,code.oobLink);
 assert.equal(result.user.emailVerified,true);return {user:result.user,link:code.oobLink};
}
module.exports={phone,loginByLink,projectId};
