"""M2.9 contract tests for the deterministic diagram renderer (03B, section 7.3)."""

from __future__ import annotations

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.renderers.diagram_renderers import (
    DiagramSource,
    render_diagram_source,
    verify_diagram_render,
)

SOURCE_TEXT = 'node n1 "Trace Engine"\nnode n2 "CLI"\nedge n1 n2\n'
MAPPING = {"n1": "comp-1", "n2": "comp-2"}


def _source(**overrides) -> DiagramSource:
    params = {
        "diagram_id": "dg-1",
        "title": "system context",
        "version": 1,
        "input_hash": "i" * 64,
        "legend": "boxes are components",
        "node_edge_semantics": "solid=call",
        "source_text": SOURCE_TEXT,
        "node_component_ids": ("n1", "n2"),
    }
    params.update(overrides)
    return DiagramSource(**params)


def test_render_is_deterministic():
    first = render_diagram_source(_source(), node_component_mapping=MAPPING)
    second = render_diagram_source(_source(), node_component_mapping=MAPPING)
    assert first.svg_text == second.svg_text
    assert first.source_hash == second.source_hash
    assert first.svg_hash == second.svg_hash
    assert first.render_receipt == second.render_receipt
    assert verify_diagram_render(first) == ()


def test_render_keeps_stable_ids_and_machine_objects():
    result = render_diagram_source(_source(), node_component_mapping=MAPPING)
    assert result.rendered_node_ids == ("n1", "n2")
    assert 'id="n1"' in result.svg_text
    assert 'id="n2"' in result.svg_text
    assert 'data-component="comp-1"' in result.svg_text
    # image is a projection: node/edge semantics live in the machine mapping
    assert len(result.source_hash) == 64
    assert len(result.svg_hash) == 64


def test_render_rejects_broken_edge_endpoint():
    result = render_diagram_source(
        _source(source_text='node n1 "A"\nedge n1 ghost\n'),
        node_component_mapping={"n1": "comp-1"},
    )
    assert result.broken_link_refs
    assert verify_diagram_render(result)  # downstream gates must fail on breaks


def test_render_records_node_without_stable_id():
    result = render_diagram_source(
        _source(node_component_ids=("n1",)),
        node_component_mapping={},  # n2 has no mapping but n1 does not either
    )
    # both nodes lack component mapping -> recorded as broken references
    assert any("n1" in ref for ref in result.broken_link_refs)
    assert any("n2" in ref for ref in result.broken_link_refs)


def test_verify_detects_source_tamper():
    result = render_diagram_source(_source(), node_component_mapping=MAPPING)
    tampered = type(result)(
        diagram_id=result.diagram_id,
        source_text=result.source_text + "# tampered\n",
        source_hash=result.source_hash,
        svg_text=result.svg_text,
        svg_hash=result.svg_hash,
        render_receipt=result.render_receipt,
        rendered_node_ids=result.rendered_node_ids,
    )
    blockers = verify_diagram_render(tampered)
    assert any("source hash" in blocker for blocker in blockers)


def test_verify_detects_svg_tamper():
    result = render_diagram_source(_source(), node_component_mapping=MAPPING)
    tampered = type(result)(
        diagram_id=result.diagram_id,
        source_text=result.source_text,
        source_hash=result.source_hash,
        svg_text=result.svg_text + "</svg>",
        svg_hash=result.svg_hash,
        render_receipt=result.render_receipt,
        rendered_node_ids=result.rendered_node_ids,
    )
    blockers = verify_diagram_render(tampered)
    assert any("SVG hash" in blocker for blocker in blockers)


def test_source_without_node_mapping_is_rejected():
    with pytest.raises(DomainError) as exc_info:
        _source(node_component_ids=())
    assert exc_info.value.error_code == "DIAGRAM_INVALID"


def test_unparseable_source_line_is_rejected():
    source = _source(source_text='node n1 "A"\nlink n1 n2\n')
    with pytest.raises(DomainError) as exc_info:
        render_diagram_source(source, node_component_mapping={"n1": "comp-1"})
    assert exc_info.value.error_code == "DIAGRAM_SOURCE_INVALID"
