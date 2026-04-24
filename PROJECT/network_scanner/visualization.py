import time
from typing import Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from pyvis.network import Network
except ImportError:
    Network = None  # type: ignore[assignment]

from network_scanner.algorithms import EdgePair, FailureFrame, MstStep, analyze_graph


def _graph_signature(graph: nx.Graph) -> Tuple[Tuple[str, ...], Tuple[Tuple[str, str, float], ...]]:
    nodes = tuple(sorted(str(n) for n in graph.nodes()))
    weighted_edges = tuple(
        sorted(
            (
                min(str(u), str(v)),
                max(str(u), str(v)),
                float(data.get("weight", 1.0)),
            )
            for u, v, data in graph.edges(data=True)
        )
    )
    return nodes, weighted_edges


@st.cache_data(show_spinner=False)
def _cached_frame_analysis(
    nodes: Tuple[str, ...],
    weighted_edges: Tuple[Tuple[str, str, float], ...],
    mst_algorithm: str,
) -> Dict[str, object]:
    frame_graph = nx.Graph()
    frame_graph.add_nodes_from(nodes)
    for u, v, w in weighted_edges:
        frame_graph.add_edge(u, v, weight=w)
    return analyze_graph(frame_graph, mst_algorithm)


def apply_dark_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #000000;
            --bg-soft: #0a0d13;
            --card: #0d1117;
            --muted: #7a8390;
            --text: #c9d1d9;
            --accent: #1f6feb;
            --danger: #da3633;
            --warn: #d29922;
            --ok: #1a7f37;
        }

        .stApp {
            background: radial-gradient(circle at top left, #050810 0%, var(--bg) 50%, #000000 100%);
            color: var(--text);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(175deg, #000000 0%, #0d1117 50%, #000000 100%);
            border-right: 1px solid #1c2128;
        }

        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3,
        section[data-testid="stSidebar"] label {
            color: #b1bac4 !important;
        }

        h1, h2, h3, h4 {
            color: var(--text);
            letter-spacing: 0.3px;
        }

        .metric-card {
            background: linear-gradient(140deg, #0a0f17, var(--card));
            border: 1px solid #21262d;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.85rem;
            margin-bottom: 6px;
        }

        .metric-value {
            color: var(--text);
            font-size: 1.8rem;
            font-weight: 700;
            line-height: 1.1;
        }

        .pill {
            display: inline-block;
            border-radius: 999px;
            padding: 2px 10px;
            font-size: 0.78rem;
            margin-right: 6px;
            margin-bottom: 6px;
            border: 1px solid transparent;
        }

        .pill-danger {
            color: #f85149;
            background: rgba(218, 54, 51, 0.12);
            border-color: rgba(218, 54, 51, 0.25);
        }

        .pill-info {
            color: #79c0ff;
            background: rgba(31, 111, 235, 0.12);
            border-color: rgba(31, 111, 235, 0.25);
        }

        .pill-success {
            color: #3fb950;
            background: rgba(26, 127, 55, 0.12);
            border-color: rgba(26, 127, 55, 0.25);
        }

        .explain-card {
            background: #0a0f18;
            border: 1px solid #1c2128;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_edge(edge: EdgePair) -> str:
    return f"{edge[0]} - {edge[1]}"


def _edge_style(
    edge_key: EdgePair,
    bridges: Set[EdgePair],
    mst_edges: Set[EdgePair],
    active_mst_edges: Optional[Set[EdgePair]],
) -> Dict[str, object]:
    if edge_key in bridges:
        return {"color": "#f59e0b", "width": 3, "dashes": True}

    selected_mst = active_mst_edges if active_mst_edges is not None else mst_edges
    if edge_key in selected_mst:
        return {"color": "#22d3ee", "width": 3, "dashes": False}

    return {"color": "#94a3b8", "width": 2, "dashes": False}


def draw_graph_matplotlib(
    graph: nx.Graph,
    articulation_points: Set[str],
    bridges: Set[EdgePair],
    mst_edges: Set[EdgePair],
    title: str,
    pos: Optional[Dict[str, Tuple[float, float]]] = None,
    active_mst_edges: Optional[Set[EdgePair]] = None,
) -> None:
    if graph.number_of_nodes() == 0:
        st.warning("Graph is empty.")
        return

    if pos is None:
        pos = nx.spring_layout(graph, seed=42)

    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    fig.patch.set_alpha(0)
    ax.set_facecolor("#000000")

    non_ap_nodes = [n for n in graph.nodes if n not in articulation_points]
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=non_ap_nodes,
        node_color="#4da6ff",
        edgecolors="#66b3ff",
        node_size=760,
        linewidths=1.2,
        ax=ax,
    )

    if articulation_points:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=list(articulation_points),
            node_color="#ff4444",
            edgecolors="#ff6666",
            node_size=920,
            linewidths=1.7,
            ax=ax,
        )

    regular_edges = []
    bridge_edges = []
    mst_only_edges = []

    chosen_mst = active_mst_edges if active_mst_edges is not None else mst_edges

    for u, v in graph.edges:
        edge_key = tuple(sorted((u, v)))
        if edge_key in bridges:
            bridge_edges.append((u, v))
        elif edge_key in chosen_mst:
            mst_only_edges.append((u, v))
        else:
            regular_edges.append((u, v))

    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=regular_edges,
        width=1.8,
        edge_color="#94a3b8",
        style="solid",
        alpha=0.8,
        ax=ax,
    )

    if mst_only_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=mst_only_edges,
            width=3.0,
            edge_color="#22d3ee",
            style="solid",
            alpha=0.95,
            ax=ax,
        )

    if bridge_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=bridge_edges,
            width=3.0,
            edge_color="#f59e0b",
            style="dashed",
            alpha=1.0,
            ax=ax,
        )

    nx.draw_networkx_labels(graph, pos, font_size=10, font_color="#f8fafc", font_weight="bold", ax=ax)

    edge_labels = {(u, v): f"{data.get('weight', 1.0):g}" for u, v, data in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=9,
        font_color="#cbd5e1",
        label_pos=0.5,
        rotate=False,
        ax=ax,
    )

    ax.set_title(title, color="#e2e8f0", fontsize=14, pad=12)
    ax.axis("off")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def draw_graph_pyvis(
    graph: nx.Graph,
    articulation_points: Set[str],
    bridges: Set[EdgePair],
    mst_edges: Set[EdgePair],
    title: str,
    active_mst_edges: Optional[Set[EdgePair]] = None,
    height: int = 550,
) -> None:
    if graph.number_of_nodes() == 0:
        st.warning("Graph is empty.")
        return

    if Network is None:
        st.warning(
            "Pyvis is not installed in the active environment. Install with 'pip install pyvis' or switch to Matplotlib mode."
        )
        return

    st.markdown(f"### {title}")

    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#000000",
        font_color="#e2e8f0",
        notebook=False,
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.2, spring_length=130, spring_strength=0.012)

    for node in graph.nodes:
        is_ap = node in articulation_points
        net.add_node(
            node,
            label=node,
            color="#ff4444" if is_ap else "#4da6ff",
            borderWidth=2,
            size=26 if is_ap else 20,
            title=f"Node: {node}" + ("<br>Articulation Point" if is_ap else ""),
        )

    for u, v, data in graph.edges(data=True):
        edge_key = tuple(sorted((u, v)))
        style = _edge_style(edge_key, bridges, mst_edges, active_mst_edges)
        net.add_edge(
            u,
            v,
            label=str(data.get("weight", 1.0)),
            color=style["color"],
            width=style["width"],
            dashes=style["dashes"],
            title=(
                f"Edge: {u}-{v}<br>Weight: {data.get('weight', 1.0)}"
                + ("<br>Bridge" if edge_key in bridges else "")
                + ("<br>MST Edge" if edge_key in mst_edges else "")
            ),
        )

    html = net.generate_html(notebook=False)
    components.html(html, height=height + 10, scrolling=False)


