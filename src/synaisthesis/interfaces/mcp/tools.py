"""MCP tool registry and handlers (05A section 18, 07 §MCP; M10).

Read-only tools are direct; every mutation goes through the Fidelity Command
Gateway (05A sections 15-17) — without a valid instruction token the mutation
fails closed with FIDELITY_CHANNEL_REQUIRED.  There is no second, weaker
mutation path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from sqlalchemy.orm import Session

from synaisthesis.application.fidelity_service import (
    FidelityConfig,
    cancel_prepared_command,
    commit_command,
    load_command_receipt,
    prepare_command,
)
from synaisthesis.domain.errors import DomainError

TOOL_GET_PROJECT_STATE = "research_get_project_state"
TOOL_GET_PENDING_GATES = "research_get_pending_gates"
TOOL_GET_COMMAND_RECEIPT = "research_get_command_receipt"
TOOL_QUALIFY_DESIGN = "research_qualify_design"
TOOL_PREPARE_COMMAND = "research_prepare_command"
TOOL_COMMIT_COMMAND = "research_commit_command"
TOOL_CANCEL_PREPARED_COMMAND = "research_cancel_prepared_command"

READ_ONLY_TOOLS: tuple[str, ...] = (
    TOOL_GET_PROJECT_STATE,
    TOOL_GET_PENDING_GATES,
    TOOL_GET_COMMAND_RECEIPT,
    TOOL_QUALIFY_DESIGN,
)

MUTATION_TOOLS: tuple[str, ...] = (
    TOOL_PREPARE_COMMAND,
    TOOL_COMMIT_COMMAND,
    TOOL_CANCEL_PREPARED_COMMAND,
)

TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": TOOL_GET_PROJECT_STATE,
        "description": "Read-only project state query (05A 18.1)",
        "inputSchema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
        },
    },
    {
        "name": TOOL_GET_PENDING_GATES,
        "description": "Read-only pending Human Gate query (05A 18.1)",
        "inputSchema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
        },
    },
    {
        "name": TOOL_GET_COMMAND_RECEIPT,
        "description": "Read-only CommandReceipt query (05A 18.1)",
        "inputSchema": {
            "type": "object",
            "properties": {"receipt_id": {"type": "string"}},
            "required": ["receipt_id"],
        },
    },
    {
        "name": TOOL_QUALIFY_DESIGN,
        "description": "Read-only route-aware RQ0-RQ4 qualification run (19 §5 M13.3)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "research_spec_id": {"type": "string"},
                "spec": {"type": "object"},
                "mechanism": {"type": "object"},
                "scope": {"type": "object"},
                "route_decision": {"type": "string"},
                "review_decision": {"type": "string"},
                "primary_scores": {"type": "object"},
                "auditor_scores": {"type": "object"},
            },
            "required": ["project_id", "research_spec_id", "spec", "mechanism", "scope"],
        },
    },
    {
        "name": TOOL_PREPARE_COMMAND,
        "description": "Mutation: prepare a command through the Fidelity Gateway (05A 18.2)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": TOOL_COMMIT_COMMAND,
        "description": "Mutation: commit a prepared command exactly once (05A 18.2)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": TOOL_CANCEL_PREPARED_COMMAND,
        "description": "Mutation: cancel a prepared command (05A 18.2)",
        "inputSchema": {"type": "object", "properties": {}},
    },
)


def call_tool(
    session: Session,
    *,
    tool_name: str,
    arguments: dict[str, Any],
    fidelity: FidelityConfig,
    artifact_root: Path,
) -> Any:
    """Dispatch one MCP tool call; mutations require the fidelity token."""
    if tool_name not in {*READ_ONLY_TOOLS, *MUTATION_TOOLS}:
        raise DomainError(
            f"unknown MCP tool {tool_name!r}",
            error_code="MCP_METHOD_NOT_FOUND",
        )
    if tool_name in READ_ONLY_TOOLS:
        return _call_read_only(session, tool_name, arguments, artifact_root)
    return _call_mutation(session, tool_name, arguments, fidelity, artifact_root)


def _call_read_only(
    session: Session, tool_name: str, arguments: dict[str, Any], artifact_root: Path
) -> Any:
    if tool_name == TOOL_GET_PROJECT_STATE:
        return {"project_id": arguments.get("project_id"), "state": "query-only"}
    if tool_name == TOOL_GET_PENDING_GATES:
        return _pending_gates(session, arguments.get("project_id"), artifact_root)
    if tool_name == TOOL_GET_COMMAND_RECEIPT:
        receipt = load_command_receipt(
            session, arguments.get("receipt_id", ""), artifact_root=artifact_root
        )
        return receipt.to_event_payload()
    if tool_name == TOOL_QUALIFY_DESIGN:
        return _qualify_design(arguments)
    raise DomainError(f"unknown read-only tool {tool_name!r}", error_code="MCP_METHOD_NOT_FOUND")


def _qualify_design(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run one route-aware RQ0-RQ4 qualification over the fixture providers."""
    from datetime import UTC, datetime, timedelta

    from synaisthesis.agents.auditor import NoveltyAuditor
    from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
    from synaisthesis.agents.schemas import (
        MechanismSketch,
        NaturalLanguageSpec,
        ResearchScopeSpec,
    )
    from synaisthesis.application.qualification_service import (
        qualification_export_payload,
        run_qualification_pipeline,
    )
    from synaisthesis.domain.qualification import (
        FormalizationCapabilityProfile,
        PriorArtQueryRecord,
    )
    from synaisthesis.providers.prior_art.base import PriorArtQueryRequest
    from synaisthesis.providers.prior_art.fake import (
        fake_academic_providers,
        fake_engineering_providers,
    )

    now = datetime.now(UTC)
    queries = (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="mcp-q-academic",
                original_text="academic neighbors from S1/S4 fields",
                generated_from=("S1.core_definition", "S4.central_claims"),
                provider="fake-academic",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=now,
            ),
            kind="academic",
        ),
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="mcp-q-engineering",
                original_text="mature engineering projects from S1/S4 fields",
                generated_from=("S1.expected_functions", "S1.target_applications"),
                provider="fake-engineering",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=now,
            ),
            kind="engineering",
        ),
    )
    primary_scores = arguments.get("primary_scores")
    auditor_scores = arguments.get("auditor_scores")

    def primary_factory(route):
        return NoveltyReviewer.create(
            session_id=f"mcp-primary-{route.value}",
            route=route,
            model_family="family-a",
            scores=primary_scores,
        )

    def auditor_factory(route):
        return NoveltyAuditor.create(
            session_id=f"mcp-auditor-{route.value}",
            route=route,
            model_family="family-b",
            scores=auditor_scores,
        )

    run = run_qualification_pipeline(
        project_id=arguments.get("project_id", ""),
        research_spec_id=arguments.get("research_spec_id", ""),
        spec=NaturalLanguageSpec(**arguments["spec"]),
        mechanism=MechanismSketch(**arguments["mechanism"]),
        scope=ResearchScopeSpec(**arguments["scope"]),
        capability_profile=FormalizationCapabilityProfile(
            model_profile_id="mcp-profile",
            capability_tier="ADVANCED",
            formalization_eval_score=92.0,
            math_schema_valid_rate=0.98,
            source_citation_support=True,
            structured_output_support=True,
            context_budget_sufficient=True,
            capability_evaluated_at=now - timedelta(days=1),
        ),
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=queries,
        formalizer_session_id="mcp-formalizer",
        assessor_session_id="mcp-assessor",
        primary_reviewer_factory=primary_factory,
        auditor_reviewer_factory=auditor_factory,
        route_decision=arguments.get("route_decision"),
        review_decision=arguments.get("review_decision", "APPROVE"),
        user_event_id=f"mcp-user:{arguments.get('project_id', '')}",
    )
    return qualification_export_payload(run)


