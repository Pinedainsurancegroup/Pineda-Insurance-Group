import copy
import datetime as dt
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('signing_profile', Path(__file__).resolve().parents[1] / 'signing_profile.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SigningProfileTests(unittest.TestCase):
    def setUp(self):
        self.identity = hashlib.sha1(b'fixture-certificate').hexdigest().upper()
        self.now = dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc)
        self.profile = {'TeamIdentifier': [module.TEAM], 'Platform': ['iOS'],
            'UUID': '7cf2f124-bdba-41d8-8f17-18c49448a442',
            'ExpirationDate': self.now + dt.timedelta(days=30),
            'DeveloperCertificates': [b'fixture-certificate'],
            'Entitlements': {'application-identifier': f'{module.TEAM}.{module.BUNDLE}',
                'com.apple.developer.team-identifier': module.TEAM,
                'get-task-allow': False, 'beta-reports-active': True}}

    def test_valid_app_store_profile(self):
        for profile_uuid in [self.profile['UUID'], self.profile['UUID'].upper()]:
            with self.subTest(profile_uuid=profile_uuid):
                self.profile['UUID'] = profile_uuid
                self.assertEqual(module.validate(self.profile, self.identity, self.now), profile_uuid)

    def test_noncanonical_uuid_rejected(self):
        for profile_uuid in ['../profile', self.profile['UUID'].replace('-', ''), '{' + self.profile['UUID'] + '}']:
            with self.subTest(profile_uuid=profile_uuid):
                self.profile['UUID'] = profile_uuid
                with self.assertRaises(ValueError): module.validate(self.profile, self.identity, self.now)

    def test_wrong_team_and_bundle_rejected(self):
        for field, value in [('application-identifier', 'U47SH3LZM6.com.other.app'),
                             ('com.apple.developer.team-identifier', 'OTHERTEAM0')]:
            with self.subTest(field=field):
                p = copy.deepcopy(self.profile)
                p['Entitlements'][field] = value
                with self.assertRaises(ValueError): module.validate(p, self.identity, self.now)
        self.profile['TeamIdentifier'] = ['OTHERTEAM0']
        with self.assertRaises(ValueError): module.validate(self.profile, self.identity, self.now)

    def test_development_ad_hoc_enterprise_rejected(self):
        for field, value in [('ProvisionedDevices', ['test-device']), ('ProvisionsAllDevices', True)]:
            with self.subTest(field=field):
                p = copy.deepcopy(self.profile)
                p[field] = value
                with self.assertRaises(ValueError): module.validate(p, self.identity, self.now)
        self.profile['Entitlements']['get-task-allow'] = True
        with self.assertRaises(ValueError): module.validate(self.profile, self.identity, self.now)

    def test_expired_and_wrong_identity_rejected(self):
        with self.assertRaises(ValueError): module.validate(self.profile, '0' * 40, self.now)
        self.profile['ExpirationDate'] = self.now
        with self.assertRaises(ValueError): module.validate(self.profile, self.identity, self.now)

    def test_missing_distribution_entitlements_rejected(self):
        for field in ['get-task-allow', 'beta-reports-active']:
            p = copy.deepcopy(self.profile)
            del p['Entitlements'][field]
            with self.assertRaises(ValueError): module.validate(p, self.identity, self.now)

    def test_naive_plist_dates_are_utc(self):
        self.profile['ExpirationDate'] = self.profile['ExpirationDate'].replace(tzinfo=None)
        module.validate(self.profile, self.identity, self.now)


if __name__ == '__main__': unittest.main()
