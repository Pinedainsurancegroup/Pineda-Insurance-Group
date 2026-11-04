const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const file=process.env.PAG_RULES_FILE ? path.resolve(process.env.PAG_RULES_FILE) : path.join(__dirname,'../firestore.rules');
const rules=fs.readFileSync(file,'utf8');
console.log('Rules loaded for emulator:',path.basename(file),'sha256='+crypto.createHash('sha256').update(rules).digest('hex'));
module.exports=rules;