def render_mst_animation(graph: nx.Graph, mst_steps: List[MstStep], bridges: Set[EdgePair], base_title: str) -> None:
    st.markdown("### MST Build Animation")
    if not mst_steps:
        st.info("No MST steps to animate.")
        return

    max_step = len(mst_steps)
    col_a, col_b = st.columns([1.5, 1])

    with col_b:
        selected_step = st.slider("Animation Step", min_value=1, max_value=max_step, value=max_step)
        auto_play = st.button("Play Animation", use_container_width=True)

    graph_pos = nx.spring_layout(graph, seed=42)
    frame_placeholder = col_a.empty()
    detail_placeholder = col_b.empty()

    def render_frame(step_idx: int) -> None:
        step = mst_steps[step_idx - 1]
        active_edges = set(step.chosen_edges)

        with frame_placeholder.container():
            draw_graph_matplotlib(
                graph,
                articulation_points=set(),
                bridges=bridges,
                mst_edges=active_edges,
                title=f"{base_title} | Step {step_idx}/{max_step}",
                pos=graph_pos,
                active_mst_edges=active_edges,
            )

        with detail_placeholder.container():
            edge_txt = "None" if step.edge is None else format_edge(step.edge)
            st.markdown(
                f"""
                <div class="explain-card">
                    <b>Action:</b> {step.action.upper()}<br>
                    <b>Edge:</b> {edge_txt}<br>
                    <b>Weight:</b> {step.weight:g}<br>
                    <b>Running MST Cost:</b> {step.running_weight:g}<br>
                    <b>Reason:</b> {step.reason}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if auto_play:
        for step_idx in range(1, max_step + 1):
            render_frame(step_idx)
            time.sleep(0.35)
    else:
        render_frame(selected_step)


def render_island_distribution(components_list: List[List[str]], title: str) -> None:
    st.markdown(f"### {title}")
    if not components_list:
        st.info("No components to display.")
        return

    df = pd.DataFrame(
        {
            "Island": [f"Island {i + 1}" for i in range(len(components_list))],
            "Size": [len(c) for c in components_list],
        }
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.bar_chart(df.set_index("Island"))


def render_failure_campaign_frame(
    frames: List[FailureFrame],
    frame_index: int,
    mst_algorithm: str,
    title: str,
) -> None:
    st.markdown(f"### {title}")
    if not frames:
        st.info("No campaign frames available.")
        return

    frame_index = max(0, min(frame_index, len(frames) - 1))
    frame = frames[frame_index]
    g = frame.graph

    graph_pos = nx.spring_layout(frames[0].graph, seed=42) if frames[0].graph.number_of_nodes() > 0 else {}
    c1, c2 = st.columns([1.6, 1])
    with c1:
        if g.number_of_nodes() > 0:
            signature = _graph_signature(g)
            analysis = _cached_frame_analysis(signature[0], signature[1], mst_algorithm)
            ap = analysis["articulation_points"]
            br = analysis["bridges"]
            mst_edges = analysis["mst_edges"]
            pos = {n: graph_pos[n] for n in g.nodes() if n in graph_pos}
            pos = pos if pos else None
        else:
            ap = set()
            br = set()
            mst_edges = set()
            pos = None

        draw_graph_matplotlib(
            g,
            articulation_points=ap,
            bridges=br,
            mst_edges=mst_edges,
            title=f"Campaign Frame {frame_index}/{len(frames)-1}",
            pos=pos,
        )

    with c2:
        st.markdown(
            f"""
            <div class="explain-card">
                <b>Action:</b> {frame.action}<br>
                <b>Target:</b> {frame.target}<br>
                <b>Connected:</b> {frame.connected}<br>
                <b>Components:</b> {frame.components_count}<br>
                <b>Island Sizes:</b> {frame.island_sizes}<br>
                <b>Bridges:</b> {frame.bridges_count}<br>
                <b>Articulation Points:</b> {frame.articulation_count}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_failure_campaign_controls(
    frames: List[FailureFrame],
    title: str,
) -> int:
    if not frames:
        return 0

    current_index = int(st.session_state.get(f"campaign_play_index_{title}", len(frames) - 1))
    current_index = max(0, min(current_index, len(frames) - 1))

    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        current_index = st.slider(
            "Frame",
            min_value=0,
            max_value=len(frames) - 1,
            value=current_index,
            key=f"campaign_frame_slider_{title}",
        )
        st.session_state[f"campaign_play_index_{title}"] = int(current_index)
    with c2:
        if st.button("Play Campaign", use_container_width=True, key=f"play_campaign_{title}"):
            st.session_state[f"campaign_playing_{title}"] = True
    with c3:
        if st.button("Pause Campaign", use_container_width=True, key=f"pause_campaign_{title}"):
            st.session_state[f"campaign_playing_{title}"] = False
    with c4:
        if st.button("Reset", use_container_width=True, key=f"reset_campaign_{title}"):
            st.session_state[f"campaign_play_index_{title}"] = 0

    return int(st.session_state.get(f"campaign_play_index_{title}", 0))


def render_campaign_timeline(frames: List[FailureFrame]) -> None:
    st.markdown("### Campaign Impact Timeline")
    if not frames:
        st.info("No timeline data available.")
        return

    df = pd.DataFrame(
        {
            "Step": [f.step for f in frames],
            "Components": [f.components_count for f in frames],
            "Bridges": [f.bridges_count for f in frames],
            "Articulation": [f.articulation_count for f in frames],
        }
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.line_chart(df.set_index("Step"))
