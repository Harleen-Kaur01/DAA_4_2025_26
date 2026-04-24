import io
from typing import List, Tuple

import pandas as pd

Edge = Tuple[str, str, float]


def parse_edge_text(raw_text: str) -> List[Edge]:
    """Parse multiline edge text using format: A-B, 10"""
    edges: List[Edge] = []
    if not raw_text.strip():
        return edges

    for idx, line in enumerate(raw_text.splitlines(), start=1):
        cleaned = line.strip()
        if not cleaned:
            continue

        try:
            left, weight_part = cleaned.split(",", 1)
            u, v = left.split("-", 1)
            u = u.strip()
            v = v.strip()
            w = float(weight_part.strip())
            if not u or not v:
                raise ValueError("Empty node label.")
            edges.append((u, v, w))
        except Exception as exc:
            raise ValueError(
                f"Invalid edge format on line {idx}: '{line}'. Use format 'A-B, 10'."
            ) from exc

    return edges


def read_edges_from_csv(uploaded_file: io.BytesIO) -> List[Edge]:
    """Read edge list CSV with columns: source,target,weight"""
    df = pd.read_csv(uploaded_file)
    required_cols = {"source", "target", "weight"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError("CSV must include columns: source,target,weight")

    edges: List[Edge] = []
    for _, row in df.iterrows():
        u = str(row["source"]).strip()
        v = str(row["target"]).strip()
        w = float(row["weight"])
        if not u or not v:
            continue
        edges.append((u, v, w))
    return edges
