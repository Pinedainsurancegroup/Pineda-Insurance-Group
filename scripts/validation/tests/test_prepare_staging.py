import importlib.util, pathlib, tempfile, unittest, xml.etree.ElementTree as ET
spec = importlib.util.spec_from_file_location('staging', pathlib.Path(__file__).parents[1] / 'prepare_staging.py')
staging = importlib.util.module_from_spec(spec); spec.loader.exec_module(staging)

def synthetic():
    return dict(environment='staging', android_package=staging.PACKAGE,
        pag_firebase_project_id='synthetic-test-project', pag_firebase_application_id='1:123456789:android:abcdef1234',
        pag_firebase_api_key='AIza'+'x'*35, pag_firebase_sender_id='123456789',
        pag_firebase_web_client_id='123456789-synthetic.apps.googleusercontent.com',
        pag_owner_gateway_url='https://script.google.com/macros/s/SYNTHETIC_NOT_DEPLOYED/exec')

class StagingTests(unittest.TestCase):
    def test_missing_and_production_fields_rejected(self):
        for key in staging.FIELDS:
            missing = synthetic(); missing[key] = ''
            with self.assertRaises(ValueError): staging.validate(missing, 'synthetic-test-project')
            prod = synthetic(); prod[key] = staging.production_values()[key]
            with self.assertRaises(ValueError): staging.validate(prod, 'synthetic-test-project')
    def test_wrong_project_and_package_rejected(self):
        with self.assertRaises(ValueError): staging.validate(synthetic(), 'different-project')
        config = synthetic(); config['android_package'] = 'com.pinedaagencygroup.leads'
        with self.assertRaises(ValueError): staging.validate(config, 'synthetic-test-project')
    def test_foreign_gateway_and_number_rejected(self):
        for key, value in [('pag_owner_gateway_url','https://example.invalid/exec'),('pag_firebase_sender_id','111111111')]:
            config = synthetic(); config[key] = value
            with self.assertRaises(ValueError): staging.validate(config, 'synthetic-test-project')
    def test_output_complete_and_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / 'overlay'
            staging.generate(synthetic(), 'synthetic-test-project', output)
            values = {n.attrib['name']: n.text for n in ET.parse(output/'res/values/staging.xml').getroot()}
            for key in staging.FIELDS: self.assertEqual(values[key], synthetic()[key])
            self.assertEqual(values['pag_qa_build'], 'true')
            with self.assertRaises(ValueError): staging.generate(synthetic(), 'synthetic-test-project', output)

if __name__ == '__main__': unittest.main()
