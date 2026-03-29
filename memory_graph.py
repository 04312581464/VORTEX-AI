from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GraphNode:
    id: str
    label: str
    type: str = "concept"
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)


@dataclass
class GraphEdge:
    src: str
    dst: str
    rel: str
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)


class MemoryGraph:
    """
    Simple local knowledge graph (nodes + relationships) persisted in JSON.
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {"nodes": {}, "edges": []}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
            if "nodes" not in self._data or "edges" not in self._data:
                self._data = {"nodes": {}, "edges": []}
        except Exception:
            self._data = {"nodes": {}, "edges": []}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert_node(self, node_id: str, label: str, type_: str = "concept", **props: Any) -> GraphNode:
        existing = self._data["nodes"].get(node_id)
        if existing:
            existing["label"] = label
            existing["type"] = type_
            existing.setdefault("props", {})
            existing["props"].update(props)
            self._save()
            return GraphNode(
                id=node_id,
                label=existing["label"],
                type=existing.get("type", "concept"),
                props=dict(existing.get("props") or {}),
                created_at=existing.get("created_at", _now_iso()),
            )
        node = GraphNode(id=node_id, label=label, type=type_, props=dict(props))
        self._data["nodes"][node_id] = node.__dict__
        self._save()
        return node

    def link(self, src: str, dst: str, rel: str, **props: Any) -> GraphEdge:
        edge = GraphEdge(src=src, dst=dst, rel=rel, props=dict(props))
        self._data["edges"].append(edge.__dict__)
        self._save()
        return edge

    def neighbors(self, node_id: str, rel: Optional[str] = None) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for e in self._data.get("edges", []):
            if e.get("src") != node_id:
                continue
            if rel and e.get("rel") != rel:
                continue
            out.append((str(e.get("dst")), str(e.get("rel"))))
        return out

    def search_nodes(self, query: str, limit: int = 10) -> List[GraphNode]:
        q = query.lower().strip()
        hits: List[GraphNode] = []
        for nid, n in (self._data.get("nodes") or {}).items():
            label = str(n.get("label", ""))
            if q in label.lower() or q in str(nid).lower():
                hits.append(
                    GraphNode(
                        id=str(nid),
                        label=label,
                        type=str(n.get("type", "concept")),
                        props=dict(n.get("props") or {}),
                        created_at=str(n.get("created_at", "")),
                    )
                )
        return hits[:limit]

