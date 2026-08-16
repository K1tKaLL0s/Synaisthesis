"""Deterministic text-source to SVG diagram renderer (03B, section 7.3).

Every diagram keeps a versionable text source plus a rendered SVG plus a
render receipt; machine-readable design objects are authoritative and images
are projection views.  This built-in renderer is intentionally deterministic
and dependency-free (no Mermaid/Graphviz CLI) so the contract can run in CI;
a real renderer may replace the implementation later but must keep the same
source/SVG/hash/receipt contract.

Mini source language (one directive per line)::

    node <stable-id> "<label>"
    edge <from-id> <to-id>

Every node id must be present in the caller-provided node component mapping
(stable ID rule); every edge endpoint must name a known node, otherwise the
render records broken links instead of guessing.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex

_NODE_LINE = re.compile(r'^\s*node\s+([A-Za-z0-9_.-]+)\s+"([^"]*)"\s*$')
_EDGE_LINE = re.compile(r"^\s*edge\s+([A-Za-z0-9_.-]+)\s+([A-Za-z0-9_.-]+)\s*$")

SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
    'width="{width}" height="{height}" id="diagram-{diagram_id}">\n'
    "{body}"
    "</svg>\n"
)


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("render payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class DiagramSource:
    """A versionable diagram text source (03B, section 7.3)."""

    diagram_id: str
    title: str
    version: int
    input_hash: str
    legend: str
    node_edge_semantics: str
    source_text: str
    node_component_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.diagram_id.strip() or not self.source_text.strip():
            raise DomainError(
                "diagram source requires diagram_id and non-empty text",
                error_code="DIAGRAM_INVALID",
            )
        if not self.node_component_ids:
            raise DomainError(
                f"diagram {self.diagram_id!r} 没有节点到组件的稳定 ID 映射",
                error_code="DIAGRAM_INVALID",
            )
        if not self.legend.strip() or not self.node_edge_semantics.strip():
            raise DomainError(
                f"diagram {self.diagram_id!r} requires legend and node/edge semantics",
                error_code="DIAGRAM_INVALID",
            )


@dataclass(frozen=True, slots=True)
class DiagramRenderResult:
    """Rendered SVG with source/SVG hashes and a receipt (03B, section 7.3)."""

    diagram_id: str
    source_text: str
    source_hash: str
    svg_text: str
    svg_hash: str
    render_receipt: str
    rendered_node_ids: tuple[str, ...]
    broken_link_refs: tuple[str, ...] = ()

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def _parse_source(
    source_text: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """Return (node-id,label) pairs and (from,to) edge pairs from the source."""
    nodes: list[tuple[str, str]] = []
    edges: list[tuple[str, str]] = []
    for line in source_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        node_match = _NODE_LINE.match(line)
        if node_match:
            nodes.append((node_match.group(1), node_match.group(2)))
            continue
        edge_match = _EDGE_LINE.match(line)
        if edge_match:
            edges.append((edge_match.group(1), edge_match.group(2)))
            continue
        raise DomainError(
            f"无法解析图示源行：{stripped!r}",
            error_code="DIAGRAM_SOURCE_INVALID",
        )
    return tuple(nodes), tuple(edges)


def render_diagram_source(
    source: DiagramSource,
    *,
    node_component_mapping: dict[str, str],
) -> DiagramRenderResult:
    """Render a text source into deterministic SVG with a receipt (03B, 7.3).

    node_component_mapping maps diagram node ids to stable component ids.  A
    node without a mapping entry, or an edge to an unknown node, is a broken
    reference: the render records it and the SVG is still produced so the
    break is auditable, but downstream gates must fail on it.
    """
    nodes, edges = _parse_source(source.source_text)
    known = {node_id for node_id, _label in nodes}
    broken: list[str] = []
    for node_id, _label in nodes:
        if node_id not in node_component_mapping:
            broken.append(f"node {node_id} 缺少稳定 component ID 映射")
    for from_id, to_id in edges:
        if from_id not in known:
            broken.append(f"edge 起点 {from_id} 未定义")
        if to_id not in known:
            broken.append(f"edge 终点 {to_id} 未定义")

    body_lines: list[str] = []
    for index, (node_id, label) in enumerate(nodes):
        body_lines.append(
            f'  <g id="{node_id}" data-component="{node_component_mapping.get(node_id, "")}">'
            f'<rect x="10" y="{10 + index * 30}" width="180" height="24"/>'
            f'<text x="20" y="{26 + index * 30}">{label}</text></g>\n'
        )
    for index, (from_id, to_id) in enumerate(edges):
        body_lines.append(
            f'  <g id="edge-{index + 1}" data-from="{from_id}" data-to="{to_id}">'
            f'<line x1="20" y1="{40 + index * 30}" x2="180" y2="{40 + index * 30}" '
            f'stroke="black"/></g>\n'
        )
    svg_text = SVG_TEMPLATE.format(
        width=400,
        height=60 + max(len(nodes), len(edges)) * 30,
        diagram_id=source.diagram_id,
        body="".join(body_lines),
    )
    source_hash = sha256_hex({"diagram_id": source.diagram_id, "source": source.source_text})
    svg_hash = sha256_hex({"diagram_id": source.diagram_id, "svg": svg_text})
    receipt = f"render:{source.diagram_id}:{source_hash}:{svg_hash}"
    return DiagramRenderResult(
        diagram_id=source.diagram_id,
        source_text=source.source_text,
        source_hash=source_hash,
        svg_text=svg_text,
        svg_hash=svg_hash,
        render_receipt=receipt,
        rendered_node_ids=tuple(node_id for node_id, _label in nodes),
        broken_link_refs=tuple(broken),
    )


def verify_diagram_render(result: DiagramRenderResult) -> tuple[str, ...]:
    """Recompute source/SVG hashes and the receipt; fail on any mismatch (03B, 7.3)."""
    blockers: list[str] = []
    source_hash = sha256_hex({"diagram_id": result.diagram_id, "source": result.source_text})
    if source_hash != result.source_hash:
        blockers.append("source hash 与源文本不符")
    svg_hash = sha256_hex({"diagram_id": result.diagram_id, "svg": result.svg_text})
    if svg_hash != result.svg_hash:
        blockers.append("SVG hash 与渲染文本不符")
    expected_receipt = f"render:{result.diagram_id}:{source_hash}:{svg_hash}"
    if result.render_receipt != expected_receipt:
        blockers.append("渲染回执不可复算")
    blockers.extend(f"broken link: {ref}" for ref in result.broken_link_refs)
    return tuple(blockers)


__all__ = [
    "DiagramRenderResult",
    "DiagramSource",
    "render_diagram_source",
    "verify_diagram_render",
]
