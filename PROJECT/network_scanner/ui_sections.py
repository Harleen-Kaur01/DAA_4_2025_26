from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

from network_scanner.algorithms import EdgePair, MstStep
from network_scanner.visualization import format_edge


def build_live_snapshot(
    graph_nodes: Set[str],
    edge_weights: Dict[EdgePair, float],
    components_count: int,
    bridges: Set[EdgePair],
    articulation_points: Set[str],
    mst_weight: float,
) -> Dict[str, object]:
    return {
        "nodes": set(graph_nodes),
        "edge_weights": dict(edge_weights),
        "components_count": components_count,
        "bridges": set(bridges),
        "articulation_points": set(articulation_points),
        "mst_weight": mst_weight,
    }


def render_live_change_explanation(
    previous: Optional[Dict[str, object]],
    current: Dict[str, object],
) -> None:
    st.subheader("Live Change Explanation")

    if previous is None:
        st.info(
            "Baseline established. Start editing edges/weights and this panel will explain the impact in real time."
        )
        return

    prev_nodes = previous["nodes"]
    curr_nodes = current["nodes"]
    prev_edge_weights = previous["edge_weights"]
    curr_edge_weights = current["edge_weights"]

    prev_edges = set(prev_edge_weights.keys())
    curr_edges = set(curr_edge_weights.keys())

    added_nodes = sorted(curr_nodes - prev_nodes)
    removed_nodes = sorted(prev_nodes - curr_nodes)
    added_edges = sorted(curr_edges - prev_edges)
    removed_edges = sorted(prev_edges - curr_edges)

    changed_weight_edges: List[Tuple[EdgePair, float, float]] = []
    for edge in sorted(prev_edges.intersection(curr_edges)):
        old_w = float(prev_edge_weights[edge])
        new_w = float(curr_edge_weights[edge])
        if old_w != new_w:
            changed_weight_edges.append((edge, old_w, new_w))

    delta_components = int(current["components_count"]) - int(previous["components_count"])
    delta_bridges = len(current["bridges"]) - len(previous["bridges"])
    delta_articulation = len(current["articulation_points"]) - len(previous["articulation_points"])
    delta_mst = float(current["mst_weight"]) - float(previous["mst_weight"])

    if (
        not added_nodes
        and not removed_nodes
        and not added_edges
        and not removed_edges
        and not changed_weight_edges
    ):
        st.success("No structural change detected compared to your previous edit.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Delta Components", f"{delta_components:+d}")
    with c2:
        st.metric("Delta Bridges", f"{delta_bridges:+d}")
    with c3:
        st.metric("Delta Articulation", f"{delta_articulation:+d}")
    with c4:
        st.metric("Delta MST Weight", f"{delta_mst:+.2f}")

    st.markdown("**Edit Diff**")
    if added_nodes:
        st.write("Added Nodes:", ", ".join(added_nodes))
    if removed_nodes:
        st.write("Removed Nodes:", ", ".join(removed_nodes))
    if added_edges:
        st.write("Added Edges:", ", ".join(format_edge(e) for e in added_edges))
    if removed_edges:
        st.write("Removed Edges:", ", ".join(format_edge(e) for e in removed_edges))
    if changed_weight_edges:
        st.write(
            "Weight Changes:",
            "; ".join(f"{format_edge(e)}: {old:g} -> {new:g}" for e, old, new in changed_weight_edges),
        )

    st.markdown("**Impact Interpretation**")
    insights: List[str] = []

    if delta_components > 0:
        insights.append(
            "Connectivity degraded: number of connected components increased, indicating more isolated islands."
        )
    elif delta_components < 0:
        insights.append(
            "Connectivity improved: connected components decreased, indicating islands merged into a more robust network."
        )

    if delta_bridges > 0:
        insights.append(
            "Single-link failure risk increased: more bridges mean more edges whose failure disconnects the network."
        )
    elif delta_bridges < 0:
        insights.append(
            "Single-link resilience improved: fewer bridges means more alternate routing cycles exist."
        )

    if delta_articulation > 0:
        insights.append(
            "Single-node failure risk increased: more articulation points means more critical junction nodes."
        )
    elif delta_articulation < 0:
        insights.append(
            "Node-level resilience improved: fewer articulation points means less dependency on single junction nodes."
        )

    if delta_mst > 0:
        insights.append(
            "Backbone efficiency degraded: MST total cost increased, implying heavier minimal infrastructure after your edit."
        )
    elif delta_mst < 0:
        insights.append(
            "Backbone efficiency improved: MST total cost dropped, implying a cheaper minimal connectivity structure."
        )

    new_bridges = sorted(current["bridges"] - previous["bridges"])
    removed_bridges = sorted(previous["bridges"] - current["bridges"])
    new_aps = sorted(current["articulation_points"] - previous["articulation_points"])
    removed_aps = sorted(previous["articulation_points"] - current["articulation_points"])

    if new_bridges:
        insights.append("Newly created bridge edges: " + ", ".join(format_edge(e) for e in new_bridges))
    if removed_bridges:
        insights.append("Bridges eliminated: " + ", ".join(format_edge(e) for e in removed_bridges))
    if new_aps:
        insights.append("New articulation points: " + ", ".join(new_aps))
    if removed_aps:
        insights.append("Articulation points removed: " + ", ".join(removed_aps))

    if not insights:
        insights.append("Changes affected structure but did not significantly alter criticality indicators.")

    for insight in insights:
        st.markdown(f"- {insight}")


