import importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('device',pathlib.Path(__file__).parents[1]/'device_preflight.py')
device=importlib.util.module_from_spec(spec);spec.loader.exec_module(device)
class DevicePreflightTests(unittest.TestCase):
    def test_missing_staging_package_is_not_a_probe_failure_and_never_installs(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=pathlib.Path(tmp)/'report.json'
            argv=['device_preflight.py','--serial','synthetic','--apk','synthetic.apk','--report',str(report)]
            with patch.object(sys,'argv',argv), patch.object(device,'run',side_effect=["package: name='com.pinedaagencygroup.leads.staging' versionName='1.9-STAGING'",'device','33']) as calls, patch.object(device.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','')) as probe, patch('builtins.print'):
                device.main()
            self.assertEqual(json.loads(report.read_text())['staging_package_already_installed'],False)
            self.assertEqual(json.loads(report.read_text())['functional_tests'],'NOT_RUN')
            self.assertEqual(probe.call_args.args[0][-3:],['pm','path',device.PACKAGE])
            self.assertFalse(any('install' in str(c) for c in calls.call_args_list))
    def test_offline_apk_rejected_before_device_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv=['device_preflight.py','--serial','synthetic','--apk','offline.apk','--report',str(pathlib.Path(tmp)/'report.json')]
            with patch.object(sys,'argv',argv),patch.object(device,'run',return_value="package: name='com.pinedaagencygroup.leads.qa'") as calls, patch('sys.stderr'),self.assertRaises(SystemExit):
                device.main()
            self.assertEqual(calls.call_count,1)
