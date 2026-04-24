# Network Reliability & Resilience Scanner

An interactive Streamlit app for analyzing communication and power networks with NetworkX. It highlights structural vulnerabilities, simulates failures, and explains why the network is fragile or resilient.

## Features

- Edge input via text or CSV upload
- Articulation point detection
- Bridge detection
- Minimum Spanning Tree analysis using Kruskal or Prim
- Live explanation of how edits affect the network
- Side-by-side before/after failure comparison
- Multi-node and multi-edge detach campaigns
- Bridge shockwave simulation
- Weighted bridge shockwave targeting
- Monte Carlo random failure profiling (node/edge)
- MST step-by-step animation
- Interactive visualization with Matplotlib or Pyvis
- Reinforcement recommendations for redundancy
- Advanced resilience KPIs (efficiency, connectivity, island ratio)

## Project Structure

- `app.py` - Streamlit entrypoint and UI orchestration
- `network_scanner/parsing.py` - Input parsing helpers
- `network_scanner/algorithms.py` - Graph analytics and simulation logic
- `network_scanner/visualization.py` - Graph rendering and animation helpers
- `network_scanner/ui_sections.py` - Theory, diagnostics, and report sections
- `sample_network_edges.csv` - Example CSV input

## Requirements

- Python 3.13 recommended
- Streamlit
- NetworkX
- Pandas
- Matplotlib
- Pyvis

## Run the Project

From the project root:

```bash
cd /Users/gauravmishra/DAA_new
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If you have not created the virtual environment yet:

```bash
cd /Users/gauravmishra/DAA_new
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Example CSV Format

```csv
source,target,weight
A,B,10
B,C,12
C,D,7
B,D,9
D,E,4
E,F,3
C,F,6
```

## Notes

- If Pyvis is unavailable, the app falls back gracefully to Matplotlib mode.
- The campaign simulator persists in session state so the lab stays open while you interact with controls.
- If the editor shows unresolved imports, make sure VS Code is using the `.venv` interpreter.
