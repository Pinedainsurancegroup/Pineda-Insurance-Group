#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
rm -f staging/work-functional/candidate-validation.json
export PAG_RULES_FILE="$PWD/staging/work-functional/firestore.candidate.rules"
sha256sum -c staging/work-functional/SHA256SUMS
./node_modules/.bin/firebase emulators:exec --only auth,firestore --project demo-pag-leads --config staging/work-functional/firebase.emulators.json 'node tests/rules.test.cjs && node tests/recruitment-sync.test.cjs && node tests/owner-password.test.cjs && node tests/agents.test.cjs && node tests/invitations.test.cjs && node tests/auth-links.test.cjs && node tests/staging-functional.test.cjs'
node - <<'JS'
const fs=require('node:fs'),crypto=require('node:crypto');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const tests=fs.readdirSync('tests').filter(x=>x.endsWith('.cjs')).sort().map(x=>({file:'tests/'+x,sha256:sha('tests/'+x)}));
fs.writeFileSync('staging/work-functional/candidate-validation.json',JSON.stringify({status:'PASS',project:'demo-pag-leads',candidateSHA256:sha(process.env.PAG_RULES_FILE),tests,completedAt:new Date().toISOString()},null,2)+'\n');
JS
