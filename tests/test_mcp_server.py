import json
import unittest
from unittest.mock import Mock, patch

from cfo_agent import mcp_server


class McpServerTests(unittest.TestCase):
    def test_initialize_response(self) -> None:
        response = mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["serverInfo"]["name"], "cfo-agent-zoho-books")
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_list_includes_zoho_tools(self) -> None:
        response = mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tool_names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("zoho_books_list_organizations", tool_names)
        self.assertIn("zoho_books_list_invoices", tool_names)

    def test_tool_call_dispatches_to_zoho_client(self) -> None:
        client = Mock()
        client.list_invoices.return_value = {"invoices": [{"invoice_id": "1"}]}
        with patch.object(mcp_server, "build_client_from_env", return_value=client):
            response = mcp_server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "zoho_books_list_invoices",
                        "arguments": {"status": "overdue", "from_date": "2026-06-01"},
                    },
                }
            )
        client.list_invoices.assert_called_once_with(status="overdue", date_start="2026-06-01")
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["invoices"][0]["invoice_id"], "1")

    def test_unknown_tool_returns_error(self) -> None:
        response = mcp_server.handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "missing", "arguments": {}}}
        )
        self.assertIn("error", response)


if __name__ == "__main__":
    unittest.main()
