import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

Edge = Tuple[str, str, float]
EdgePair = Tuple[str, str]


@dataclass
class MstStep:
    index: int
    edge: Optional[EdgePair]
    weight: float
    action: str
    reason: str
    running_weight: float
    chosen_edges: List[EdgePair]


@dataclass
class FailureFrame:
    step: int
    action: str
    target: str
    graph: nx.Graph
    connected: bool
    components_count: int
    island_sizes: List[int]
    bridges_count: int
    articulation_count: int


def normalize_edge(u: str, v: str) -> EdgePair:
    return tuple(sorted((u, v)))


def build_graph(edges: List[Edge]) -> nx.Graph:
    graph = nx.Graph()
    for u, v, w in edges:
        graph.add_edge(u, v, weight=w)
    return graph


def compute_redundancy_recommendations(graph: nx.Graph, bridges: List[EdgePair]) -> List[EdgePair]:
    """Suggest candidate links to create alternate paths across bridge cuts."""
    recommendations: Set[EdgePair] = set()

    for u, v in bridges:
        if not graph.has_edge(u, v):
            continue

        temp = graph.copy()
        temp.remove_edge(u, v)
        components = list(nx.connected_components(temp))
        if len(components) < 2:
            continue

        comp_a = next((c for c in components if u in c), None)
        comp_b = next((c for c in components if v in c), None)
        if not comp_a or not comp_b or comp_a == comp_b:
            continue

        cand_a = max(comp_a, key=lambda n: (temp.degree(n), n))
        cand_b = max(comp_b, key=lambda n: (temp.degree(n), n))

        if cand_a != cand_b and not graph.has_edge(cand_a, cand_b):
            recommendations.add(normalize_edge(cand_a, cand_b))

    return sorted(recommendations)


def calculate_resilience_metrics(graph: nx.Graph) -> Dict[str, float]:
    if graph.number_of_nodes() == 0:
        return {
            "node_count": 0.0,
            "edge_count": 0.0,
            "components": 0.0,
            "largest_component_ratio": 0.0,
            "global_efficiency": 0.0,
            "node_connectivity": 0.0,
            "edge_connectivity": 0.0,
            "density": 0.0,
            "avg_clustering": 0.0,
            "avg_shortest_path_lcc": 0.0,
        }

    components = list(nx.connected_components(graph))
    largest_component = max(components, key=len)
    lcc = graph.subgraph(largest_component).copy()

    if lcc.number_of_nodes() > 1:
        avg_shortest_path = float(nx.average_shortest_path_length(lcc, weight=None))
    else:
        avg_shortest_path = 0.0

    node_connectivity = float(nx.node_connectivity(graph)) if graph.number_of_nodes() > 1 else 0.0
    edge_connectivity = float(nx.edge_connectivity(graph)) if graph.number_of_nodes() > 1 else 0.0

    return {
        "node_count": float(graph.number_of_nodes()),
        "edge_count": float(graph.number_of_edges()),
        "components": float(len(components)),
        "largest_component_ratio": float(len(largest_component) / graph.number_of_nodes()),
        "global_efficiency": float(nx.global_efficiency(graph)),
        "node_connectivity": node_connectivity,
        "edge_connectivity": edge_connectivity,
        "density": float(nx.density(graph)),
        "avg_clustering": float(nx.average_clustering(graph)),
        "avg_shortest_path_lcc": avg_shortest_path,
    }


def explain_bridges(graph: nx.Graph, bridges: List[EdgePair]) -> List[Dict[str, object]]:
    details: List[Dict[str, object]] = []
    base_components = nx.number_connected_components(graph)

    for edge in bridges:
        u, v = edge
        temp = graph.copy()
        temp.remove_edge(u, v)
        comps = list(nx.connected_components(temp))
        sizes = sorted([len(c) for c in comps], reverse=True)

        details.append(
            {
                "edge": edge,
                "components_before": base_components,
                "components_after": len(comps),
                "island_sizes": sizes,
                "reason": (
                    f"Removing edge {u}-{v} increases connected components from "
                    f"{base_components} to {len(comps)}. That means every path between "
                    "the resulting islands must traverse this edge."
                ),
            }
        )

    return details


