import time
from typing import List, Optional, Tuple

import networkx as nx
import pandas as pd
import streamlit as st

from network_scanner.algorithms import (
    analyze_graph,
    build_graph,
    normalize_edge,
    simulate_bridge_shockwave,
    simulate_failure,
    simulate_failure_campaign,
    simulate_random_failures,
)
from network_scanner.parsing import parse_edge_text, read_edges_from_csv
from network_scanner.ui_sections import (
    build_live_snapshot,
    render_algorithm_theory,
    render_critical_reasoning,
    render_live_change_explanation,
    render_mst_table,
    render_reinforcement_report,
)
from network_scanner.visualization import (
    apply_dark_theme,
    draw_graph_matplotlib,
    draw_graph_pyvis,
    format_edge,
    metric_card,
    render_campaign_timeline,
    render_failure_campaign_controls,
    render_failure_campaign_frame,
    render_island_distribution,
    render_mst_animation,
)


st.set_page_config(page_title="Network Reliability & Resilience Scanner", page_icon="🕸️", layout="wide")
apply_dark_theme()

st.title("Network Reliability & Resilience Scanner")
st.caption(
    "Advanced resilience analytics: articulation points, bridges, MST traceability, failure impact simulation, and reinforcement recommendations."
)

with st.sidebar:
    st.header("Control Center")
    st.caption("Edit topology, switch visual style, and run realistic failure campaigns.")

    with st.expander("Network Input", expanded=True):
        edge_text = st.text_area(
            "Edges (one per line)",
            value="A-B, 10\nB-C, 12\nC-D, 7\nB-D, 9\nD-E, 4\nE-F, 3\nC-F, 6\nA-G, 5\nG-H, 8\nH-C, 11",
            height=220,
            help="Format: Node1-Node2, weight",
        )
        uploaded_csv = st.file_uploader("Upload CSV source,target,weight", type=["csv"])

    with st.expander("Algorithm + Visual", expanded=True):
        mst_algorithm = st.selectbox("MST Algorithm", options=["kruskal", "prim"], index=0)
        viz_mode = st.selectbox("Primary Visualization", options=["Matplotlib", "Pyvis (Interactive)"], index=0)
        animation_speed = st.slider("Animation Speed (seconds/frame)", min_value=0.2, max_value=1.2, value=0.45, step=0.05)

    with st.expander("Campaign Simulator", expanded=True):
        campaign_mode = st.radio(
            "Campaign Type",
            options=["Manual Multi-Detach", "Bridge Shockwave", "Monte Carlo Random Failures"],
            horizontal=False,
        )
        shockwave_steps = st.slider("Shockwave Max Steps", min_value=1, max_value=15, value=6)
        shockwave_weighted = st.checkbox("Use weighted shockwave targeting", value=True)

all_edges: List[Tuple[str, str, float]] = []
parse_error: Optional[str] = None

if uploaded_csv is not None:
    try:
        all_edges = read_edges_from_csv(uploaded_csv)
    except Exception as exc:
        parse_error = str(exc)
else:
    try:
        all_edges = parse_edge_text(edge_text)
    except Exception as exc:
        parse_error = str(exc)

if parse_error:
    st.error(parse_error)
    st.stop()

if not all_edges:
    st.warning("Provide at least one valid edge to begin analysis.")
    st.stop()

graph = build_graph(all_edges)
if graph.number_of_nodes() == 0:
    st.warning("No valid nodes found.")
    st.stop()

analysis = analyze_graph(graph, mst_algorithm)
articulation_points = analysis["articulation_points"]
bridges = analysis["bridges"]
mst_edges = analysis["mst_edges"]
mst_weight = analysis["mst_weight"]
recommendations = analysis["recommendations"]
resilience_metrics = analysis["resilience_metrics"]

graph_signature = (
    tuple(sorted(graph.nodes())),
    tuple(sorted((normalize_edge(u, v)[0], normalize_edge(u, v)[1], float(data.get("weight", 1.0))) for u, v, data in graph.edges(data=True))),
)
if st.session_state.get("layout_signature") != graph_signature:
    st.session_state["base_layout"] = nx.spring_layout(graph, seed=42)
    st.session_state["layout_signature"] = graph_signature
