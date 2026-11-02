import importlib.util,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
spec=importlib.util.spec_from_file_location('importer',pathlib.Path(__file__).parents[1]/'import_staging_android.py')
importer=importlib.util.module_from_spec(spec);spec.loader.exec_module(importer)
class ImportTests(unittest.TestCase):
    def test_wrong_project_and_missing_configuration_fail_without_inventing_values(self):
        for info in [{},{'project_info':{'project_id':'pag-leads-8c6ef','project_number':'880973015225'}},{'project_info':{'project_id':'pag-leads-staging','project_number':'301600139735'}}]:
            with self.assertRaises(ValueError):importer.convert(info)
    def test_production_android_package_rejected(self):
        data={'project_info':{'project_id':'pag-leads-staging','project_number':'301600139735'},'client':[{'client_info':{'android_client_info':{'package_name':'com.pinedaagencygroup.leads'}}}]}
        with self.assertRaises(ValueError):importer.convert(data)
    def test_missing_oauth_is_reported_before_attempting_any_service(self):
        data={'project_info':{'project_id':'pag-leads-staging','project_number':'301600139735'},'client':[{'client_info':{'android_client_info':{'package_name':importer.PACKAGE}},'api_key':[{'current_key':'local-parser-input-not-used-for-auth'}]}]}
        with self.assertRaisesRegex(ValueError,'OAuth'):importer.convert(data)