def explain_articulation_points(graph: nx.Graph, points: List[str]) -> List[Dict[str, object]]:
    details: List[Dict[str, object]] = []
    base_components = nx.number_connected_components(graph)

    for node in points:
        temp = graph.copy()
        temp.remove_node(node)
        if temp.number_of_nodes() == 0:
            comps: List[Set[str]] = []
        else:
            comps = list(nx.connected_components(temp))

        sizes = sorted([len(c) for c in comps], reverse=True)
        details.append(
            {
                "node": node,
                "components_before": base_components,
                "components_after": len(comps),
                "island_sizes": sizes,
                "reason": (
                    f"Removing node {node} disconnects parts of the network "
                    f"(components {base_components} -> {len(comps)}). "
                    "This node acts as a structural junction in the DFS tree."
                ),
            }
        )

    return details


def kruskal_trace(graph: nx.Graph) -> List[MstStep]:
    parent: Dict[str, str] = {n: n for n in graph.nodes()}
    rank: Dict[str, int] = {n: 0 for n in graph.nodes()}

    def find(x: str) -> str:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> bool:
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            return False

        if rank[root_a] < rank[root_b]:
            parent[root_a] = root_b
        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a
        else:
            parent[root_b] = root_a
            rank[root_a] += 1
        return True

    edges = sorted(
        ((data.get("weight", 1.0), u, v) for u, v, data in graph.edges(data=True)),
        key=lambda x: (x[0], min(x[1], x[2]), max(x[1], x[2])),
    )

    chosen: List[EdgePair] = []
    running_weight = 0.0
    steps: List[MstStep] = []

    for idx, (weight, u, v) in enumerate(edges, start=1):
        edge_pair = normalize_edge(u, v)
        if union(u, v):
            chosen.append(edge_pair)
            running_weight += weight
            steps.append(
                MstStep(
                    index=idx,
                    edge=edge_pair,
                    weight=weight,
                    action="accept",
                    reason="Edge connects two different components; safe to add.",
                    running_weight=running_weight,
                    chosen_edges=chosen.copy(),
                )
            )
        else:
            steps.append(
                MstStep(
                    index=idx,
                    edge=edge_pair,
                    weight=weight,
                    action="reject",
                    reason="Edge would create a cycle in the current forest.",
                    running_weight=running_weight,
                    chosen_edges=chosen.copy(),
                )
            )

    return steps


def prim_trace(graph: nx.Graph) -> List[MstStep]:
    if graph.number_of_nodes() == 0:
        return []

    steps: List[MstStep] = []
    chosen: List[EdgePair] = []
    running_weight = 0.0
    step_index = 0

    visited_global: Set[str] = set()

    for start in sorted(graph.nodes()):
        if start in visited_global:
            continue

        visited_component: Set[str] = {start}
        visited_global.add(start)

        step_index += 1
        steps.append(
            MstStep(
                index=step_index,
                edge=None,
                weight=0.0,
                action="start",
                reason=f"Start Prim expansion from node {start}.",
                running_weight=running_weight,
                chosen_edges=chosen.copy(),
            )
        )

        while True:
            frontier: List[Tuple[float, str, str]] = []
            for u in visited_component:
                for v, attrs in graph[u].items():
                    if v not in visited_component:
                        frontier.append((attrs.get("weight", 1.0), u, v))

            if not frontier:
                break

            weight, u, v = min(frontier, key=lambda x: (x[0], min(x[1], x[2]), max(x[1], x[2])))
            edge_pair = normalize_edge(u, v)

            if edge_pair in chosen:
                break

            visited_component.add(v)
            visited_global.add(v)
            chosen.append(edge_pair)
            running_weight += weight

            step_index += 1
            steps.append(
                MstStep(
                    index=step_index,
                    edge=edge_pair,
                    weight=weight,
                    action="accept",
                    reason="Minimum-weight frontier edge selected by Prim.",
                    running_weight=running_weight,
                    chosen_edges=chosen.copy(),
                )
            )

    return steps