base_layout = st.session_state.get("base_layout")

edge_weights = {
    normalize_edge(u, v): float(data.get("weight", 1.0))
    for u, v, data in graph.edges(data=True)
}

current_snapshot = build_live_snapshot(
    graph_nodes=set(graph.nodes()),
    edge_weights=edge_weights,
    components_count=nx.number_connected_components(graph),
    bridges=bridges,
    articulation_points=articulation_points,
    mst_weight=float(mst_weight),
)

previous_snapshot = st.session_state.get("live_snapshot")
render_live_change_explanation(previous_snapshot, current_snapshot)
st.session_state["live_snapshot"] = current_snapshot
st.markdown("---")

components_count = nx.number_connected_components(graph)
bridge_risk_ratio = (len(bridges) / graph.number_of_edges()) if graph.number_of_edges() > 0 else 0.0
node_risk_ratio = (len(articulation_points) / graph.number_of_nodes()) if graph.number_of_nodes() > 0 else 0.0

component_state = "Connected" if components_count == 1 else f"{components_count} Islands"

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Nodes", str(graph.number_of_nodes()))
with c2:
    metric_card("Total Edges", str(graph.number_of_edges()))
with c3:
    metric_card("Topology State", component_state)
with c4:
    metric_card("Bridge Risk Ratio", f"{bridge_risk_ratio:.2f}")

c5, c6, c7, c8 = st.columns(4)
with c5:
    metric_card("Node Criticality Ratio", f"{node_risk_ratio:.2f}")
with c6:
    metric_card("Global Efficiency", f"{resilience_metrics['global_efficiency']:.3f}")
with c7:
    metric_card("Node Connectivity", f"{resilience_metrics['node_connectivity']:.0f}")
with c8:
    metric_card("Largest Island Ratio", f"{resilience_metrics['largest_component_ratio']:.2f}")

left, right = st.columns([1.35, 1])
with left:
    if viz_mode == "Pyvis (Interactive)":
        draw_graph_pyvis(
            graph,
            articulation_points=articulation_points,
            bridges=bridges,
            mst_edges=mst_edges,
            title="Interactive Topology View",
        )
    else:
        draw_graph_matplotlib(
            graph,
            articulation_points=articulation_points,
            bridges=bridges,
            mst_edges=mst_edges,
            title="Topology View (Red: Articulation, Dashed Orange: Bridges, Cyan: MST)",
            pos=base_layout,
        )

with right:
    st.subheader("Critical Components")

    st.markdown("**Articulation Points**")
    if articulation_points:
        for node in sorted(articulation_points):
            st.markdown(f'<span class="pill pill-danger">{node}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-success">None</span>', unsafe_allow_html=True)

    st.markdown("**Bridges**")
    if bridges:
        for edge in sorted(bridges):
            st.markdown(f'<span class="pill pill-info">{format_edge(edge)}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-success">None</span>', unsafe_allow_html=True)

    st.markdown("**MST Summary**")
    st.write(f"Algorithm: **{mst_algorithm.title()}**")
    if components_count == 1:
        st.write(f"Total MST Weight: **{mst_weight:g}**")
    else:
        st.write(f"Total Spanning Forest Weight: **{mst_weight:g}**")
    st.write(
        "Edges: "
        + (", ".join(format_edge(e) for e in sorted(mst_edges)) if mst_edges else "No MST edges")
    )

st.markdown("---")
st.subheader("Algorithm Intelligence")

t1, t2, t3 = st.tabs(["Theory", "Why It Is Critical", "MST Animation + Decisions"])

with t1:
    render_algorithm_theory()

with t2:
    render_critical_reasoning(analysis["bridge_details"], analysis["articulation_details"])

with t3:
    render_mst_table(analysis["mst_steps"])
    render_mst_animation(
        graph,
        mst_steps=analysis["mst_steps"],
        bridges=bridges,
        base_title=f"{mst_algorithm.title()} Construction",
    )

