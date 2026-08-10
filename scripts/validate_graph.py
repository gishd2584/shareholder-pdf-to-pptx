#!/usr/bin/env python3
"""Validate ownership graph JSON before creating a PowerPoint diagram."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PERCENT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def warning(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_json", type=Path)
    args = parser.parse_args()

    try:
        graph = json.loads(args.graph_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read graph JSON: {exc}") from exc

    errors = 0
    if not isinstance(graph, dict):
        error("root value must be an object")
        raise SystemExit(1)
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not nodes:
        error("nodes must be a non-empty array")
        errors += 1
        nodes = []
    if not isinstance(edges, list):
        error("edges must be an array")
        errors += 1
        edges = []

    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            error(f"nodes[{index}] must be an object")
            errors += 1
            continue
        node_id = node.get("id")
        label = node.get("label")
        if not isinstance(node_id, str) or not node_id.strip():
            error(f"nodes[{index}].id must be a non-empty string")
            errors += 1
        elif node_id in node_ids:
            error(f"duplicate node id: {node_id}")
            errors += 1
        else:
            node_ids.add(node_id)
        if not isinstance(label, str) or not label.strip():
            error(f"nodes[{index}].label must be a non-empty string")
            errors += 1

    holdings: defaultdict[str, list[float]] = defaultdict(list)
    seen_edges: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            error(f"edges[{index}] must be an object")
            errors += 1
            continue
        source, target = edge.get("from"), edge.get("to")
        if source not in node_ids:
            error(f"edges[{index}].from references unknown node: {source!r}")
            errors += 1
        if target not in node_ids:
            error(f"edges[{index}].to references unknown node: {target!r}")
            errors += 1
        if source == target and source in node_ids:
            error(f"edges[{index}] cannot connect a node to itself: {source}")
            errors += 1
        holding = edge.get("holding")
        if holding is not None and not isinstance(holding, str):
            error(f"edges[{index}].holding must be a string")
            errors += 1
        if isinstance(holding, str):
            matched = PERCENT.match(holding)
            if matched:
                holdings[str(target)].append(float(matched.group(1)))
        key = (str(source), str(target), str(holding or ""))
        if key in seen_edges:
            warning(f"duplicate relationship: {source} -> {target} ({holding or 'no label'})")
        seen_edges.add(key)

    for target, values in sorted(holdings.items()):
        total = sum(values)
        if len(values) > 1 and abs(total - 100) > 0.2:
            warning(f"numeric direct holdings for {target} sum to {total:.4g}%, not 100%")

    if errors:
        raise SystemExit(1)
    print(f"Valid graph: {len(node_ids)} nodes, {len(edges)} ownership relationships")


if __name__ == "__main__":
    main()
