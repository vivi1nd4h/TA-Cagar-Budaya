from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"

BAB4_PATH = DATA_DIR / "bab4.json"
TOPIC_REVIEW_PATH = INPUT_DIR / "df_final_topic_gmaps.xlsx"
INTEGRATED_PATH = INPUT_DIR / "integrasi_sna_topik_final.xlsx"
OBP_PROFILE_PATH = INPUT_DIR / "obp_object_profile_final.xlsx"
RAW_REVIEW_PATH = INPUT_DIR / "GMaps_Reviews_Merged_Clean.xlsx"
COORDINATE_PATH = INPUT_DIR / "GMaps_Reviews_With_Coordinates.xlsx"

TOPIC_ID_ALIASES = {"M1": "T12", "M2": "T16", "M3": "T4"}
ISSUE_TOPIC_IDS = {7, 8, 15}


def _coordinate_lookup(fallback: pd.DataFrame) -> dict[str, dict[str, float]]:
    coordinates = fallback.set_index("nama")[["lat", "lon"]].to_dict("index")
    if not COORDINATE_PATH.exists():
        return coordinates

    source = pd.read_excel(COORDINATE_PATH)
    required = {"Nama Objek (Standar)", "Latitude", "Longitude"}
    if not required.issubset(source.columns):
        return coordinates

    source = source.dropna(subset=["Nama Objek (Standar)", "Latitude", "Longitude"]).copy()
    source["Nama Objek (Standar)"] = source["Nama Objek (Standar)"].astype(str).str.strip()
    coordinate_rows = (
        source.groupby("Nama Objek (Standar)", as_index=False)
        .agg(lat=("Latitude", "first"), lon=("Longitude", "first"))
    )
    for _, row in coordinate_rows.iterrows():
        coordinates[str(row["Nama Objek (Standar)"]).strip()] = {
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        }
    return coordinates


def _load_bab4() -> dict:
    with BAB4_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)

    for topic in data["topik"]:
        topic["id_source"] = topic["id"]
        topic["id"] = TOPIC_ID_ALIASES.get(topic["id"], topic["id"])
    return data


def _topic_number(value: object) -> int:
    text = str(value).strip().upper()
    if text in {"NOISE", "OUTLIER", "NOISE/OUTLIER"}:
        return -1
    text = TOPIC_ID_ALIASES.get(text, text)
    if text.startswith("T"):
        text = text[1:]
    return int(float(text))


def _community_number(value: object) -> int:
    text = str(value).strip().upper().replace("K-", "")
    return int(float(text))


def _topic_metadata(bab4: dict) -> dict[int, dict]:
    metadata: dict[int, dict] = {}
    for topic in bab4["topik"]:
        metadata[_topic_number(topic["id"])] = topic
    return metadata