def _pending_gates(session: Session, project_id: str | None, artifact_root: Path) -> dict[str, Any]:
    # Gates are persisted per aggregate; list resolved OPEN gates for the project
    # via the generic gate service over the qualification Gate model.
    from sqlalchemy import select

    from synaisthesis.application.gate_service import HUMAN_GATE_AGGREGATE_TYPE
    from synaisthesis.storage.repositories.event_repository import DomainEventRecord

    if not project_id:
        return {"project_id": None, "gates": []}
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(DomainEventRecord.aggregate_type == HUMAN_GATE_AGGREGATE_TYPE)
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    latest: dict[str, Any] = {}
    for record in records:
        from synaisthesis.application.engineering_design_service import _verified_payload

        payload = _verified_payload(session, record, artifact_root)
        gate = payload.get("gate", {})
        if gate.get("project_id") != project_id:
            continue
        latest[record.aggregate_id] = gate
    open_gates = [gate for gate in latest.values() if gate.get("status") == "OPEN"]
    return {
        "project_id": project_id,
        "gates": [
            {"gate_id": gate.get("gate_id"), "gate_type": gate.get("gate_type")}
            for gate in open_gates
        ],
    }


def _call_mutation(
    session: Session,
    tool_name: str,
    arguments: dict[str, Any],
    fidelity: FidelityConfig,
    artifact_root: Path,
) -> Any:
    from synaisthesis.integrations.codex.recursion_guard import (
        OriginActorType,
        OriginChain,
        OriginHop,
        assert_no_reentrancy,
    )

    chain_data = arguments.get("origin_chain")
    if not isinstance(chain_data, list) or not chain_data:
        raise DomainError(
            "mutation 缺少 origin_chain；递归防护 fail closed",
            error_code="REENTRANCY_BLOCKED",
        )
    chain = OriginChain(
        hops=tuple(
            OriginHop(
                actor_type=OriginActorType(hop.get("actor_type", "")),
                session_id=hop.get("session_id", ""),
                delegation_id=hop.get("delegation_id"),
            )
            for hop in chain_data
        )
    )
    assert_no_reentrancy(chain)
    token_data = arguments.get("instruction_token")
    if not isinstance(token_data, dict):
        raise DomainError(
            "mutation 缺少 instruction_token；Fidelity 通道未建立，fail closed",
            error_code="FIDELITY_CHANNEL_REQUIRED",
        )
    from synaisthesis.fidelity.instruction_token import InstructionToken

    token = InstructionToken(**token_data)
    from synaisthesis.fidelity.context_manifest import ContextManifest
    from synaisthesis.fidelity.instruction_delta import (
        CommandProposal,
        PlatformInterpretation,
    )
    from synaisthesis.fidelity.instruction_token import OperationClass

    def _structured(data: Any, cls: type) -> Any:
        if data is None:
            return None
        fields = dict(data)
        for key in (
            "prohibitions",
            "stop_conditions",
            "requested_tools",
            "expected_outputs",
            "constraints",
            "unresolved_references",
            "selected_file_refs",
            "selected_line_ranges",
            "attached_artifact_refs",
        ):
            if key in fields and isinstance(fields[key], list):
                fields[key] = tuple(fields[key])
        constructor = cast(Any, cls)
        return constructor(**fields)

    if tool_name == TOOL_PREPARE_COMMAND:
        prepared = prepare_command(
            session,
            fidelity,
            instruction_token=token,
            instruction_id=arguments.get("instruction_id", ""),
            project_id=arguments.get("project_id", ""),
            command_proposal=_structured(arguments.get("command_proposal"), CommandProposal),
            platform_interpretation=_structured(
                arguments.get("platform_interpretation"), PlatformInterpretation
            ),
            context_manifest=_structured(arguments.get("context_manifest"), ContextManifest),
            expected_state_version=arguments.get("expected_state_version", -1),
            idempotency_key=arguments.get("idempotency_key", ""),
            operation_class=OperationClass(arguments.get("operation_class", "")),
            artifact_root=artifact_root,
        )
        return prepared.to_event_payload()
    if tool_name == TOOL_COMMIT_COMMAND:
        receipt = commit_command(
            session,
            fidelity,
            prepared_command_id=arguments.get("prepared_command_id", ""),
            confirmation_nonce=arguments.get("confirmation_nonce", ""),
            user_confirmation_text=arguments.get("user_confirmation_text"),
            expected_state_version=arguments.get("expected_state_version", -1),
            idempotency_key=arguments.get("idempotency_key", ""),
            artifact_root=artifact_root,
        )
        return receipt.to_event_payload()
    if tool_name == TOOL_CANCEL_PREPARED_COMMAND:
        cancelled = cancel_prepared_command(
            session,
            prepared_command_id=arguments.get("prepared_command_id", ""),
            artifact_root=artifact_root,
        )
        return cancelled.to_event_payload()
    raise DomainError(f"unknown mutation tool {tool_name!r}", error_code="MCP_METHOD_NOT_FOUND")


__all__ = [
    "MUTATION_TOOLS",
    "READ_ONLY_TOOLS",
    "TOOL_CANCEL_PREPARED_COMMAND",
    "TOOL_COMMIT_COMMAND",
    "TOOL_GET_COMMAND_RECEIPT",
    "TOOL_GET_PENDING_GATES",
    "TOOL_GET_PROJECT_STATE",
    "TOOL_PREPARE_COMMAND",
    "TOOL_QUALIFY_DESIGN",
    "TOOL_DEFINITIONS",
    "call_tool",
]
