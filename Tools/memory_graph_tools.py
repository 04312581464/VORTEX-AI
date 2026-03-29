from __future__ import annotations

from livekit.agents import function_tool


# Set by agent.py at runtime
MEMORY_GRAPH = None


def set_memory_graph(graph) -> None:
    global MEMORY_GRAPH
    MEMORY_GRAPH = graph


@function_tool()
async def graph_upsert_node(node_id: str, label: str, type_: str = "concept") -> str:
    """
    Upsert a node in the Memory Graph.
    Example: node_id="python", label="Python", type_="skill"
    """
    if MEMORY_GRAPH is None:
        return "Memory graph is not initialized."
    n = MEMORY_GRAPH.upsert_node(node_id=node_id, label=label, type_=type_)
    return f"✅ Node saved: {n.id} ({n.type})"


@function_tool()
async def graph_link(src: str, dst: str, rel: str) -> str:
    """
    Create a relationship edge in the Memory Graph.
    Example: src="python" dst="proj_vortex" rel="USED_IN"
    """
    if MEMORY_GRAPH is None:
        return "Memory graph is not initialized."
    e = MEMORY_GRAPH.link(src=src, dst=dst, rel=rel)
    return f"✅ Linked: {e.src} -[{e.rel}]-> {e.dst}"


@function_tool()
async def graph_search(query: str) -> str:
    """
    Search nodes by id/label.
    """
    if MEMORY_GRAPH is None:
        return "Memory graph is not initialized."
    hits = MEMORY_GRAPH.search_nodes(query)
    if not hits:
        return "No matches."
    lines = ["Matches:"]
    for h in hits:
        lines.append(f"- {h.id} ({h.type}): {h.label}")
    return "\n".join(lines)


@function_tool()
async def graph_neighbors(node_id: str, rel: str = "") -> str:
    """
    Show outgoing neighbors of a node (optionally filtered by rel).
    """
    if MEMORY_GRAPH is None:
        return "Memory graph is not initialized."
    r = rel.strip() or None
    nbrs = MEMORY_GRAPH.neighbors(node_id, rel=r)
    if not nbrs:
        return "No linked nodes."
    lines = [f"Neighbors of {node_id}:"]
    for dst, rname in nbrs:
        lines.append(f"- -[{rname}]-> {dst}")
    return "\n".join(lines)