def render_algorithm_theory() -> None:
    st.subheader("Algorithm Theory and Structural Interpretation")

    left, right = st.columns(2)

    with left:
        st.markdown(
            """
            <div class="explain-card">
                <b>What the scanner is really doing</b><br>
                It is looking for <i>single points of failure</i> and the cheapest backbone that still keeps the network connected.
                Think of the network as a city map: if one road or junction disappears, does the city split into isolated districts?
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="explain-card">
                <b>How to read the output</b><br>
                <span class="pill pill-danger">Red nodes</span> are critical junctions.<br>
                <span class="pill pill-info">Orange dashed edges</span> are fragile links.<br>
                <span class="pill pill-success">Cyan edges</span> are the minimum-cost backbone.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 1. Tarjan DFS: why a node or edge becomes critical")
    st.markdown(
        """
        Tarjan’s DFS is the engine behind bridge and articulation detection. The algorithm assigns every node two values:

        - `disc[u]`: when node `u` was first discovered
        - `low[u]`: the earliest discovery time reachable from `u` or any node below it in the DFS tree

        The intuition is simple: if a subtree cannot reach an ancestor by using a back-edge, then the parent edge is structurally fragile.
        
        **Bridge rule**

        $$low[v] > disc[u]$$

        If a child subtree rooted at `v` cannot reach `u` or anything above `u`, then edge `(u, v)` is a bridge.

        **Articulation rule**

        $$low[v] \\ge disc[u]$$

        If removing `u` separates child subtree `v` from the rest of the graph, then `u` is an articulation point.

        In practical terms: a bridge is a vulnerable wire; an articulation point is a vulnerable junction.
        """
    )

    st.markdown("### 2. MST: how the app builds the cheapest resilient backbone")
    st.markdown(
        """
        The Minimum Spanning Tree gives the lightest set of edges that still keeps each connected component reachable.

        - **Kruskal** behaves like a careful contractor: it sorts roads by cost and keeps the next cheapest one only if it does not create a loop.
        - **Prim** behaves like an expanding frontier: it starts from one location and always chooses the cheapest outgoing road from the current network.

        Both rely on the **cut property**: the cheapest edge across a cut is safe to choose.

        Why this matters here:
        - the MST is the “minimum-cost survival skeleton” of the graph
        - any edge outside the MST may still be important, but it is not required for the cheapest connected backbone
        - if the MST cost rises after your change, the network became more expensive to keep connected
        - if the graph is disconnected, the result is a minimum spanning forest across all islands
        """
    )

    st.markdown("### 3. Reliability meaning in the real world")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="explain-card">
                <b>Bridge</b><br>
                One failure can split the system into islands.<br>
                Example: a lone transmission line between two regions.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="explain-card">
                <b>Articulation Point</b><br>
                One node can disconnect several regions at once.<br>
                Example: a central router or substation.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="explain-card">
                <b>Reinforcement</b><br>
                Add a redundant link to turn a fragile chain into a cycle.<br>
                Cycles create alternate routes and improve resilience.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Why the app highlights certain nodes and edges", expanded=False):
        st.markdown(
            """
            - A red node appears when removing it increases the number of connected components.
            - An orange dashed edge appears when removing it breaks the only path between two regions.
            - A cyan edge appears when it belongs to the MST backbone.
            - When you edit the network live, the app compares the new structure with the previous state and explains what became more fragile or more stable.
            """
        )


def render_critical_reasoning(bridge_details: List[Dict[str, object]], articulation_details: List[Dict[str, object]]) -> None:
    st.subheader("Why Each Critical Element Appears")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Bridge Diagnostics")
        if not bridge_details:
            st.success("No bridges found. Every edge has an alternate route.")
        else:
            bridge_df = pd.DataFrame(
                [
                    {
                        "Bridge": format_edge(item["edge"]),
                        "Components Before": item["components_before"],
                        "Components After": item["components_after"],
                        "Island Sizes": item["island_sizes"],
                    }
                    for item in bridge_details
                ]
            )
            st.dataframe(bridge_df, use_container_width=True, hide_index=True)
            for item in bridge_details:
                st.markdown(f"- {item['reason']}")

    with right:
        st.markdown("#### Articulation Diagnostics")
        if not articulation_details:
            st.success("No articulation points found. No single node disconnects the network.")
        else:
            art_df = pd.DataFrame(
                [
                    {
                        "Node": item["node"],
                        "Components Before": item["components_before"],
                        "Components After": item["components_after"],
                        "Island Sizes": item["island_sizes"],
                    }
                    for item in articulation_details
                ]
            )
            st.dataframe(art_df, use_container_width=True, hide_index=True)
            for item in articulation_details:
                st.markdown(f"- {item['reason']}")


def render_mst_table(mst_steps: List[MstStep]) -> None:
    st.subheader("MST Decision Trace")
    if not mst_steps:
        st.info("No MST trace available.")
        return

    df = pd.DataFrame(
        [
            {
                "Step": step.index,
                "Edge": "None" if step.edge is None else format_edge(step.edge),
                "Weight": step.weight,
                "Action": step.action,
                "Running Cost": step.running_weight,
                "Reason": step.reason,
            }
            for step in mst_steps
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_reinforcement_report(recommendations: List[EdgePair], bridge_count: int) -> None:
    st.subheader("Reinforcement Report")
    if recommendations:
        st.success("Suggested redundant links to reduce bridge-driven vulnerability:")
        for idx, (u, v) in enumerate(recommendations, start=1):
            st.write(f"{idx}. Add link: **{u} - {v}**")
    elif bridge_count > 0:
        st.warning("Bridges exist, but no safe automatic reinforcement candidate was inferred.")
    else:
        st.success("No bridges detected. Current topology already has edge-level redundancy.")