def load_topics(bab4: dict) -> pd.DataFrame:
    """Build the topic summary from the final per-review BERTopic output."""
    topic_meta = _topic_metadata(bab4)

    if not TOPIC_REVIEW_PATH.exists():
        return pd.DataFrame(bab4["topik"])

    reviews = pd.read_excel(TOPIC_REVIEW_PATH)
    required = {"topic_id_final", "topic_keywords_final"}
    if not required.issubset(reviews.columns):
        return pd.DataFrame(bab4["topik"])

    reviews["topic_id_final"] = reviews["topic_id_final"].map(
        lambda value: _topic_number(value) if pd.notna(value) else np.nan
    )
    valid = reviews[reviews["topic_id_final"].notna() & (reviews["topic_id_final"] != -1)].copy()
    valid["topic_id_final"] = valid["topic_id_final"].astype(int)
    total = len(valid)

    rows: list[dict] = []
    for topic_id, group in valid.groupby("topic_id_final"):
        meta = topic_meta.get(topic_id, {})
        label = (
            group["topic_label"].dropna().astype(str).iloc[0]
            if "topic_label" in group and group["topic_label"].notna().any()
            else meta.get("label", f"Topik T{topic_id}")
        )
        label_short = (
            group["topic_label_short"].dropna().astype(str).iloc[0]
            if "topic_label_short" in group and group["topic_label_short"].notna().any()
            else meta.get("short", label)
        )
        keyword_values = group["topic_keywords_final"].dropna().astype(str)
        keywords = keyword_values.mode().iloc[0] if not keyword_values.empty else ""
        rows.append(
            {
                "id": f"T{topic_id}",
                "topic_id": topic_id,
                "label": label,
                "label_short": label_short,
                "n": len(group),
                "pct": round(len(group) / total * 100, 1) if total else 0.0,
                "keywords": keywords,
                "rumpun": meta.get("rumpun", "Topik final"),
            }
        )

    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def _top_topic_profile(row: pd.Series, topic_meta: dict[int, dict]) -> dict:
    topic_columns = [
        column
        for column in row.index
        if column.startswith("T") and column.endswith("_pct")
    ]
    proportions = {
        _topic_number(column.replace("_pct", "")): float(row.get(column, 0) or 0)
        for column in topic_columns
        if pd.notna(row.get(column))
    }
    ordered = sorted(proportions.items(), key=lambda item: item[1], reverse=True)
    ordered = [(topic_id, pct) for topic_id, pct in ordered if pct > 0]

    if not ordered:
        return {
            "top_1_id": -1,
            "top_1_label": "-",
            "top_1_pct": 0.0,
            "top_2_id": -1,
            "top_2_label": "-",
            "top_2_pct": 0.0,
            "topic_purity": 0.0,
            "topic_entropy": 0.0,
            "issue_topic_share": 0.0,
        }

    top_1_id, top_1_pct = ordered[0]
    top_2_id, top_2_pct = ordered[1] if len(ordered) > 1 else (-1, 0.0)
    probabilities = np.array([pct / 100 for _, pct in ordered], dtype=float)
    entropy = -np.sum(probabilities * np.log(probabilities))
    normalized_entropy = entropy / np.log(len(probabilities)) if len(probabilities) > 1 else 0.0

    def short_label(topic_id: int) -> str:
        if topic_id == -1:
            return "-"
        meta = topic_meta.get(topic_id, {})
        return meta.get("short", meta.get("label", f"T{topic_id}"))

    return {
        "top_1_id": top_1_id,
        "top_1_label": short_label(top_1_id),
        "top_1_pct": round(top_1_pct, 1),
        "top_2_id": top_2_id,
        "top_2_label": short_label(top_2_id),
        "top_2_pct": round(top_2_pct, 1),
        "topic_purity": round(top_1_pct / 100, 3),
        "topic_entropy": round(float(normalized_entropy), 3),
        "issue_topic_share": round(
            sum(proportions.get(topic_id, 0.0) for topic_id in ISSUE_TOPIC_IDS), 1
        ),
    }


def _first_existing(row: pd.Series, candidates: list[str], default: object = np.nan) -> object:
    for column in candidates:
        if column in row.index and pd.notna(row[column]):
            return row[column]
    return default


