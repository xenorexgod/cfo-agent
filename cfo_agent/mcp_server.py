from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from .zoho_books import ZohoBooksError, build_client_from_env

JsonObject = dict[str, Any]
ToolHandler = Callable[[JsonObject], JsonObject]


TOOL_SCHEMAS: list[JsonObject] = [
    {
        "name": "zoho_books_list_organizations",
        "description": "List Zoho Books organizations available to the configured OAuth credentials.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "zoho_books_list_invoices",
        "description": "List Zoho Books invoices for the configured organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional invoice status filter such as overdue, sent, paid, or draft."},
                "from_date": {"type": "string", "description": "Optional invoice start date in YYYY-MM-DD format."},
                "to_date": {"type": "string", "description": "Optional invoice end date in YYYY-MM-DD format."},
                "page": {"type": "string", "description": "Optional Zoho page number."},
                "per_page": {"type": "string", "description": "Optional Zoho page size."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "zoho_books_list_bills",
        "description": "List Zoho Books vendor bills for the configured organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional bill status filter."},
                "from_date": {"type": "string", "description": "Optional bill start date in YYYY-MM-DD format."},
                "to_date": {"type": "string", "description": "Optional bill end date in YYYY-MM-DD format."},
                "page": {"type": "string", "description": "Optional Zoho page number."},
                "per_page": {"type": "string", "description": "Optional Zoho page size."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "zoho_books_list_expenses",
        "description": "List Zoho Books expenses for the configured organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string", "description": "Optional expense start date in YYYY-MM-DD format."},
                "to_date": {"type": "string", "description": "Optional expense end date in YYYY-MM-DD format."},
                "page": {"type": "string", "description": "Optional Zoho page number."},
                "per_page": {"type": "string", "description": "Optional Zoho page size."},
            },
            "additionalProperties": False,
        },
    },
]


def _zoho_params(arguments: JsonObject) -> dict[str, str]:
    params: dict[str, str] = {}
    for source, target in {
        "status": "status",
        "from_date": "date_start",
        "to_date": "date_end",
        "page": "page",
        "per_page": "per_page",
    }.items():
        value = arguments.get(source)
        if value not in (None, ""):
            params[target] = str(value)
    return params


def _json_text(payload: JsonObject) -> JsonObject:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, sort_keys=True)}]}


def list_organizations(_: JsonObject) -> JsonObject:
    return _json_text(build_client_from_env().list_organizations())


def list_invoices(arguments: JsonObject) -> JsonObject:
    return _json_text(build_client_from_env().list_invoices(**_zoho_params(arguments)))


def list_bills(arguments: JsonObject) -> JsonObject:
    return _json_text(build_client_from_env().list_bills(**_zoho_params(arguments)))


def list_expenses(arguments: JsonObject) -> JsonObject:
    return _json_text(build_client_from_env().list_expenses(**_zoho_params(arguments)))


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "zoho_books_list_organizations": list_organizations,
    "zoho_books_list_invoices": list_invoices,
    "zoho_books_list_bills": list_bills,
    "zoho_books_list_expenses": list_expenses,
}


def handle_request(message: JsonObject) -> JsonObject | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if request_id is None:
        return None

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "cfo-agent-zoho-books", "version": "0.1.0"},
                },
            }
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOL_SCHEMAS}}
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name not in TOOL_HANDLERS:
                raise ValueError(f"Unknown tool: {name}")
            return {"jsonrpc": "2.0", "id": request_id, "result": TOOL_HANDLERS[name](arguments)}
        raise ValueError(f"Unsupported MCP method: {method}")
    except (ValueError, ZohoBooksError) as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def serve(input_stream: Any = sys.stdin, output_stream: Any = sys.stdout) -> None:
    for line in input_stream:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle_request(message)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
            output_stream.flush()


def main() -> int:
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
