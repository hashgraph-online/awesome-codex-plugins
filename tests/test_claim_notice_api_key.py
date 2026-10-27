import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import HTTPRedirectHandler

SPEC = importlib.util.spec_from_file_location('claim_api_key', Path(__file__).resolve().parents[1] / 'scripts/post-claim-notice.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CatalogKeyTests(unittest.TestCase):
    def test_key_is_sent_only_to_the_catalog_read_and_not_forwarded_on_redirect(self):
        with patch.object(MODULE, 'REGISTRY_BROKER_API_KEY', 'fixture-key'), patch.object(
            MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"items":[]}')
        ) as fetch:
            MODULE.api_request('https://hol.org/api/v1/plugins/catalog?q=owner%2Frepo', retry_registry=True)
            request = fetch.call_args.args[0]
            self.assertEqual(request.get_header('X-api-key'), 'fixture-key')
            redirected = HTTPRedirectHandler().redirect_request(request, None, 302, 'found', {}, 'https://other.example/catalog')
            self.assertIsNone(redirected.get_header('X-api-key'))

    def test_github_calls_never_receive_the_registry_key(self):
        with patch.object(MODULE, 'REGISTRY_BROKER_API_KEY', 'fixture-key'), patch.object(
            MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{}')
        ) as fetch:
            MODULE.api_request('https://api.github.com/repos/owner/catalog')
            self.assertIsNone(fetch.call_args.args[0].get_header('X-api-key'))

    def test_bad_origin_path_or_method_cannot_receive_the_key(self):
        with patch.object(MODULE, 'REGISTRY_BROKER_API_KEY', 'fixture-key'), patch.object(MODULE.urllib.request, 'urlopen') as fetch:
            for url, method in [
                ('https://other.example/api/v1/plugins/catalog', 'GET'),
                ('http://hol.org/api/v1/plugins/catalog', 'GET'),
                ('https://hol.org/api/v1/plugins', 'GET'),
                ('https://hol.org/api/v1/plugins/catalog', 'POST'),
            ]:
                with self.subTest(url=url, method=method), self.assertRaises(MODULE.RegistryCatalogFetchError):
                    MODULE.api_request(url, method=method, retry_registry=True)
            fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
