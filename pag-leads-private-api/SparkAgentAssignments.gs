// Add to the existing PRIVATE Spark sender project. No web endpoint or private key.
// Dormant until explicit deployment + AGENT_ASSIGNMENT_PUSH_ENABLED=true.
function pagAgentDecode_(v) {
  if (!v) return null;
  if ('stringValue' in v) return v.stringValue;
  if ('booleanValue' in v) return v.booleanValue;
  if ('integerValue' in v) return Number(v.integerValue);
  if ('timestampValue' in v) return v.timestampValue;
  if (v.mapValue) return pagAgentFields_(v.mapValue.fields || {});
  return null;
}
function pagAgentFields_(fields) {
  return Object.fromEntries(Object.keys(fields).map(k => [k, pagAgentDecode_(fields[k])]));
}
function pagAgentRead_(c, path) {
  const d = pagPushFirestore_(c, path);
  return d ? pagAgentFields_(d.fields || {}) : null;
}
function pagAgentQuery_(c, collection, field, value, limit) {
  const response = UrlFetchApp.fetch('https://firestore.googleapis.com/v1/projects/' + c.project +
    '/databases/(default)/documents:runQuery', {
      method:'post', contentType:'application/json', muteHttpExceptions:true,
      headers:{Authorization:'Bearer ' + ScriptApp.getOAuthToken()},
      payload:JSON.stringify({structuredQuery:{from:[{collectionId:collection}],
        where:{fieldFilter:{field:{fieldPath:field},op:'EQUAL',value:{stringValue:value}}},limit}})
    });
  if (response.getResponseCode() !== 200) throw new Error('PAG_AGENT_QUERY');
  return JSON.parse(response.getContentText()).filter(x=>x.document).map(x=>({
    id:x.document.name.split('/').pop(), ...pagAgentFields_(x.document.fields || {})}));
}
function pagAgentDecision_(notice, profile, lead, device, request, preference, hash) {
  const module = notice.bucket === 'clients' ? 'clients' : notice.bucket === 'recruitmentAssignments' ? 'recruitment' : null;
  if (!module || !profile || profile.role !== 'agent' || profile.active !== true || profile.suspended !== false ||
      !profile.scopes || profile.scopes[module] !== true) return 'NO_ACCESS';
  if (!lead || lead.assignedTo !== notice.targetUid) return 'REASSIGNED';
  if (preference && preference.notifications === false) return 'DISABLED';
  if (!device || device.userId !== notice.targetUid || device.enabled !== true) return 'DEVICE_NOT_APPROVED';
  if (!request || request.platform !== 'android' || typeof request.fcmToken !== 'string' ||
      request.fcmToken.length < 20 || request.fcmToken.length > 4096 || hash(request.fcmToken) !== device.approvedTokenSha256)
    return 'TOKEN_CHANGED';
  return 'READY';
}
function pagAgentMark_(c,id,state) {
  pagPushFirestore_(c,'assignmentNotices/'+id,'patch',{fields:{state:{stringValue:state},
    checkedAt:{timestampValue:new Date().toISOString()}}},'?updateMask.fieldPaths=state&updateMask.fieldPaths=checkedAt');
}
function pagRunAgentAssignmentNotices() {
  const p=PropertiesService.getScriptProperties();
  if(p.getProperty('AGENT_ASSIGNMENT_PUSH_ENABLED')!=='true')return;
  pagPushWithLock_(()=>{
    const c=pagPushConfig_();if(!c.enabled||!pagPushOwner_(c))return;
    const day=Utilities.formatDate(new Date(),'America/Los_Angeles','yyyy-MM-dd'),capKey='AGENT_PUSH_CAP_'+day;
    let sent=Number(p.getProperty(capKey)||0);
    const notices=pagAgentQuery_(c,'assignmentNotices','state','pending',25);
    for(const notice of notices){
      if(sent>=100)return;
      if(!/^[A-Za-z0-9_-]{16,80}$/.test(notice.id)||!['clients','recruitmentAssignments'].includes(notice.bucket)||
        !/^[A-Za-z0-9_-]{1,128}$/.test(notice.targetUid)||! /^[A-Za-z0-9_-]{1,128}$/.test(notice.recordId)) continue;
      const created=Date.parse(notice.createdAt);if(!Number.isFinite(created)||Date.now()-created>7*86400000){pagAgentMark_(c,notice.id,'expired');continue;}
      const audit=pagAgentRead_(c,notice.bucket+'/'+notice.recordId+'/audit/'+notice.id);
      if(!audit||!audit.after||audit.after.assignedTo!==notice.targetUid||audit.actorUid!==c.owner){pagAgentMark_(c,notice.id,'invalid');continue;}
      const devices=pagAgentQuery_(c,'agentDevices','userId',notice.targetUid,20);
      let pending=false,any=false;
      for(const device of devices){
        if(sent>=100)return;
        if(!/^[A-Za-z0-9_-]{16,80}$/.test(device.deviceId||''))continue;
        // Fresh permissions, assignment, preference and token on every attempt.
        if(!pagPushOwner_(c))return;
        const profile=pagAgentRead_(c,'users/'+notice.targetUid),lead=pagAgentRead_(c,notice.bucket+'/'+notice.recordId);
        const request=pagAgentRead_(c,'users/'+notice.targetUid+'/deviceRequests/'+device.deviceId);
        const pref=pagAgentRead_(c,'users/'+notice.targetUid+'/preferences/operational');
        const decision=pagAgentDecision_(notice,profile,lead,device,request,pref,pagPushHash_);
        if(decision!=='READY')continue;
        const path='assignmentNotices/'+notice.id+'/deliveries/'+device.deviceId;
        if(pagAgentRead_(c,path)){any=true;continue;}
        // Charge the attempt before sending, including ambiguous/transient responses.
        p.setProperty(capKey,String(++sent));
        const result=pagPushSend_(c,{token:request.fcmToken,kind:'assignment'},notice.id,false);
        if(result==='ACCEPTED'){
          pagPushFirestore_(c,path,'patch',{fields:{acceptedAt:{timestampValue:new Date().toISOString()}}},'?currentDocument.exists=false');any=true;
        }else pending=true;
      }
      if(!pending&&any)pagAgentMark_(c,notice.id,'accepted');
      if(!pending&&!any)pagAgentMark_(c,notice.id,'skipped_policy_or_device');
      // No retroactive send after missing approval: the next assignment produces a new notice.
    }
  });
}
function pagInstallAgentAssignmentTrigger() {
  if(PropertiesService.getScriptProperties().getProperty('AGENT_ASSIGNMENT_PUSH_ENABLED')!=='true')throw new Error('PAG_AGENT_NOT_ENABLED');
  const c=pagPushConfig_();if(!pagPushOwner_(c))throw new Error('PAG_OWNER_INACTIVE');
  if(!ScriptApp.getProjectTriggers().some(t=>t.getHandlerFunction()==='pagRunAgentAssignmentNotices'))
    ScriptApp.newTrigger('pagRunAgentAssignmentNotices').timeBased().everyMinutes(1).create();
}