st.markdown("---")
st.subheader("Resilience Lab")

tab_single, tab_campaign = st.tabs(["Single Failure Sandbox", "Multi-Detach Campaign"])

with tab_single:
    sim_mode = st.selectbox("Deactivate", options=["None", "Node", "Edge"], index=0)
    selected_target: Optional[object] = None

    if sim_mode == "Node":
        selected_target = st.selectbox("Node to deactivate", options=sorted(graph.nodes()))
    elif sim_mode == "Edge":
        edge_options = [normalize_edge(u, v) for u, v in graph.edges()]
        edge_labels = {f"{e[0]} - {e[1]}": e for e in sorted(edge_options)}
        selected_label = st.selectbox("Edge to deactivate", options=list(edge_labels.keys()))
        selected_target = edge_labels[selected_label]

    if st.button("Run Single Failure Simulation", use_container_width=True, disabled=sim_mode == "None"):
        result = simulate_failure(graph, sim_mode, selected_target)
        if result["graph"].number_of_nodes() > 0:
            result["analysis"] = analyze_graph(result["graph"], mst_algorithm)
        else:
            result["analysis"] = {
                "articulation_points": set(),
                "bridges": set(),
                "mst_edges": set(),
                "mst_weight": 0.0,
                "recommendations": [],
                "bridge_details": [],
                "articulation_details": [],
                "mst_steps": [],
            }

        st.session_state["single_failure_result"] = result
        st.session_state["single_failure_title"] = f"{sim_mode} Failure"
        st.session_state["single_failure_playing"] = False
        st.session_state["single_failure_frame"] = 0

    single_failure_result = st.session_state.get("single_failure_result")

    if single_failure_result:
        sim_graph = single_failure_result["graph"]
        sim_analysis = single_failure_result["analysis"]

        clear_col, info_col = st.columns([1, 3])
        with clear_col:
            if st.button("Clear Single Failure", use_container_width=True):
                for key in [
                    "single_failure_result",
                    "single_failure_title",
                    "single_failure_playing",
                    "single_failure_frame",
                ]:
                    st.session_state.pop(key, None)
                st.rerun()

        st.info(single_failure_result["message"])

        before_pos = base_layout if base_layout else nx.spring_layout(graph, seed=42)
        after_pos = {n: before_pos[n] for n in sim_graph.nodes() if n in before_pos}

        st.markdown("### Before vs After (Side-by-Side)")
        col_before, col_after = st.columns(2)

        with col_before:
            draw_graph_matplotlib(
                graph,
                articulation_points=articulation_points,
                bridges=bridges,
                mst_edges=mst_edges,
                title="Before Failure",
                pos=before_pos,
            )

        with col_after:
            draw_graph_matplotlib(
                sim_graph,
                articulation_points=sim_analysis["articulation_points"],
                bridges=sim_analysis["bridges"],
                mst_edges=sim_analysis["mst_edges"],
                title="After Failure",
                pos=after_pos if after_pos else None,
            )

        st.markdown("### Transition Animation")
        transition_title = st.session_state.get("single_failure_title", "Single Failure")
        frame_key = f"single_failure_frame_{transition_title}"
        play_key = f"single_failure_playing_{transition_title}"

        current_frame = int(st.session_state.get(frame_key, 0))
        control_col, action_col = st.columns([2, 1])
        with control_col:
            current_frame = st.slider("Transition Frame", min_value=0, max_value=1, value=current_frame, key=frame_key)
        with action_col:
            if st.button("Play Before -> After", use_container_width=True):
                st.session_state[play_key] = True
                st.session_state[frame_key] = 0
                st.rerun()
            if st.button("Pause", use_container_width=True):
                st.session_state[play_key] = False

        transition_placeholder = st.empty()

        def draw_transition_frame(frame: int) -> None:
            with transition_placeholder.container():
                if frame == 0:
                    draw_graph_matplotlib(
                        graph,
                        articulation_points=articulation_points,
                        bridges=bridges,
                        mst_edges=mst_edges,
                        title="Transition Frame: Before",
                        pos=before_pos,
                    )
                else:
                    draw_graph_matplotlib(
                        sim_graph,
                        articulation_points=sim_analysis["articulation_points"],
                        bridges=sim_analysis["bridges"],
                        mst_edges=sim_analysis["mst_edges"],
                        title="Transition Frame: After",
                        pos=after_pos if after_pos else None,
                    )

        if st.session_state.get(play_key, False):
            draw_transition_frame(current_frame)
            if current_frame >= 1:
                st.session_state[play_key] = False
            else:
                st.session_state[frame_key] = current_frame + 1
                time.sleep(animation_speed)
                st.rerun()
        else:
            draw_transition_frame(current_frame)

        st.markdown("### Comparative Data")
        comparison_df = pd.DataFrame(
            [
                {
                    "Metric": "Nodes",
                    "Before": graph.number_of_nodes(),
                    "After": sim_graph.number_of_nodes(),
                },
                {
                    "Metric": "Edges",
                    "Before": graph.number_of_edges(),
                    "After": sim_graph.number_of_edges(),
                },
                {
                    "Metric": "Connected Components",
                    "Before": nx.number_connected_components(graph),
                    "After": nx.number_connected_components(sim_graph) if sim_graph.number_of_nodes() > 0 else 0,
                },
                {
                    "Metric": "Bridges",
                    "Before": len(bridges),
                    "After": len(sim_analysis["bridges"]),
                },
                {
                    "Metric": "Articulation Points",
                    "Before": len(articulation_points),
                    "After": len(sim_analysis["articulation_points"]),
                },
                {
                    "Metric": "MST Weight",
                    "Before": mst_weight,
                    "After": sim_analysis["mst_weight"],
                },
            ]
        )
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        render_island_distribution(single_failure_result["components"], "Post-Failure Island Size Distribution")

        sim_metrics = sim_analysis.get("resilience_metrics", {})
        if sim_metrics:
            st.markdown("### Post-Failure Resilience Metrics")
            sim_df = pd.DataFrame(
                [
                    {"Metric": "Global Efficiency", "Value": f"{sim_metrics['global_efficiency']:.3f}"},
                    {"Metric": "Node Connectivity", "Value": f"{sim_metrics['node_connectivity']:.0f}"},
                    {"Metric": "Edge Connectivity", "Value": f"{sim_metrics['edge_connectivity']:.0f}"},
                    {"Metric": "Largest Island Ratio", "Value": f"{sim_metrics['largest_component_ratio']:.2f}"},
                ]
            )
            st.dataframe(sim_df, use_container_width=True, hide_index=True)
    else:
        st.info("Run a single failure simulation to keep this viewer open. The lab will persist while you interact.")

