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
    node_levels: dict[str, int] = {}
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
        level = node.get("level")
        if level is not None and (not isinstance(level, int) or level < 0):
            error(f"nodes[{index}].level must be a non-negative integer")
            errors += 1
        elif isinstance(node_id, str) and isinstance(level, int):
            node_levels[node_id] = level
        order = node.get("order")
        if order is not None and not isinstance(order, (int, float)):
            error(f"nodes[{index}].order must be numeric")
            errors += 1
        if node.get("shape") not in (None, "rect", "ellipse"):
            error(f"nodes[{index}].shape must be rect or ellipse")
            errors += 1
        if node.get("style") not in (None, "company", "person", "target"):
            error(f"nodes[{index}].style must be company, person, or target")
            errors += 1
        if "collapsed" in node and not isinstance(node.get("collapsed"), bool):
            error(f"nodes[{index}].collapsed must be true or false")
            errors += 1

    holdings: defaultdict[str, list[float]] = defaultdict(list)
    adjacency: defaultdict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in node_ids}
    connected: set[str] = set()
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
        if source in node_ids and target in node_ids and source != target:
            adjacency[source].append(target)
            indegree[target] += 1
            connected.update((source, target))
            if source in node_levels and target in node_levels:
                if node_levels[source] >= node_levels[target]:
                    error(
                        f"edges[{index}] must point downward: level {node_levels[source]} "
                        f"{source} -> level {node_levels[target]} {target}"
                    )
                    errors += 1
        key = (str(source), str(target), str(holding or ""))
        if key in seen_edges:
            warning(f"duplicate relationship: {source} -> {target} ({holding or 'no label'})")
        seen_edges.add(key)

    for target, values in sorted(holdings.items()):
        total = sum(values)
        if len(values) > 1 and abs(total - 100) > 0.2:
            warning(f"numeric direct holdings for {target} sum to {total:.4g}%, not 100%")

    if node_ids:
        stack = [node_id for node_id, degree in indegree.items() if degree == 0]
        visited = 0
        while stack:
            current = stack.pop()
            visited += 1
            for target in adjacency[current]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    stack.append(target)
        if visited != len(node_ids):
            error("ownership graph contains a cycle")
            errors += 1
        for node_id in sorted(node_ids - connected):
            warning(f"isolated node has no ownership relationship: {node_id}")

    if errors:
        raise SystemExit(1)
    level_count = len(set(node_levels.values())) if node_levels else "automatic"
    print(
        f"Valid graph: {len(node_ids)} nodes, {len(edges)} ownership relationships, "
        f"{level_count} explicit level(s)"
    )


if __name__ == "__main__":
    main()
