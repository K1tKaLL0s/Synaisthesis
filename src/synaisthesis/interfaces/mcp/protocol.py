"""MCP stdio JSON-RPC framing (05A section 18, 07 §MCP; M10).

Implements the LSP-style Content-Length framed JSON-RPC 2.0 transport used by
MCP servers over stdio.  Parsing is strict: malformed framing or unknown
methods fail closed.
"""

from __future__ import annotations

import json
from typing import Any, TextIO

from synaisthesis.domain.errors import DomainError

JSONRPC_VERSION = "2.0"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def read_message(stream: TextIO) -> dict[str, Any] | None:
    """Read one Content-Length framed JSON-RPC message; None on EOF."""
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if line == "":
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length = headers.get("content-length")
    if length is None:
        raise DomainError(
            "MCP message missing Content-Length header",
            error_code="MCP_FRAMING_INVALID",
        )
    body = stream.read(int(length))
    try:
        message = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DomainError(
            f"MCP body is not valid JSON: {exc}",
            error_code="MCP_FRAMING_INVALID",
        ) from exc
    if not isinstance(message, dict):
        raise DomainError(
            "MCP message must be a JSON object",
            error_code="MCP_FRAMING_INVALID",
        )
    return message


def write_message(stream: TextIO, message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    stream.write(f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}")
    stream.flush()


def rpc_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def rpc_notification(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "method": method, "params": params}


__all__ = [
    "INTERNAL_ERROR",
    "INVALID_PARAMS",
    "INVALID_REQUEST",
    "JSONRPC_VERSION",
    "METHOD_NOT_FOUND",
    "PARSE_ERROR",
    "read_message",
    "rpc_error",
    "rpc_notification",
    "rpc_response",
    "write_message",
]