def _float_value(row: pd.Series, candidates: list[str], default: float = 0.0) -> float:
    value = _first_existing(row, candidates, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_value(row: pd.Series, candidates: list[str], default: int = 0) -> int:
    value = _float_value(row, candidates, float(default))
    if pd.isna(value):
        return default
    return int(round(value))


def _load_obp_profile(bab4: dict, fallback: pd.DataFrame) -> pd.DataFrame | None:
    """Load the notebook's final OBP profile when exported.

    This keeps the dashboard aligned with the TA notebook's OBP-5 logic:
    sentiment_balance = pct_positive - pct_negative, derived from
    df_valid_sent["sentiment_pred_label"].
    """
    if not OBP_PROFILE_PATH.exists():
        return None

    source = pd.read_excel(OBP_PROFILE_PATH)
    if source.empty:
        return None

    source = source.copy()
    source.columns = [str(column).strip() for column in source.columns]
    topic_meta = _topic_metadata(bab4)
    coordinates = _coordinate_lookup(fallback)

    def topic_short(value: object) -> str:
        if pd.isna(value):
            return "-"
        text = str(value).strip()
        try:
            topic_id = _topic_number(text)
        except (TypeError, ValueError):
            return text if text else "-"
        meta = topic_meta.get(topic_id, {})
        return meta.get("short", meta.get("label", f"T{topic_id}"))

    rows: list[dict] = []
    for _, source_row in source.iterrows():
        name = str(_first_existing(source_row, ["nama_objek", "Nama_Objek", "nama", "Objek"])).strip()
        if not name or name.lower() == "nan":
            continue

        community = _community_number(_first_existing(source_row, ["community", "Community", "komunitas", "Kom"]))
        coord = coordinates.get(name, {"lat": np.nan, "lon": np.nan})
        positive = _float_value(source_row, ["pct_positive", "%Pos", "pos", "pct_positif"])
        negative = _float_value(source_row, ["pct_negative", "%Neg", "neg", "pct_negatif"])
        neutral = _float_value(
            source_row,
            ["pct_neutral", "pct_netral", "netral", "neutral"],
            max(0.0, 100.0 - positive - negative),
        )
        balance = _float_value(
            source_row,
            ["sentiment_balance", "balance"],
            round(positive - negative, 1),
        )

        top_1_id = _int_value(source_row, ["top_1_id", "topik_dominan_id", "dominant_topic_id"], -1)
        top_2_id = _int_value(source_row, ["top_2_id"], -1)
        top_1_label = str(
            _first_existing(
                source_row,
                ["top_1_label", "Topik Dominan", "dominant_topic_label", "topik_dominan_label"],
                topic_short(top_1_id),
            )
        )
        top_2_label = str(
            _first_existing(
                source_row,
                ["top_2_label", "Topik Kedua", "topikPendamping"],
                topic_short(top_2_id),
            )
        )
        dominant_sentiment = str(
            _first_existing(
                source_row,
                ["dominant_sentiment", "Sentimen Dominan"],
                max(
                    {"positive": positive, "negative": negative, "neutral": neutral},
                    key={"positive": positive, "negative": negative, "neutral": neutral}.get,
                ),
            )
        )

        rows.append(
            {
                "nama": name,
                "komunitas": community,
                "wd": _float_value(source_row, ["weighted_degree", "Weighted_Degree", "WD", "wd"]),
                "degree": _float_value(source_row, ["degree", "Degree"], 0.0),
                "degree_centrality": _float_value(
                    source_row,
                    ["degree_centrality", "Degree_Centrality"],
                    0.0,
                ),
                "bc": _float_value(
                    source_row,
                    ["betweenness_centrality", "Betweenness_Centrality", "BC", "bc"],
                    0.0,
                ),
                "avg_rating": _float_value(source_row, ["avg_rating", "Avg_Rating"], np.nan),
                "unique_reviewer": _int_value(source_row, ["unique_reviewer"], 0),
                "total_valid": _int_value(source_row, ["total_valid", "total_ulasan"], 0),
                "pos": positive,
                "neg": negative,
                "netral": neutral,
                "balance": round(balance, 1),
                "dominant_sentiment": dominant_sentiment,
                "topikUtama": top_1_label,
                "topikUtamaPct": _float_value(source_row, ["top_1_pct", "topik_dominan_pct"], 0.0),
                "topikPendamping": top_2_label,
                "lat": coord["lat"],
                "lon": coord["lon"],
                "top_1_id": top_1_id,
                "top_1_label": top_1_label,
                "top_1_pct": _float_value(source_row, ["top_1_pct", "topik_dominan_pct"], 0.0),
                "top_2_id": top_2_id,
                "top_2_label": top_2_label,
                "top_2_pct": _float_value(source_row, ["top_2_pct"], 0.0),
                "topic_purity": _float_value(source_row, ["topic_purity"], 0.0),
                "topic_entropy": _float_value(source_row, ["topic_entropy"], 0.0),
                "issue_topic_share": _float_value(source_row, ["issue_topic_share"], 0.0),
                "peran": str(_first_existing(source_row, ["role_label", "Role", "peran"], "")),
            }
        )

    if not rows:
        return None

    result = pd.DataFrame(rows)
    missing_role = result["peran"].isna() | (result["peran"].astype(str).str.strip() == "")
    if missing_role.any():
        reassigned = _assign_obp_roles(result.drop(columns=["peran"]))
        result.loc[missing_role, "peran"] = reassigned.loc[missing_role, "peran"]
    return result.sort_values(["komunitas", "wd"], ascending=[True, False]).reset_index(drop=True)


def _assign_obp_roles(objects: pd.DataFrame) -> pd.DataFrame:
    result = objects.copy()
    positive_bc = result.loc[result["bc"] > 0, "bc"]
    thresholds = {
        "wd_high": np.nanpercentile(result["wd"], 60),
        "bc_high": np.nanpercentile(positive_bc, 70) if not positive_bc.empty else math.inf,
        "pos_high": np.nanpercentile(result["pos"], 60),
        "neg_high": np.nanpercentile(result["neg"], 70),
        "neg_med": np.nanpercentile(result["neg"], 50),
        "purity_hi": np.nanpercentile(result["topic_purity"], 65),
    }

    bridge_names = set(
        result.loc[result.groupby("komunitas")["bc"].idxmax(), "nama"].tolist()
    )

    def assign(row: pd.Series) -> str:
        wd_high = row["wd"] >= thresholds["wd_high"]
        bc_high = (
            row["bc"] > 0
            and (row["bc"] >= thresholds["bc_high"] or row["nama"] in bridge_names)
        )
        pos_high = row["pos"] >= thresholds["pos_high"]
        neg_high = row["neg"] >= thresholds["neg_high"]
        purity_high = row["topic_purity"] >= thresholds["purity_hi"]
        issue_dominant = (
            row["top_1_id"] in ISSUE_TOPIC_IDS or row["issue_topic_share"] >= 25
        )

        if (wd_high or bc_high) and neg_high:
            return "Issue Amplifier Node"
        if bc_high:
            return "Bridge Heritage Node"
        if wd_high and pos_high:
            return "Anchor Experience Node"
        if issue_dominant and row["neg"] >= thresholds["neg_med"]:
            return "Operational Concern Node"
        if purity_high:
            return "Specialized Identity Node"
        if pos_high and not wd_high:
            return "Niche Positive Node"
        return "General Heritage Node"

    result["peran"] = result.apply(assign, axis=1)
    return result


def load_objects(bab4: dict) -> pd.DataFrame:
    """Load the integrated topic-sentiment-SNA object table and derive OBP fields."""
    fallback = pd.DataFrame(bab4["objek"])
    obp_profile = _load_obp_profile(bab4, fallback)
    if obp_profile is not None:
        return obp_profile

    if not INTEGRATED_PATH.exists():
        coordinates = _coordinate_lookup(fallback)
        fallback["lat"] = fallback["nama"].map(lambda name: coordinates.get(name, {}).get("lat", np.nan))
        fallback["lon"] = fallback["nama"].map(lambda name: coordinates.get(name, {}).get("lon", np.nan))
        fallback["balance"] = (fallback["pos"] - fallback["neg"]).round(1)
        fallback["netral"] = (100 - fallback["pos"] - fallback["neg"]).clip(lower=0)
        return fallback

    source = pd.read_excel(INTEGRATED_PATH)
    topic_meta = _topic_metadata(bab4)
    coordinates = _coordinate_lookup(fallback)

    rows: list[dict] = []
    for _, source_row in source.iterrows():
        topic_profile = _top_topic_profile(source_row, topic_meta)
        name = str(source_row["nama_objek"]).strip()
        coord = coordinates.get(name, {"lat": np.nan, "lon": np.nan})
        community = _community_number(source_row["community"])
        positive = float(source_row["pct_positif"])
        negative = float(source_row["pct_negatif"])
        neutral = float(source_row["pct_netral"])
        dominant_sentiment = max(
            {"positive": positive, "negative": negative, "neutral": neutral},
            key={"positive": positive, "negative": negative, "neutral": neutral}.get,
        )
        rows.append(
            {
                "nama": name,
                "komunitas": community,
                "wd": float(source_row["weighted_degree"]),
                "degree": float(source_row["degree"]),
                "degree_centrality": float(source_row["degree_centrality"]),
                "bc": float(source_row["betweenness_centrality"]),
                "avg_rating": float(source_row["avg_rating"]),
                "unique_reviewer": int(source_row["unique_reviewer"]),
                "total_valid": int(source_row["total_valid"]),
                "pos": positive,
                "neg": negative,
                "netral": neutral,
                "balance": round(positive - negative, 1),
                "dominant_sentiment": dominant_sentiment,
                "topikUtama": str(source_row["topik_dominan_label"]),
                "topikUtamaPct": float(source_row["topik_dominan_pct"]),
                "topikPendamping": topic_profile["top_2_label"],
                "lat": coord["lat"],
                "lon": coord["lon"],
                **topic_profile,
            }
        )

    result = _assign_obp_roles(pd.DataFrame(rows))
    return result.sort_values(["komunitas", "wd"], ascending=[True, False]).reset_index(drop=True)


def load_communities(bab4: dict, objects: pd.DataFrame) -> pd.DataFrame:
    source = pd.DataFrame(bab4["komunitas"])
    source = source[source["id"].isin(sorted(objects["komunitas"].unique()))].copy()
    bridges = objects.loc[objects.groupby("komunitas")["bc"].idxmax()].set_index(
        "komunitas"
    )["nama"]
    source["bridge"] = source["id"].map(bridges)
    return source.sort_values("id").reset_index(drop=True)


def build_empirical_edges(objects: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the notebook co-reviewer edges, limited to the 27 final objects."""
    processed_path = PROCESSED_DIR / "gephi_edges_final.csv"
    if processed_path.exists():
        cached = pd.read_csv(processed_path)
        expected_nodes = set(objects["nama"])
        cached_nodes = set(cached["Source"]) | set(cached["Target"])
        if cached_nodes.issubset(expected_nodes):
            return cached

    if not RAW_REVIEW_PATH.exists():
        return pd.DataFrame(columns=["Source", "Target", "Weight", "Type"])

    reviews = pd.read_excel(RAW_REVIEW_PATH, sheet_name="Data GMaps Reviews")
    reviews = reviews.iloc[:, :10].copy()
    reviews.columns = [
        "Nama_Objek",
        "GMaps_Title",
        "Place_ID",
        "Reviewer_ID",
        "Reviewer_Name",
        "Reviewer_URL",
        "Total_Reviews_User",
        "Rating",
        "Review_Text",
        "Review_Date",
    ]
    reviews = reviews[reviews["Nama_Objek"].isin(set(objects["nama"]))].copy()
    reviews = reviews.dropna(subset=["Reviewer_ID", "Nama_Objek"])

    reviewer_counts = reviews.groupby("Reviewer_ID")["Nama_Objek"].nunique()
    co_reviewer_ids = reviewer_counts[reviewer_counts > 1].index
    co_reviews = reviews[reviews["Reviewer_ID"].isin(co_reviewer_ids)]

    edge_instances: list[tuple[str, str]] = []
    for _, group in co_reviews.groupby("Reviewer_ID"):
        places = sorted(group["Nama_Objek"].dropna().astype(str).unique())
        edge_instances.extend(combinations(places, 2))

    if not edge_instances:
        return pd.DataFrame(columns=["Source", "Target", "Weight", "Type"])

    edges = (
        pd.DataFrame(edge_instances, columns=["Source", "Target"])
        .groupby(["Source", "Target"])
        .size()
        .reset_index(name="Weight")
    )
    edges = edges[edges["Weight"] >= 2].sort_values(
        "Weight", ascending=False
    ).reset_index(drop=True)
    edges["Type"] = "Undirected"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    edges.to_csv(processed_path, index=False)
    return edges


def build_obp_table(objects: pd.DataFrame, communities: pd.DataFrame) -> pd.DataFrame:
    community_names = communities.set_index("id")["nama"].to_dict()
    result = objects.copy()
    result["komunitas_nama"] = result["komunitas"].map(community_names)
    result["interpretasi"] = result.apply(
        lambda row: (
            f"{row['komunitas_nama']}; diskursus didominasi "
            f"'{row['top_1_label']}' ({row['top_1_pct']:.0f}%), "
            f"sentimen dominan {row['dominant_sentiment']} "
            f"(+{row['pos']:.0f}% / -{row['neg']:.0f}%); "
            f"peran: {row['peran']}."
        ),
        axis=1,
    )
    columns = [
        "komunitas",
        "komunitas_nama",
        "nama",
        "peran",
        "top_1_label",
        "top_1_pct",
        "top_2_label",
        "top_2_pct",
        "topic_purity",
        "topic_entropy",
        "issue_topic_share",
        "pos",
        "neg",
        "netral",
        "balance",
        "dominant_sentiment",
        "wd",
        "degree_centrality",
        "bc",
        "avg_rating",
        "interpretasi",
    ]
    return result[columns]


def load_dashboard_data() -> dict:
    bab4 = _load_bab4()
    topics = load_topics(bab4)
    objects = load_objects(bab4)
    communities = load_communities(bab4, objects)
    edges = build_empirical_edges(objects)
    obp = build_obp_table(objects, communities)

    source_status = {
        "topik": TOPIC_REVIEW_PATH.exists(),
        "sentimen_objek": OBP_PROFILE_PATH.exists() or INTEGRATED_PATH.exists(),
        "sna_nodes": OBP_PROFILE_PATH.exists() or INTEGRATED_PATH.exists(),
        "sna_edges": not edges.empty,
        "obp": OBP_PROFILE_PATH.exists(),
        "obp_profile": OBP_PROFILE_PATH.exists(),
        "integrated_profile": INTEGRATED_PATH.exists(),
    }
    return {
        "bab4": bab4,
        "topics": topics,
        "objects": objects,
        "communities": communities,
        "edges": edges,
        "obp": obp,
        "source_status": source_status,
    }


if __name__ == "__main__":
    payload = load_dashboard_data()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    payload["topics"].to_csv(PROCESSED_DIR / "topics_final.csv", index=False)
    payload["objects"].to_csv(PROCESSED_DIR / "objects_integrated.csv", index=False)
    payload["obp"].to_csv(PROCESSED_DIR / "obp_object_profile_final.csv", index=False)
    print(
        f"Generated {len(payload['topics'])} topics, "
        f"{len(payload['objects'])} objects, "
        f"{len(payload['edges'])} empirical edges."
    )