def analyze_graph(graph: nx.Graph, mst_algorithm: str) -> Dict[str, object]:
    articulation_points = set(nx.articulation_points(graph)) if graph.number_of_nodes() > 1 else set()
    bridges = {normalize_edge(u, v) for u, v in nx.bridges(graph)} if graph.number_of_edges() > 0 else set()

    mst = nx.minimum_spanning_tree(graph, algorithm=mst_algorithm, weight="weight")
    mst_edges = {normalize_edge(u, v) for u, v in mst.edges()}
    mst_weight = mst.size(weight="weight")

    recommendations = compute_redundancy_recommendations(graph, sorted(bridges))
    bridge_details = explain_bridges(graph, sorted(bridges))
    articulation_details = explain_articulation_points(graph, sorted(articulation_points))

    mst_steps = kruskal_trace(graph) if mst_algorithm == "kruskal" else prim_trace(graph)
    resilience_metrics = calculate_resilience_metrics(graph)

    return {
        "articulation_points": articulation_points,
        "bridges": bridges,
        "mst_edges": mst_edges,
        "mst_weight": mst_weight,
        "recommendations": recommendations,
        "bridge_details": bridge_details,
        "articulation_details": articulation_details,
        "mst_steps": mst_steps,
        "resilience_metrics": resilience_metrics,
    }


def simulate_failure(graph: nx.Graph, mode: str, target: object) -> Dict[str, object]:
    sim_graph = graph.copy()

    if mode == "Node":
        node = str(target)
        if not sim_graph.has_node(node):
            return {
                "graph": sim_graph,
                "connected": nx.is_connected(sim_graph) if sim_graph.number_of_nodes() > 0 else False,
                "components": [sorted(c) for c in nx.connected_components(sim_graph)] if sim_graph.number_of_nodes() > 0 else [],
                "message": f"Node {node} was not found. No failure simulated.",
            }
        sim_graph.remove_node(node)
        removed_label = node
        removed_kind = "node"
    elif mode == "Edge":
        u, v = target  # type: ignore[misc]
        if not sim_graph.has_edge(u, v):
            return {
                "graph": sim_graph,
                "connected": nx.is_connected(sim_graph) if sim_graph.number_of_nodes() > 0 else False,
                "components": [sorted(c) for c in nx.connected_components(sim_graph)] if sim_graph.number_of_nodes() > 0 else [],
                "message": f"Edge {u}-{v} was not found. No failure simulated.",
            }
        sim_graph.remove_edge(u, v)
        removed_label = f"{u}-{v}"
        removed_kind = "edge"
    else:
        return {
            "graph": sim_graph,
            "connected": nx.is_connected(sim_graph) if sim_graph.number_of_nodes() > 0 else False,
            "components": [sorted(c) for c in nx.connected_components(sim_graph)] if sim_graph.number_of_nodes() > 0 else [],
            "message": "No failure simulated.",
        }

    if sim_graph.number_of_nodes() == 0:
        message = f"Removed {removed_kind} {removed_label}. No active network remains."
        connected = False
        components: List[List[str]] = []
    elif nx.is_connected(sim_graph):
        message = f"Removed {removed_kind} {removed_label}. Network remains connected."
        connected = True
        components = [sorted(c) for c in nx.connected_components(sim_graph)]
    else:
        connected = False
        components = [sorted(c) for c in nx.connected_components(sim_graph)]
        message = (
            f"Removed {removed_kind} {removed_label}. "
            f"Network split into {len(components)} islands."
        )

    return {
        "graph": sim_graph,
        "connected": connected,
        "components": components,
        "message": message,
    }


def _build_failure_frame(step: int, action: str, target: str, frame_graph: nx.Graph) -> FailureFrame:
    if frame_graph.number_of_nodes() == 0:
        connected = False
        components_count = 0
        island_sizes: List[int] = []
        bridges_count = 0
        articulation_count = 0
    else:
        connected = nx.is_connected(frame_graph)
        components = list(nx.connected_components(frame_graph))
        components_count = len(components)
        island_sizes = sorted([len(c) for c in components], reverse=True)
        bridges_count = len(list(nx.bridges(frame_graph))) if frame_graph.number_of_edges() > 0 else 0
        articulation_count = len(list(nx.articulation_points(frame_graph))) if frame_graph.number_of_nodes() > 1 else 0

    return FailureFrame(
        step=step,
        action=action,
        target=target,
        graph=frame_graph.copy(),
        connected=connected,
        components_count=components_count,
        island_sizes=island_sizes,
        bridges_count=bridges_count,
        articulation_count=articulation_count,
    )


