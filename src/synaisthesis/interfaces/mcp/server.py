"""MCP stdio server (05A section 18, 07 §MCP; M10).

A minimal MCP server over stdio JSON-RPC: initialize handshake, tools/list and
tools/call.  Every mutation is routed through the Fidelity Command Gateway and
fails closed without an instruction token; read-only tools are direct.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO

from synaisthesis.application.fidelity_service import FidelityConfig
from synaisthesis.domain.errors import DomainError
from synaisthesis.interfaces.mcp.protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    read_message,
    rpc_error,
    rpc_response,
    write_message,
)
from synaisthesis.interfaces.mcp.tools import TOOL_DEFINITIONS, call_tool

PROTOCOL_VERSION = "2024-11-05"


class MCPServer:
    """One stdio MCP server session bound to a database session factory."""

    def __init__(
        self,
        session_factory,
        *,
        fidelity: FidelityConfig,
        artifact_root: Path,
    ) -> None:
        self._session_factory = session_factory
        self._fidelity = fidelity
        self._artifact_root = artifact_root

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Handle one request; returns None for notifications."""
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}
        if request_id is None:
            return None  # notification
        try:
            if method == "initialize":
                return rpc_response(
                    request_id,
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "synaisthesis-mcp", "version": "0.1.0"},
                    },
                )
            if method == "tools/list":
                return rpc_response(request_id, {"tools": list(TOOL_DEFINITIONS)})
            if method == "tools/call":
                return self._handle_tool_call(request_id, params)
            return rpc_error(request_id, METHOD_NOT_FOUND, f"unknown method {method!r}")
        except DomainError as exc:
            if exc.error_code == "MCP_METHOD_NOT_FOUND":
                return rpc_error(request_id, METHOD_NOT_FOUND, str(exc))
            return rpc_error(request_id, INVALID_REQUEST, f"{exc.error_code}: {exc}")
        except Exception as exc:  # noqa: BLE001 - server boundary
            return rpc_error(request_id, INTERNAL_ERROR, str(exc))

    def _handle_tool_call(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(tool_name, str) or not isinstance(arguments, dict):
            return rpc_error(request_id, INVALID_PARAMS, "name/arguments required")
        with self._session_factory() as session:
            result = call_tool(
                session,
                tool_name=tool_name,
                arguments=arguments,
                fidelity=self._fidelity,
                artifact_root=self._artifact_root,
            )
        return rpc_response(request_id, {"content": [{"type": "text", "text": str(result)}]})

    def serve_stdio(self, stdin: TextIO, stdout: TextIO) -> None:
        """Serve requests until EOF."""
        while True:
            try:
                message = read_message(stdin)
            except DomainError:
                write_message(stdout, rpc_error(None, INVALID_REQUEST, "framing error"))
                continue
            if message is None:
                return
            response = self.handle(message)
            if response is not None:
                write_message(stdout, response)


__all__ = ["MCPServer", "PROTOCOL_VERSION"]