with tab_campaign:
    st.markdown("Detaching multiple assets emulates cascades and operational outages over time.")

    edge_options = [normalize_edge(u, v) for u, v in graph.edges()]
    edge_label_to_pair = {f"{e[0]} - {e[1]}": e for e in sorted(edge_options)}

    selected_nodes = st.multiselect("Detach Nodes (sequence starts here)", options=sorted(graph.nodes()))
    selected_edge_labels = st.multiselect("Detach Edges (after node removals)", options=list(edge_label_to_pair.keys()))
    selected_edges = [edge_label_to_pair[label] for label in selected_edge_labels]

    if campaign_mode == "Monte Carlo Random Failures":
        mc_trials = st.slider("Monte Carlo Trials", min_value=25, max_value=1000, value=200, step=25)
        mc_steps = st.slider("Random Failure Steps", min_value=1, max_value=max(1, graph.number_of_edges()), value=min(8, max(1, graph.number_of_edges())))
        mc_mode = st.selectbox("Failure Unit", options=["edge", "node"], index=0)
        mc_seed = st.number_input("Random Seed", min_value=1, max_value=999999, value=42, step=1)

    if st.button("Run Campaign Simulation", use_container_width=True):
        if campaign_mode == "Manual Multi-Detach":
            frames = simulate_failure_campaign(graph, selected_nodes, selected_edges)
            campaign_title = "Manual Multi-Detach Animation"
            st.session_state["campaign_frames"] = frames
        elif campaign_mode == "Bridge Shockwave":
            frames = simulate_bridge_shockwave(graph, shockwave_steps, use_weights=shockwave_weighted)
            campaign_title = "Bridge Shockwave Animation"
            st.session_state["campaign_frames"] = frames
        else:
            campaign_title = "Monte Carlo Random Failure Profile"
            summary = simulate_random_failures(
                graph,
                trials=mc_trials,
                max_steps=mc_steps,
                mode=mc_mode,
                seed=int(mc_seed),
            )
            st.session_state["monte_carlo_summary"] = summary
            st.session_state.pop("campaign_frames", None)

        st.session_state["campaign_title"] = campaign_title
        st.session_state["campaign_mode"] = campaign_mode
        st.session_state["campaign_graph_signature"] = tuple(sorted(graph.nodes()))
        st.session_state[f"campaign_playing_{campaign_title}"] = False
        st.session_state[f"campaign_play_index_{campaign_title}"] = 0

    campaign_frames = st.session_state.get("campaign_frames")
    monte_carlo_summary = st.session_state.get("monte_carlo_summary")
    campaign_title = st.session_state.get("campaign_title", "Resilience Campaign")

    if campaign_mode == "Monte Carlo Random Failures" and monte_carlo_summary:
        st.markdown("### Monte Carlo Risk Profile")
        mc_df = pd.DataFrame(monte_carlo_summary)
        display_df = mc_df.rename(
            columns={
                "step": "Step",
                "disconnect_probability": "Disconnect Probability",
                "avg_components": "Avg Components",
                "avg_lcc_ratio": "Avg Largest Island Ratio",
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.line_chart(display_df.set_index("Step")[["Disconnect Probability", "Avg Components", "Avg Largest Island Ratio"]])

    if campaign_frames:
        if st.button("Clear Campaign", use_container_width=True):
            for key in [
                "campaign_frames",
                "campaign_title",
                "campaign_mode",
                "campaign_graph_signature",
                f"campaign_playing_{campaign_title}",
                f"campaign_play_index_{campaign_title}",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

        current_index = render_failure_campaign_controls(campaign_frames, campaign_title)
        render_failure_campaign_frame(
            frames=campaign_frames,
            frame_index=current_index,
            mst_algorithm=mst_algorithm,
            title=campaign_title,
        )
        render_campaign_timeline(campaign_frames)

        if st.session_state.get(f"campaign_playing_{campaign_title}", False):
            if current_index >= len(campaign_frames) - 1:
                st.session_state[f"campaign_playing_{campaign_title}"] = False
            else:
                st.session_state[f"campaign_play_index_{campaign_title}"] = current_index + 1
                time.sleep(animation_speed)
                st.rerun()

        final_graph = campaign_frames[-1].graph
        final_analysis = analyze_graph(final_graph, mst_algorithm) if final_graph.number_of_nodes() > 0 else {
            "articulation_points": set(),
            "bridges": set(),
            "mst_edges": set(),
        }
        st.markdown("### Baseline vs End-of-Campaign")
        cb, ca = st.columns(2)
        base_pos = base_layout if base_layout else nx.spring_layout(graph, seed=42)
        end_pos = {n: base_pos[n] for n in final_graph.nodes() if n in base_pos}

        with cb:
            draw_graph_matplotlib(
                graph,
                articulation_points=articulation_points,
                bridges=bridges,
                mst_edges=mst_edges,
                title="Campaign Start",
                pos=base_pos,
            )

        with ca:
            draw_graph_matplotlib(
                final_graph,
                articulation_points=final_analysis["articulation_points"],
                bridges=final_analysis["bridges"],
                mst_edges=final_analysis["mst_edges"],
                title="Campaign End",
                pos=end_pos if end_pos else None,
            )
    else:
        st.info("Run a campaign to keep the lab open. The simulation will remain visible while you adjust the controls.")

st.markdown("---")
render_reinforcement_report(recommendations, len(bridges))
