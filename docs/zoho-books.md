# Zoho Books Setup

This project reads Zoho Books credentials from environment variables only. Do not commit real credentials.

## Required Secrets

| Environment variable | What it stores | Where it comes from |
| --- | --- | --- |
| `ZOHO_BOOKS_CLIENT_ID` | OAuth client ID | Zoho API Console connected app |
| `ZOHO_BOOKS_CLIENT_SECRET` | OAuth client secret | Zoho API Console connected app |
| `ZOHO_BOOKS_REFRESH_TOKEN` | Long-lived OAuth refresh token | OAuth authorization/token flow |
| `ZOHO_BOOKS_ORGANIZATION_ID` | Zoho Books organization ID | Zoho Books organization settings or organizations API |
| `ZOHO_BOOKS_ACCOUNTS_URL` | Zoho Accounts URL for the account data center | Defaults to `https://accounts.zoho.com` |
| `ZOHO_BOOKS_API_DOMAIN` | Zoho API domain for Books calls | Defaults to `https://www.zohoapis.com`; token refresh may return a domain |

## GitHub Secrets

For GitHub Actions, add the values under repository Settings -> Secrets and variables -> Actions.

Recommended secret names:

- `ZOHO_BOOKS_CLIENT_ID`
- `ZOHO_BOOKS_CLIENT_SECRET`
- `ZOHO_BOOKS_REFRESH_TOKEN`
- `ZOHO_BOOKS_ORGANIZATION_ID`
- `ZOHO_BOOKS_ACCOUNTS_URL`
- `ZOHO_BOOKS_API_DOMAIN`

## Local Development

Copy `.env.example` to `.env` locally and fill in the values. `.env` files are ignored by git.

The CLI does not automatically load `.env`; export variables in your shell before running commands.

```bash
export ZOHO_BOOKS_CLIENT_ID="..."
export ZOHO_BOOKS_CLIENT_SECRET="..."
export ZOHO_BOOKS_REFRESH_TOKEN="..."
export ZOHO_BOOKS_ORGANIZATION_ID="..."
```

## Commands

List available Zoho Books organizations:

```bash
python -m cfo_agent.cli zoho-organizations
```

List invoices for the configured organization:

```bash
python -m cfo_agent.cli zoho-invoices --status overdue
```

## OAuth Notes

Zoho access tokens are short-lived. The app stores only the refresh token in environment variables, requests an access token when needed, and sends the access token in the `Authorization` header as `Zoho-oauthtoken {access_token}`.
