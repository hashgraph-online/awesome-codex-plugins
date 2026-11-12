import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch
from urllib.request import HTTPRedirectHandler
import yaml

SPEC = importlib.util.spec_from_file_location('claim_api_key', Path(__file__).resolve().parents[1] / 'scripts/post-claim-notice.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MergedCatalogCheckoutTests(unittest.TestCase):
    def test_claim_notice_scopes_write_permissions_to_its_job(self):
        workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / '.github/workflows/claim-notice.yml').read_text())
        self.assertEqual(workflow['permissions'], {})
        self.assertEqual(
            workflow['jobs']['post-claim-notice']['permissions'],
            {'contents': 'read', 'issues': 'write', 'pull-requests': 'write'},
        )

    def test_marketplace_sync_writes_only_from_non_pr_job(self):
        workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / '.github/workflows/validate-plugins.yml').read_text())
        self.assertEqual(workflow['permissions'], {})
        self.assertEqual(workflow['jobs']['sync']['permissions'], {'contents': 'write'})
        self.assertEqual(workflow['jobs']['sync']['if'], "github.event_name != 'pull_request'")
        self.assertNotIn('secrets.GITHUB_TOKEN', Path(__file__).resolve().parents[1].joinpath('.github/workflows/validate-plugins.yml').read_text())

    def test_closed_event_reads_catalog_after_the_merge(self):
        workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / '.github/workflows/claim-notice.yml').read_text())
        snapshots = {
            'event-base-sha': '## Community Plugins\n- [Old](https://github.com/owner/old) - Old plugin.\n',
            'main': '## Community Plugins\n- [New](https://github.com/owner/new-plugin) - New plugin.\n',
        }
        checked = 0
        for job in workflow['jobs'].values():
            for step in job.get('steps', []):
                if not step.get('uses', '').startswith('actions/checkout@'):
                    continue
                ref = step.get('with', {}).get('ref', 'event-base-sha')
                if ref == '${{ github.event.repository.default_branch }}':
                    ref = 'main'
                with self.subTest(ref=ref), patch('builtins.open', mock_open(read_data=snapshots[ref])):
                    self.assertIn('owner/new-plugin', MODULE.catalog_source_repos())
                checked += 1
        self.assertGreater(checked, 0)


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
