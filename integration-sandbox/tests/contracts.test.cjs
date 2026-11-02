'use strict';
// Synthetic contract scenarios. No service SDK, network adapter or send function.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {evaluatePilotSafety,planDeliveryReconciliation}=require('../vendor/integration-controls.cjs');
const now=1700000000000;
function fixture(){
 const destination={locationId:'test-tenant',contactId:'test-contact',from:'+12025550101',to:'+12025550102',channel:'whatsapp'};
 const state={locationId:destination.locationId,contactId:destination.contactId,revision:1,observedAt:now,paused:false,optedOut:false};
 return {destination,crm:{...state},receiver:{...state},policy:{enabled:true,transport:'highlevel',singleResponderVerified:true,pausePropagationVerified:true,allowlist:[{...destination}]},draft:{crmRevision:1,receiverRevision:1,inboundAt:now-1000,replyToId:'test-inbound',latestInboundId:'test-inbound',dnd:false}};
}
test('AI proposal never grants send authority even with eligible synthetic controls',()=>{
 const f=fixture();
 const proposal={text:'Synthetic response',requestedTool:'send_whatsapp',sendAuthorized:true};
 const decision=evaluatePilotSafety(f,now);
 assert.equal(decision.decision,'eligible-for-locked-recheck');
 assert.equal(decision.sendAuthorized,false);
 // Model output is not an input to the safety contract.
 assert.equal(proposal.requestedTool,'send_whatsapp');
 assert.equal(decision.requiresAtomicRecheck,true);
});
test('STOP received after proposal blocks execution planning',()=>{
 const f=fixture();assert.equal(evaluatePilotSafety(f,now).decision,'eligible-for-locked-recheck');
 f.receiver.optedOut=true;f.receiver.revision++;
 const result=evaluatePilotSafety(f,now);assert.equal(result.reason,'opted-out');assert.equal(result.sendAuthorized,false);
});
test('human pause and stale account state block pending proposals',()=>{
 const f=fixture();f.crm.paused=true;assert.equal(evaluatePilotSafety(f,now).reason,'human-pause');
 f.crm.paused=false;f.crm.observedAt=now-5001;
 assert.equal(evaluatePilotSafety(f,now).decision,'blocked');
});
test('receiver evidence cannot be reused across tenant or contact',()=>{
 for(const key of ['locationId','contactId']){
  const f=fixture();f.receiver[key]='other-identity';assert.equal(evaluatePilotSafety(f,now).decision,'blocked');
 }
});
test('a later inbound supersedes the AI draft and repeated checks do not authorize sends',()=>{
 const f=fixture();f.draft.latestInboundId='new-inbound';
 for(let i=0;i<3;i++)assert.equal(evaluatePilotSafety(f,now).reason,'superseded-inbound');
});
test('delivery reconciliation never resends, including replayed and mismatched evidence',()=>{
 const f=fixture();
 const local={destination:f.destination,messageId:'test-message',conversationId:'test-conversation',bodySha256:'a'.repeat(64),status:'sent',revision:1};
 const provider={...local,status:'delivered',direction:'outbound',observedAt:now,providerUpdatedAt:now};
 const result=planDeliveryReconciliation(local,provider,now);
 assert.equal(result.action,'reconcile-local-only');assert.equal(result.resend,false);
 assert.equal(planDeliveryReconciliation({...local,status:'delivered'},provider,now).action,'keep');
 assert.equal(planDeliveryReconciliation(local,{...provider,messageId:'different'},now).resend,false);
});