def simulate_failure_campaign(
    graph: nx.Graph,
    nodes_to_remove: List[str],
    edges_to_remove: List[EdgePair],
) -> List[FailureFrame]:
    """Apply multiple node/edge removals sequentially and return frame-by-frame impact."""
    working = graph.copy()
    frames: List[FailureFrame] = [_build_failure_frame(0, "baseline", "none", working)]
    step = 1

    for node in nodes_to_remove:
        if working.has_node(node):
            working.remove_node(node)
            frames.append(_build_failure_frame(step, "remove-node", node, working))
            step += 1

    for edge in edges_to_remove:
        u, v = edge
        if working.has_edge(u, v):
            working.remove_edge(u, v)
            frames.append(_build_failure_frame(step, "remove-edge", f"{u}-{v}", working))
            step += 1

    return frames


def simulate_bridge_shockwave(graph: nx.Graph, max_steps: int, use_weights: bool = True) -> List[FailureFrame]:
    """
    Repeatedly remove the most fragile edge:
    prioritize current bridges; if none, remove edge with highest edge-betweenness.
    """
    working = graph.copy()
    frames: List[FailureFrame] = [_build_failure_frame(0, "baseline", "none", working)]

    for step in range(1, max_steps + 1):
        if working.number_of_edges() == 0 or working.number_of_nodes() == 0:
            break

        bridge_edges = [normalize_edge(u, v) for u, v in nx.bridges(working)]

        if bridge_edges:
            target = sorted(bridge_edges)[0]
            reason = "bridge"
        else:
            ebc = nx.edge_betweenness_centrality(
                working,
                normalized=True,
                weight="weight" if use_weights else None,
            )
            (u, v), _ = max(ebc.items(), key=lambda kv: kv[1])
            target = normalize_edge(u, v)
            reason = "high-betweenness-weighted" if use_weights else "high-betweenness"

        if not working.has_edge(target[0], target[1]):
            break

        working.remove_edge(target[0], target[1])
        frames.append(
            _build_failure_frame(step, f"shockwave-{reason}", f"{target[0]}-{target[1]}", working)
        )

    return frames


def simulate_random_failures(
    graph: nx.Graph,
    trials: int,
    max_steps: int,
    mode: str = "edge",
    seed: int = 42,
) -> List[Dict[str, float]]:
    """Run Monte Carlo failure experiments and return stepwise resilience statistics."""
    if trials <= 0 or max_steps <= 0 or graph.number_of_nodes() == 0:
        return []

    rng = random.Random(seed)
    per_step_components: Dict[int, List[int]] = {s: [] for s in range(1, max_steps + 1)}
    per_step_lcc_ratio: Dict[int, List[float]] = {s: [] for s in range(1, max_steps + 1)}
    per_step_disconnects: Dict[int, int] = {s: 0 for s in range(1, max_steps + 1)}

    for _ in range(trials):
        working = graph.copy()

        if mode == "node":
            candidates = list(working.nodes())
        else:
            candidates = [normalize_edge(u, v) for u, v in working.edges()]

        rng.shuffle(candidates)

        for step in range(1, max_steps + 1):
            if mode == "node":
                if not candidates:
                    break
                target = candidates.pop()
                if working.has_node(str(target)):
                    working.remove_node(str(target))
            else:
                if not candidates:
                    break
                u, v = candidates.pop()
                if working.has_edge(u, v):
                    working.remove_edge(u, v)

            if working.number_of_nodes() == 0:
                comps_count = 0
                lcc_ratio = 0.0
                disconnected = True
            else:
                comps = list(nx.connected_components(working))
                comps_count = len(comps)
                lcc_size = len(max(comps, key=len)) if comps else 0
                lcc_ratio = lcc_size / working.number_of_nodes() if working.number_of_nodes() > 0 else 0.0
                disconnected = comps_count > 1

            per_step_components[step].append(comps_count)
            per_step_lcc_ratio[step].append(lcc_ratio)
            if disconnected:
                per_step_disconnects[step] += 1

    summary: List[Dict[str, float]] = []
    for step in range(1, max_steps + 1):
        comp_values = per_step_components[step]
        lcc_values = per_step_lcc_ratio[step]
        if not comp_values:
            continue

        summary.append(
            {
                "step": float(step),
                "disconnect_probability": float(per_step_disconnects[step] / len(comp_values)),
                "avg_components": float(sum(comp_values) / len(comp_values)),
                "avg_lcc_ratio": float(sum(lcc_values) / len(lcc_values)),
            }
        )

    return summary
