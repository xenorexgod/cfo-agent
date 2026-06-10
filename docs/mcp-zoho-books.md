# Zoho Books MCP Server

`cfo-agent` can expose Zoho Books data through a local MCP stdio server. This lets an MCP-capable agent fetch finance data with tools while Zoho secrets remain in environment variables.

## Available MCP Tools

| Tool | Purpose |
| --- | --- |
| `zoho_books_list_organizations` | Confirms OAuth works and lists available Zoho Books organizations. |
| `zoho_books_list_invoices` | Fetches invoices for the configured organization. |
| `zoho_books_list_bills` | Fetches vendor bills for the configured organization. |
| `zoho_books_list_expenses` | Fetches expenses for the configured organization. |

The invoice, bill, and expense tools accept optional `from_date`, `to_date`, `page`, and `per_page` arguments. Invoice and bill tools also accept `status`.

## Required Environment Variables

Set the same variables used by the CLI:

```bash
ZOHO_BOOKS_CLIENT_ID=
ZOHO_BOOKS_CLIENT_SECRET=
ZOHO_BOOKS_REFRESH_TOKEN=
ZOHO_BOOKS_ORGANIZATION_ID=
ZOHO_BOOKS_ACCOUNTS_URL=https://accounts.zoho.com
ZOHO_BOOKS_API_DOMAIN=https://www.zohoapis.com
```

For India accounts, use:

```bash
ZOHO_BOOKS_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_BOOKS_API_DOMAIN=https://www.zohoapis.in
```

## Example MCP Client Configuration

Use placeholders only in shared config. Put real values in your local environment or secret manager.

```json
{
  "mcpServers": {
    "zoho-books": {
      "command": "python",
      "args": ["-m", "cfo_agent.mcp_server"],
      "cwd": "/absolute/path/to/cfo-agent",
      "env": {
        "ZOHO_BOOKS_CLIENT_ID": "your-client-id",
        "ZOHO_BOOKS_CLIENT_SECRET": "your-client-secret",
        "ZOHO_BOOKS_REFRESH_TOKEN": "your-refresh-token",
        "ZOHO_BOOKS_ORGANIZATION_ID": "your-organization-id",
        "ZOHO_BOOKS_ACCOUNTS_URL": "https://accounts.zoho.com",
        "ZOHO_BOOKS_API_DOMAIN": "https://www.zohoapis.com"
      }
    }
  }
}
```

## Local Smoke Test

You can verify the server responds to MCP initialization without Zoho credentials:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' \
  | python -m cfo_agent.mcp_server
```

To test a real Zoho fetch, first export the Zoho environment variables, then call the tool from an MCP client or run:

```bash
python -m cfo_agent.cli zoho-organizations
```

## Safety Notes

- Do not paste Zoho secrets into prompts or committed files.
- Keep the MCP server read-only until the CFO pipeline is stable.
- Expect Zoho responses to contain customer, vendor, invoice, and payment data. Treat tool output as confidential finance data.
