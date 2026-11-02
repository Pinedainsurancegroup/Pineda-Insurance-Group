import importlib.util,pathlib,unittest,xml.etree.ElementTree as ET
spec=importlib.util.spec_from_file_location('client',pathlib.Path(__file__).parents[1]/'prepare_staging.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
class LinkTests(unittest.TestCase):
    def test_auth_links_and_launcher_are_isolated_without_credentials(self):
        data=client.staging_manifest('demo-local-review');root=ET.fromstring(data)
        android='{http://schemas.android.com/apk/res/android}';tools='{http://schemas.android.com/tools}'
        activity=root.find('application/activity')
        self.assertEqual(activity.attrib[tools+'node'],'replace')
        hosts=[n.attrib[android+'host'] for n in activity.findall('intent-filter/data')]
        self.assertEqual(hosts,['demo-local-review.firebaseapp.com'])
        self.assertNotIn(b'pag-leads-8c6ef',data)
        self.assertEqual(len(activity.findall('intent-filter')),2)
        service=root.find('application/service')
        self.assertEqual(service.attrib[android+'name'],'com.pinedaagencygroup.leads.LeadMonitorService')
        self.assertEqual(service.attrib[tools+'node'],'remove')
    def test_production_link_host_rejected(self):
        with self.assertRaises(ValueError):client.staging_manifest('pag-leads-8c6ef')
