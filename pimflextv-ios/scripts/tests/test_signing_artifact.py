import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('signing_artifact', Path(__file__).resolve().parents[1] / 'signing_artifact.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SigningArtifactTests(unittest.TestCase):
    def test_roundtrip_and_no_plaintext_in_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'fixture.zip'
            payload = b'private IPA fixture' * 100
            source.write_bytes(payload)
            module.encrypt(source, root / 'encrypted', b'fixture-password-32-characters-long')
            self.assertNotIn(payload[:64], (root / 'encrypted' / module.CIPHER).read_bytes())
            module.decrypt(root / 'encrypted', root / 'decoded.zip', b'fixture-password-32-characters-long')
            self.assertEqual((root / 'decoded.zip').read_bytes(), payload)

    def test_tampering_rejected_before_decryption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'fixture.zip').write_bytes(b'fixture payload')
            module.encrypt(root / 'fixture.zip', root / 'encrypted', b'fixture-password-32-characters-long')
            cipher = root / 'encrypted' / module.CIPHER
            data = bytearray(cipher.read_bytes())
            data[-1] ^= 1
            cipher.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'integrity'):
                module.decrypt(root / 'encrypted', root / 'decoded.zip', b'fixture-password-32-characters-long')
            self.assertFalse((root / 'decoded.zip').exists())

    def test_wrong_password_rejected_before_decryption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'fixture.zip').write_bytes(b'fixture payload')
            module.encrypt(root / 'fixture.zip', root / 'encrypted', b'fixture-password-32-characters-long')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                module.decrypt(root / 'encrypted', root / 'decoded.zip', b'wrong-password-32-characters-long')
            self.assertFalse((root / 'decoded.zip').exists())


if __name__ == '__main__': unittest.main()
