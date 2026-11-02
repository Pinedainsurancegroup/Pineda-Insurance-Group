import importlib.util,json,pathlib,tempfile,unittest,hashlib
spec=importlib.util.spec_from_file_location('bundle',pathlib.Path(__file__).parents[1]/'prepare_firebase_staging.py')
bundle=importlib.util.module_from_spec(spec);spec.loader.exec_module(bundle)
class BundleTests(unittest.TestCase):
    def test_known_project_and_invalid_names_rejected_without_files(self):
        for project in ['pag-leads-8c6ef','','../other','UPPERCASE']:
            with self.assertRaises(ValueError):bundle.validate_project(project)
    def test_local_bundle_has_no_credentials_or_sending_components(self):
        # Local test identifier only: no Firebase account/key/token is created or used.
        with tempfile.TemporaryDirectory() as tmp:
            output=pathlib.Path(tmp)/'bundle';m=bundle.generate('demo-local-review',output)
            config=json.loads((output/'firebase.json').read_text())
            self.assertNotIn('functions',config)
            self.assertEqual(config['firestore']['rules'],'firestore.bootstrap.rules')
            self.assertIn('allow read, write: if false;', (output/'firestore.bootstrap.rules').read_text())
            original=(bundle.ROOT/'firebase/firestore.rules').read_bytes()
            self.assertEqual((output/'firestore.candidate.rules').read_bytes(),original)
            self.assertEqual(m['candidateRulesSha256'],hashlib.sha256(original).hexdigest())
            self.assertNotIn('pag-leads-8c6ef',(output/'apps-script/OwnerGateway.gs').read_text())
            self.assertFalse(m['credentialsIncluded']);self.assertFalse(m['deployExecuted'])
            self.assertNotIn('default',json.loads((output/'.firebaserc').read_text())['projects'])
            self.assertEqual(sorted(p.name for p in (output/'apps-script').iterdir()),['OwnerGateway.gs','appsscript.json'])
            with self.assertRaises(ValueError):bundle.generate('demo-local-review',output)
