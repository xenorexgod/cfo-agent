import os
import unittest
from unittest.mock import patch

from cfo_agent.zoho_books import ZohoBooksClient, ZohoBooksConfig, ZohoBooksError


class ZohoBooksConfigTests(unittest.TestCase):
    def test_from_env_requires_core_oauth_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ZohoBooksError, "ZOHO_BOOKS_CLIENT_ID"):
                ZohoBooksConfig.from_env()

    def test_from_env_reads_defaults(self) -> None:
        env = {
            "ZOHO_BOOKS_CLIENT_ID": "client-id",
            "ZOHO_BOOKS_CLIENT_SECRET": "client-secret",
            "ZOHO_BOOKS_REFRESH_TOKEN": "refresh-token",
            "ZOHO_BOOKS_ORGANIZATION_ID": "12345",
        }
        with patch.dict(os.environ, env, clear=True):
            config = ZohoBooksConfig.from_env()
        self.assertEqual(config.accounts_url, "https://accounts.zoho.com")
        self.assertEqual(config.api_domain, "https://www.zohoapis.com")
        self.assertEqual(config.organization_id, "12345")


class ZohoBooksClientTests(unittest.TestCase):
    def test_organization_id_required_for_org_scoped_calls(self) -> None:
        config = ZohoBooksConfig("client", "secret", "refresh")
        client = ZohoBooksClient(config)
        with self.assertRaisesRegex(ZohoBooksError, "ZOHO_BOOKS_ORGANIZATION_ID"):
            client.list_invoices()

    def test_refresh_token_sets_access_token(self) -> None:
        config = ZohoBooksConfig("client", "secret", "refresh")
        client = ZohoBooksClient(config)
        with patch.object(client, "_request_json", return_value={"access_token": "access", "api_domain": "https://www.zohoapis.in"}) as request_json:
            token = client.refresh_access_token()
        self.assertEqual(token, "access")
        self.assertEqual(config.api_domain, "https://www.zohoapis.in")
        self.assertIn("grant_type=refresh_token", request_json.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
