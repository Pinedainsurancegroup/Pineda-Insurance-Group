const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const context={};vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/SparkAgentAssignments.gs','utf8'),context);
const valid=()=>[{bucket:'clients',targetUid:'agent1'},{role:'agent',active:true,suspended:false,scopes:{clients:true,recruitment:true}},{assignedTo:'agent1'},{userId:'agent1',enabled:true,approvedTokenSha256:'digest'},{platform:'android',fcmToken:'synthetic_token_1234567890'},{notifications:true},()=> 'digest'];
test('assignment notice requires current scoped agent, assignment, preferences and approved token',()=>{assert.equal(context.pagAgentDecision_(...valid()),'READY');});
test('revoked identity, section, reassignment and paused preference never send',()=>{
 for(const [index,change,expected] of [[1,{suspended:true},'NO_ACCESS'],[1,{active:false},'NO_ACCESS'],[1,{role:'owner'},'NO_ACCESS'],[1,{scopes:{clients:false}},'NO_ACCESS'],[2,{assignedTo:'another'},'REASSIGNED'],[5,{notifications:false},'DISABLED']]){const args=valid();args[index]={...args[index],...change};assert.equal(context.pagAgentDecision_(...args),expected);}
});
test('device and token renewal require owner approval; no fallback to another user',()=>{
 for(const [index,change,expected] of [[3,{enabled:false},'DEVICE_NOT_APPROVED'],[3,{userId:'other'},'DEVICE_NOT_APPROVED'],[3,{approvedTokenSha256:'old'},'TOKEN_CHANGED'],[4,{fcmToken:'short'},'TOKEN_CHANGED']]){const args=valid();args[index]={...args[index],...change};assert.equal(context.pagAgentDecision_(...args),expected);}
});
test('recruitment permission is independent of clients permission',()=>{const args=valid();args[0].bucket='recruitmentAssignments';args[1].scopes={clients:false,recruitment:true};assert.equal(context.pagAgentDecision_(...args),'READY');args[1].scopes.recruitment=false;assert.equal(context.pagAgentDecision_(...args),'NO_ACCESS');});
test('sender is disabled by default and does not query or send',()=>{const c={PropertiesService:{getScriptProperties:()=>({getProperty:()=>null})},pagPushWithLock_:()=>assert.fail('should remain dormant')};vm.createContext(c);vm.runInContext(fs.readFileSync(__dirname+'/SparkAgentAssignments.gs','utf8'),c);c.pagRunAgentAssignmentNotices();});
