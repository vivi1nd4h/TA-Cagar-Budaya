from __future__ import annotations

import html
import io
import json
import math
import textwrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

try:
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ModuleNotFoundError:
    mpatches = None
    plt = None
    MATPLOTLIB_AVAILABLE = False

from data_pipeline import load_dashboard_data

COMMUNITY_FALLBACK = {
    0: "#C9772F",
    1: "#1F8A5B",
    2: "#2A6FDB",
    3: "#8754C9",
}
SPATIAL_COLORS = {
    "Utara · Kota Lama–Ampel": "#C9772F",
    "Pusat · Tunjungan–Grahadi": "#2C66C9",
    "Timur · Monkasel–Gelora": "#8A63D2",
    "Selatan–Barat · Darmo–Rahmat": "#1F8A5B",
    "Koordinat belum tersedia": "#9B9285",
}
TOPIC_RUMPUN_COLORS = {
    "Religi": "#2C8A62",
    "Kuliner & Hospitality": "#C9772F",
    "Museum & Edukasi": "#2C66C9",
    "Heritage & Identitas Kota": "#7E4FC0",
    "Fasilitas & Operasional": "#C9360A",
}
NOTEBOOK_COMMUNITY_COLORS = {
    0: "#E63946",
    1: "#2A9D8F",
    2: "#E9C46A",
    3: "#4361EE",
}
st.set_page_config(
    page_title="Ekosistem Pengalaman Cagar Budaya Surabaya",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data
def load_app_data() -> dict:
    return load_dashboard_data()


def enrich_object_labels(
    objects: pd.DataFrame, communities: pd.DataFrame
) -> pd.DataFrame:
    objects = objects.copy()
    community_names = communities.set_index("id")["nama"].to_dict()
    community_colors = communities.set_index("id")["color"].to_dict()
    objects["komunitas_nama"] = objects["komunitas"].map(community_names)
    objects["komunitas_warna"] = objects["komunitas"].map(community_colors)
    objects["objek_short"] = (
        objects["nama"]
        .str.replace("Monumen dan Museum ", "", regex=False)
        .str.replace("Kawasan ", "", regex=False)
    )
    return objects


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap');
        :root {
            --ink: #211d17;
            --muted: #756b5c;
            --paper: #eee9de;
            --card: #fbfaf6;
            --line: #ded5c6;
            --green: #1f7a57;
            --blue: #2c66c9;
            --purple: #7e4fc0;
            --brown: #a05d17;
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"],
        #MainMenu,
        footer {
            display: none !important;
        }
        [data-testid="stSidebar"] {display: none !important;}
        .stApp {
            background: var(--paper);
            color: var(--ink);
            font-family: "IBM Plex Sans", sans-serif;
        }
        .block-container {
            max-width: 1490px;
            padding: 3.1rem 1.6rem 4.5rem;
        }
        p, li, div, label {font-family: "IBM Plex Sans", sans-serif;}
        h1, h2, h3 {color: var(--ink); letter-spacing: -.02em;}
        h1 {
            font-family: "Spectral", Georgia, serif !important;
            font-weight: 600 !important;
        }
        h2, h3 {
            font-family: "IBM Plex Sans", sans-serif !important;
            font-weight: 700 !important;
        }
        h2 {font-size: 1.9rem !important; margin: 2rem 0 1rem !important;}
        h3 {font-size: 1.15rem !important;}
        .hero {
            padding: 0 0 2.25rem;
            margin: 0 0 .35rem;
            border: 0;
            background: transparent;
            box-shadow: none;
        }
        .hero-kicker, .eyebrow {
            font-family: "IBM Plex Mono", monospace;
            font-size: .76rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
        }
        .hero-kicker {display: none;}
        .hero h1 {
            font-size: clamp(2.35rem, 3vw, 3.35rem);
            line-height: 1.08;
            text-transform: none;
            letter-spacing: -.018em;
            margin: .7rem 0 .85rem;
            max-width: 1240px;
        }
        .hero p {
            font-size: 1.04rem;
            line-height: 1.55;
            color: #4f493f;
            max-width: 1045px;
            margin: 0;
        }
        .metric-card {
            padding: 1.15rem 1.25rem;
            min-height: 108px;
            border: 1px solid var(--line);
            border-radius: 6px;
            background: var(--card);
        }
        .metric-card .value {
            font-family: "Spectral", Georgia, serif;
            font-size: 2rem;
            line-height: 1;
            font-weight: 600;
            color: #050505;
        }
        .metric-card .label {
            font-size: .78rem;
            color: #665e52;
            margin-top: .8rem;
        }
        .narrative {
            border-left: 4px solid var(--blue);
            padding: .9rem 1rem;
            background: #fbfaf6;
            border-radius: 0 6px 6px 0;
            font-family: "Spectral", serif;
            font-size: 1.02rem;
            line-height: 1.45;
        }
        .integrative-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 2rem 2.2rem;
            min-height: 286px;
        }
        .integrative-card .question {
            font-family: "Spectral", Georgia, serif;
            font-size: 1.55rem;
            line-height: 1.48;
            color: #0d0c0a;
            margin: 1.1rem 0 1.8rem;
        }
        .integrative-card p {
            color: #4d463b;
            font-size: .98rem;
            line-height: 1.65;
            margin: 0;
        }
        .dimension-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-left: 3px solid var(--accent);
            border-radius: 5px;
            padding: 1.25rem 1.45rem;
            height: 176px;
            margin-bottom: 0;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .dimension-card .method {
            float: right;
            font-family: "IBM Plex Mono", monospace;
            font-size: .68rem;
            letter-spacing: .15em;
            text-transform: uppercase;
            color: var(--accent);
        }
        .dimension-card h3 {
            font-family: "Spectral", Georgia, serif !important;
            font-size: 1.45rem !important;
            margin: .55rem 0 1.25rem !important;
        }
        .dimension-card p {
            color: #5b544a;
            font-size: .98rem;
            line-height: 1.55;
            margin: 0;
            min-height: 3.05rem;
        }
        .dark-card {
            background: #26221b;
            color: #f8f2e7;
            border-radius: 5px;
            padding: 2rem 2.2rem;
            min-height: 260px;
        }
        .dark-card .eyebrow {color: #d58a2e;}
        .dark-card h2 {
            font-family: "Spectral", Georgia, serif !important;
            color: #fff8ed;
            font-size: 1.75rem !important;
            line-height: 1.35;
            margin: 1rem 0 1.6rem !important;
        }
        .dark-card p {
            color: #eadfca;
            font-size: .96rem;
            line-height: 1.65;
            margin: 0;
        }
        .finding-list-title {
            font-family: "IBM Plex Mono", monospace;
            font-size: .76rem;
            letter-spacing: .22em;
            color: var(--brown);
            text-transform: uppercase;
            margin: .2rem 0 1.1rem;
        }
        .finding-item {
            display: grid;
            grid-template-columns: 32px 1fr;
            gap: .9rem;
            align-items: start;
            margin: 0 0 1rem;
            color: #332e27;
            font-size: .97rem;
            line-height: 1.48;
        }
        .finding-number {
            width: 24px;
            height: 24px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #f5ead5;
            color: #a05d17;
            font-family: "IBM Plex Mono", monospace;
            font-size: .75rem;
        }
        .topic-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            margin: 0 0 .55rem;
        }
        .topic-copy {
            color: #5e5548;
            max-width: 940px;
            font-size: .95rem;
            line-height: 1.55;
            margin: 0 0 1.9rem;
        }
        .topic-bars-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1.55rem 3rem;
            margin-bottom: 1.35rem;
        }
        .topic-row {margin-bottom: 1rem;}
        .topic-row-head {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 1rem;
            align-items: end;
            margin-bottom: .35rem;
        }
        .topic-row-title {
            color: #090806;
            font-size: .86rem;
            font-weight: 700;
            line-height: 1.25;
        }
        .topic-row-meta {
            color: #7b705f;
            font-family: "IBM Plex Mono", monospace;
            font-size: .76rem;
            white-space: nowrap;
        }
        .topic-track {
            height: 8px;
            border-radius: 999px;
            background: #e5dccb;
            overflow: hidden;
        }
        .topic-fill {
            height: 100%;
            border-radius: 999px;
            min-width: 10px;
        }
        .topic-legend {
            display: flex;
            flex-wrap: wrap;
            gap: .85rem 1.05rem;
            align-items: center;
            margin: 1.3rem 0 2.6rem;
            color: #5e5548;
            font-size: .82rem;
        }
        .topic-legend-item {
            display: inline-flex;
            gap: .45rem;
            align-items: center;
        }
        .topic-legend-swatch {
            width: 13px;
            height: 13px;
            border-radius: 3px;
            display: inline-block;
        }
        .section-title-serif {
            font-family: "Spectral", Georgia, serif !important;
            color: #11100e;
            font-size: 1.65rem !important;
            line-height: 1.2;
            margin: 2.15rem 0 .75rem !important;
        }
        .section-explain {
            color: #5e5548;
            max-width: 860px;
            font-size: .92rem;
            line-height: 1.55;
            margin: 0 0 1rem;
        }
        .section-explain .good {color: #0b7f50; font-weight: 800;}
        .section-explain .warn {color: #c2410c; font-weight: 800;}
        .method-note {
            color: #6f6557;
            background: rgba(255, 255, 255, .42);
            border-left: 3px solid #b36b2c;
            border-radius: 8px;
            padding: .75rem .95rem;
            max-width: 940px;
            font-size: .84rem;
            line-height: 1.55;
            margin: .85rem 0 1.15rem;
        }
        .method-note code {
            background: rgba(234, 223, 204, .75);
            border-radius: 5px;
            padding: .08rem .28rem;
            color: #2b261f;
        }
        .plot-note {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            color: #8c806f;
            margin: .55rem 0 0;
        }
        @media (max-width: 900px) {
            .topic-bars-grid {grid-template-columns: 1fr;}
        }
        div[data-testid="stVerticalBlock"] {gap: 1rem;}
        div[data-testid="stHorizontalBlock"] {gap: 1rem;}
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 1px solid #d8cfc0;
            margin-bottom: 2.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 42px;
            padding: 0 1.25rem;
            color: #8a8070;
            font-size: .88rem;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {color: #11100e !important;}
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #1e1b16 !important;
            height: 2px !important;
        }
        .priority-card {
            padding: 1.35rem 1.5rem 1.2rem;
            border: 1px solid var(--line);
            border-left: 4px solid var(--accent);
            border-radius: 7px;
            background: #fbfaf6;
            margin-bottom: 1rem;
        }
        .priority-card h4 {
            margin: 0 0 .85rem;
            font-family: "Spectral", Georgia, serif;
            font-size: 1.18rem;
            line-height: 1.25;
            color: #11100e;
        }
        .priority-card p {
            margin: .9rem 0 0;
            color: #5e5548;
            font-size: .88rem;
            line-height: 1.55;
        }
        .chip {
            display: inline-block;
            padding: .25rem .7rem;
            margin: .16rem .22rem .16rem 0;
            border-radius: 999px;
            background: #eee7da;
            color: #51493e;
            font-size: .76rem;
            line-height: 1.25;
        }
        .priority-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .24em;
            text-transform: uppercase;
            color: var(--brown);
            margin: .2rem 0 .95rem;
        }
        .strategy-card {
            background: #211d17;
            border-radius: 7px;
            padding: 1.55rem 1.65rem;
            color: #f8f2e8;
            margin-bottom: 1rem;
        }
        .strategy-card .priority-kicker {
            color: #d58a2e;
            margin-top: 0;
        }
        .strategy-item {
            display: grid;
            grid-template-columns: 1.45rem 1fr;
            gap: .65rem;
            margin: 1rem 0;
        }
        .strategy-number {
            font-family: "Spectral", Georgia, serif;
            color: #d58a2e;
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1;
        }
        .strategy-title {
            color: #fbfaf6;
            font-weight: 800;
            font-size: .95rem;
            margin-bottom: .2rem;
        }
        .strategy-copy {
            color: #cfc5b7;
            font-size: .84rem;
            line-height: 1.45;
        }
        .role-def-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 7px;
            padding: 1.45rem 1.55rem;
        }
        .role-def-item {
            margin: .85rem 0;
        }
        .role-def-item h4 {
            margin: 0 0 .18rem;
            color: #2b261f;
            font-family: "IBM Plex Sans", sans-serif;
            font-size: .9rem;
            font-weight: 800;
        }
        .role-def-item p {
            margin: 0;
            color: #7a7062;
            font-size: .78rem;
            line-height: 1.35;
        }
        div[data-testid="stPlotlyChart"] {
            border: 1px solid var(--line); border-radius: 6px;
            background: #fbfaf6; overflow: hidden;
        }
        .network-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            margin: 0 0 .6rem;
        }
        .network-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 385px;
            gap: 1.5rem;
            align-items: start;
        }
        .network-controls {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.25rem;
            margin: 0 0 1rem;
        }
        .dimension-pills {
            display: inline-flex;
            padding: .25rem;
            background: #e7dfd0;
            border-radius: 6px;
        }
        .dimension-pill {
            display: inline-block;
            padding: .55rem 1rem;
            border-radius: 5px;
            font-size: .84rem;
            color: #665e52;
            font-weight: 600;
        }
        .dimension-pill.active {
            background: #26221b;
            color: #fbf7ef;
            box-shadow: 0 2px 8px rgba(38,34,27,.16);
        }
        .network-filter-grid {
            display: grid;
            grid-template-columns: auto auto;
            gap: 1.1rem;
            align-items: end;
        }
        .community-chips {
            display: flex;
            gap: .45rem;
            align-items: center;
        }
        .community-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 42px;
            height: 36px;
            padding: 0 .75rem;
            border-radius: 6px;
            color: #fff;
            font-weight: 700;
            font-size: .82rem;
        }
        div[data-testid="stPills"] {
            margin-top: -.15rem;
        }
        div[data-testid="stPills"] button {
            min-width: 42px !important;
            height: 36px !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
        }
        .role-select-label {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            margin-bottom: .55rem;
        }
        .network-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: .75rem .75rem .55rem;
        }
        .network-card svg {
            display: block;
            width: 100%;
            height: auto;
            min-height: 520px;
        }
        .network-note {
            border-top: 1px solid #e4daca;
            margin-top: .25rem;
            padding: .7rem .4rem .2rem;
            color: #9a8d7b;
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
        }
        .network-side-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 1.45rem 1.55rem;
        }
        .legend-title {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            color: var(--brown);
            text-transform: uppercase;
            margin-bottom: 1.2rem;
        }
        .legend-item {
            display: grid;
            grid-template-columns: 18px 1fr;
            gap: .75rem;
            align-items: start;
            margin-bottom: 1rem;
            color: #332e27;
            font-size: .9rem;
            line-height: 1.35;
        }
        .legend-swatch {
            width: 14px;
            height: 14px;
            border-radius: 4px;
            margin-top: .17rem;
        }
        .legend-divider {
            height: 1px;
            background: #e2d8c7;
            margin: 1.4rem 0 1.3rem;
        }
        .legend-note {
            color: #6b6256;
            font-size: .9rem;
            line-height: 1.5;
            margin-bottom: 1.2rem;
        }
        .legend-hint {
            color: #8d8171;
            font-size: .86rem;
            font-style: italic;
            line-height: 1.45;
        }
        div[data-testid="stSelectbox"] label {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
        }
        div[data-testid="stRadio"] > label {display: none;}
        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: inline-flex;
            gap: 0;
            padding: .25rem;
            background: #e7dfd0;
            border-radius: 6px;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            min-height: 36px;
            padding: 0 .92rem;
            margin: 0;
            border-radius: 5px;
            color: #665e52;
            font-weight: 700;
            font-size: .84rem;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
            background: #26221b;
            color: #fbf7ef !important;
            box-shadow: 0 2px 8px rgba(38,34,27,.16);
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) *,
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {
            color: #fbf7ef !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
            display: none;
        }
        @media (max-width: 1050px) {
            .network-row {grid-template-columns: 1fr;}
            .network-controls {align-items: stretch; flex-direction: column;}
            .network-filter-grid {grid-template-columns: 1fr;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(meta: dict) -> None:
    metrics = [
        (f"{meta['dataReviews']:,}".replace(",", "."), "data review Google Maps"),
        (f"{meta['ulasanTeksValid']:,}".replace(",", "."), "ulasan teks valid"),
        (meta["jumlahObjek"], "objek cagar budaya"),
        (meta["jumlahTopikFinal"], "topik final"),
        (meta["jumlahKomunitas"], "komunitas ko-reviewer"),
    ]
    columns = st.columns(len(metrics))
    for column, (value, label) in zip(columns, metrics):
        column.markdown(
            f'<div class="metric-card"><div class="value">{value}</div>'
            f'<div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )


def topic_bars_html(topics: pd.DataFrame) -> str:
    ordered = topics.sort_values("n", ascending=False).reset_index(drop=True)
    max_n = max(float(ordered["n"].max()), 1)

    def render_row(row: pd.Series) -> str:
        color = TOPIC_RUMPUN_COLORS.get(str(row["rumpun"]), "#7E4FC0")
        width = max(float(row["n"]) / max_n * 100, 1)
        pct = f'{float(row["pct"]):.1f}'.replace(".", ",")
        return (
            '<div class="topic-row">'
            '<div class="topic-row-head">'
            f'<div class="topic-row-title">{html.escape(str(row["label_short"]))}</div>'
            f'<div class="topic-row-meta">{int(row["n"])} · {pct}%</div>'
            '</div>'
            '<div class="topic-track">'
            f'<div class="topic-fill" style="width:{width:.2f}%; background:{color}"></div>'
            '</div>'
            '</div>'
        )

    left = ordered.iloc[::2]
    right = ordered.iloc[1::2]
    left_html = "".join(render_row(row) for _, row in left.iterrows())
    right_html = "".join(render_row(row) for _, row in right.iterrows())
    legend_html = "".join(
        '<span class="topic-legend-item">'
        f'<span class="topic-legend-swatch" style="background:{color}"></span>'
        f'{html.escape(label)}'
        '</span>'
        for label, color in TOPIC_RUMPUN_COLORS.items()
    )
    return (
        '<div class="topic-bars-grid">'
        f'<div>{left_html}</div>'
        f'<div>{right_html}</div>'
        '</div>'
        f'<div class="topic-legend">{legend_html}</div>'
    )


def topic_color(label: str) -> str:
    text = str(label).lower()
    if any(token in text for token in ["religi", "gereja", "masjid", "ampel"]):
        return "#1e865a"
    if any(token in text for token in ["kuliner", "restoran", "hotel", "zangrandi"]):
        return "#c97a2b"
    if any(
        token in text
        for token in ["fasilitas", "parkir", "jam", "wifi", "coworking", "keluhan", "operasional"]
    ):
        return "#c2410c"
    if any(token in text for token in ["museum", "monumen", "edukasi", "bank", "monkasel", "sejarah"]):
        return "#2c66c9"
    if any(token in text for token in ["balai", "bangunan", "kolonial", "grahadi", "heritage", "seni", "budaya"]):
        return "#7e4fc0"
    return "#7e4fc0"


def spatial_group(lat: float, lon: float) -> str:
    if pd.isna(lat) or pd.isna(lon):
        return "Koordinat belum tersedia"

    lat = float(lat)
    lon = float(lon)
    if lat <= -7.276 or lon <= 112.733:
        return "Selatan–Barat · Darmo–Rahmat"
    if lat >= -7.246:
        return "Utara · Kota Lama–Ampel"
    if lon >= 112.748:
        return "Timur · Monkasel–Gelora"
    return "Pusat · Tunjungan–Grahadi"


def spatial_color(lat: float, lon: float) -> str:
    return SPATIAL_COLORS[spatial_group(lat, lon)]


def safe_float(value: float) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def build_network_svg(
    objects: pd.DataFrame,
    edges: pd.DataFrame,
    color_mode: str,
    community_colors: dict[int, str],
) -> str:
    """Render a Claude-style static SVG network card."""
    width, height = 960, 620
    centers = {
        0: (190, 185),
        1: (760, 180),
        2: (270, 455),
        3: (560, 330),
    }
    positions: dict[str, tuple[float, float]] = {}
    ordered = objects.sort_values(["komunitas", "wd"], ascending=[True, False])

    for community_id, group in ordered.groupby("komunitas"):
        cx, cy = centers.get(int(community_id), (width / 2, height / 2))
        group = group.sort_values("wd", ascending=False).reset_index(drop=True)
        count = max(len(group), 1)
        for rank, row in group.iterrows():
            if rank == 0:
                x, y = cx, cy
            else:
                angle = (2 * math.pi * (rank - 1) / max(count - 1, 1)) + int(community_id) * 0.42
                radius = 55 + 15 * ((rank - 1) % 3)
                x = cx + math.cos(angle) * radius
                y = cy + math.sin(angle) * radius
            positions[str(row["nama"])] = (x, y)

    max_wd = max(float(objects["wd"].max()), 1)
    max_bc = max(float(objects["bc"].max()), 0.001)
    object_lookup = objects.set_index("nama").to_dict("index")
    visible_edges = edges[
        edges["Source"].isin(positions) & edges["Target"].isin(positions)
    ].copy()
    if not visible_edges.empty:
        threshold = max(2, int(visible_edges["Weight"].quantile(0.62)))
        visible_edges = visible_edges[
            visible_edges["Weight"] >= threshold
        ].sort_values("Weight", ascending=True)

    edge_markup = []
    for row in visible_edges.itertuples():
        x1, y1 = positions[row.Source]
        x2, y2 = positions[row.Target]
        width_line = 0.55 + min(float(row.Weight), 30) / 30 * 1.6
        edge_markup.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#d8d0c2" stroke-width="{width_line:.2f}" stroke-opacity=".82" />'
        )

    node_markup = []
    for row in ordered.itertuples():
        name = str(row.nama)
        x, y = positions[name]
        radius = 10 + math.sqrt(float(row.wd) / max_wd) * 18
        ring_width = 1.4 + float(row.bc) / max_bc * 4.2
        if color_mode == "Diskursif · Topik":
            fill = topic_color(str(row.topikUtama))
        elif color_mode == "Spasial · Kawasan":
            fill = spatial_color(float(row.lat), float(row.lon))
        else:
            fill = community_colors.get(int(row.komunitas), "#8754C9")
        title = html.escape(
            f"{name} | WD {int(row.wd)} | BC {float(row.bc):.3f} | "
            f"{row.komunitas_nama} | {row.peran}"
        )
        node_markup.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{fill}" '
            f'stroke="#3b332b" stroke-width="{ring_width:.2f}" opacity=".96">'
            f"<title>{title}</title></circle>"
        )

    return textwrap.dedent(f"""
    <div class="network-card">
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="Jaringan ko-reviewer cagar budaya Surabaya">
        <rect x="0" y="0" width="{width}" height="{height}" rx="4" fill="#fbfaf6"/>
        <g>{''.join(edge_markup)}</g>
        <g>{''.join(node_markup)}</g>
      </svg>
      <div class="network-note">
        Ukuran node = weighted degree · ketebalan cincin = betweenness · hover node untuk profil ringkas.
      </div>
    </div>
    """).strip()


def _role_summary(role: str) -> str:
    role_text = str(role)
    lowered = role_text.lower()
    if "bridge" in lowered or "penghubung" in lowered:
        return "Simpul penghubung lintas komunitas; posisinya penting untuk membaca keterkaitan pengalaman antarobjek."
    if "issue" in lowered or "keluhan" in lowered:
        return "Objek dengan isu pengalaman yang relatif menonjol, sehingga relevan untuk dilihat sebagai prioritas perbaikan."
    if "anchor" in lowered or "positif" in lowered:
        return "Objek dengan posisi pengalaman yang kuat; sentimen dan identitas topiknya relatif jelas."
    return "Objek ini dibaca melalui gabungan posisi struktural, topik dominan, dan komposisi sentimen pengunjung."


def build_network_panel(
    objects: pd.DataFrame,
    edges: pd.DataFrame,
    color_mode: str,
    community_colors: dict[int, str],
    communities: pd.DataFrame,
) -> str:
    """Render an interactive SVG network with a click-to-open profile card."""
    width, height = 960, 620
    centers = {
        0: (190, 185),
        1: (760, 180),
        2: (270, 455),
        3: (560, 330),
    }
    positions: dict[str, tuple[float, float]] = {}
    ordered = objects.sort_values(["komunitas", "wd"], ascending=[True, False])

    for community_id, group in ordered.groupby("komunitas"):
        cx, cy = centers.get(int(community_id), (width / 2, height / 2))
        group = group.sort_values("wd", ascending=False).reset_index(drop=True)
        count = max(len(group), 1)
        for rank, row in group.iterrows():
            if rank == 0:
                x, y = cx, cy
            else:
                angle = (2 * math.pi * (rank - 1) / max(count - 1, 1)) + int(community_id) * 0.42
                radius = 55 + 15 * ((rank - 1) % 3)
                x = cx + math.cos(angle) * radius
                y = cy + math.sin(angle) * radius
            positions[str(row["nama"])] = (x, y)

    max_wd = max(float(objects["wd"].max()), 1)
    max_bc = max(float(objects["bc"].max()), 0.001)
    visible_edges = edges[
        edges["Source"].isin(positions) & edges["Target"].isin(positions)
    ].copy()
    if not visible_edges.empty:
        threshold = max(2, int(visible_edges["Weight"].quantile(0.62)))
        visible_edges = visible_edges[
            visible_edges["Weight"] >= threshold
        ].sort_values("Weight", ascending=True)

    edge_markup = []
    for row in visible_edges.itertuples():
        x1, y1 = positions[row.Source]
        x2, y2 = positions[row.Target]
        width_line = 0.55 + min(float(row.Weight), 30) / 30 * 1.6
        edge_markup.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#d8d0c2" stroke-width="{width_line:.2f}" stroke-opacity=".82" />'
        )

    profiles: dict[str, dict] = {}
    node_markup = []
    for node_idx, row in enumerate(ordered.itertuples()):
        node_id = f"node-{node_idx}"
        name = str(row.nama)
        x, y = positions[name]
        radius = 10 + math.sqrt(float(row.wd) / max_wd) * 18
        ring_width = 1.4 + float(row.bc) / max_bc * 4.2
        community_id = int(row.komunitas)
        community_color = community_colors.get(community_id, "#8754C9")
        if color_mode == "Diskursif · Topik":
            fill = topic_color(str(row.topikUtama))
        elif color_mode == "Spasial · Kawasan":
            fill = spatial_color(float(row.lat), float(row.lon))
        else:
            fill = community_color
        title = html.escape(
            f"{name} | WD {int(row.wd)} | BC {float(row.bc):.3f} | "
            f"{row.komunitas_nama} | {row.peran}"
        )
        node_markup.append(
            f'<circle class="network-node" data-node-id="{node_id}" '
            f'cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{fill}" '
            f'stroke="#3b332b" stroke-width="{ring_width:.2f}" opacity=".96">'
            f"<title>{title}</title></circle>"
        )
        profiles[node_id] = {
            "name": name,
            "community": f"K-{community_id} · {str(row.komunitas_nama)}",
            "communityColor": community_color,
            "profileColor": fill,
            "role": str(row.peran),
            "roleSummary": _role_summary(str(row.peran)),
            "topic": str(row.topikUtama),
            "topicPct": float(row.topikUtamaPct),
            "topicSecondary": str(row.topikPendamping),
            "spatial": spatial_group(float(row.lat), float(row.lon)),
            "lat": safe_float(row.lat),
            "lon": safe_float(row.lon),
            "pos": float(row.pos),
            "netral": float(row.netral),
            "neg": float(row.neg),
            "wd": float(row.wd),
            "bc": float(row.bc),
            "totalValid": int(row.total_valid),
            "uniqueReviewer": int(row.unique_reviewer),
            "avgRating": float(row.avg_rating),
        }

    legend_html = network_legend_html(color_mode, communities)
    profiles_json = json.dumps(profiles, ensure_ascii=False)
    legend_json = json.dumps(legend_html, ensure_ascii=False)

    template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Spectral:wght@500;600;700&display=swap');
* { box-sizing: border-box; }
body { margin: 0; background: #eee9de; color: #211d17; font-family: "IBM Plex Sans", sans-serif; }
.network-panel { display: grid; grid-template-columns: minmax(0, 2.35fr) 1fr; gap: 1.35rem; align-items: start; }
.network-card, .network-side-card, .profile-card {
  background: #fbfaf6; border: 1px solid #ded5c6; border-radius: 6px; overflow: hidden;
}
.network-card { padding: 0.65rem 0.65rem 0; }
.network-card svg { width: 100%; height: 620px; display: block; }
.network-note {
  border-top: 1px solid #eadfcc; padding: .75rem .5rem .8rem;
  color: #9a8b77; font-family: "IBM Plex Mono", monospace; font-size: .72rem;
}
.network-node { cursor: pointer; transition: opacity .15s ease, stroke-width .15s ease, filter .15s ease; }
.network-node:hover { opacity: 1; filter: drop-shadow(0 3px 5px rgba(38,34,27,.22)); }
.network-node.active { stroke-width: 5.5px; }
.network-side-card { padding: 1.45rem; min-height: 248px; }
.legend-title {
  font-family: "IBM Plex Mono", monospace; font-size: .72rem; letter-spacing: .22em;
  text-transform: uppercase; color: #a05d17; margin-bottom: 1.05rem;
}
.legend-item { display: flex; gap: .75rem; align-items: flex-start; margin: .78rem 0; color: #332d25; font-size: .9rem; line-height: 1.35; }
.legend-swatch { width: 13px; height: 13px; flex: 0 0 13px; border-radius: 3px; margin-top: .14rem; }
.legend-divider { border-top: 1px solid #eadfcc; margin: 1.3rem 0 1rem; }
.legend-note { color: #6d6254; font-size: .9rem; line-height: 1.55; }
.legend-hint { color: #8c7d69; font-size: .86rem; font-style: italic; line-height: 1.45; margin-top: 1rem; }
.profile-card { padding: 0; }
.profile-head {
  position: relative; background: var(--profile-color, #c9772f); color: #fffaf0;
  padding: 1.15rem 1.35rem 1.25rem;
}
.profile-close {
  position: absolute; right: .85rem; top: .8rem; width: 28px; height: 28px; border: 0;
  border-radius: 999px; background: rgba(255,255,255,.22); color: #fffaf0;
  font-size: 1.25rem; cursor: pointer; line-height: 1;
}
.profile-head h3 {
  font-family: "Spectral", Georgia, serif; font-size: 1.28rem; line-height: 1.18;
  margin: 0 2rem .7rem 0; color: #fffaf0;
}
.profile-community {
  font-family: "IBM Plex Mono", monospace; font-size: .74rem; letter-spacing: .08em;
  font-weight: 700; line-height: 1.35;
}
.profile-body { padding: 1.2rem 1.35rem 1.35rem; }
.role-pill {
  display: inline-block; padding: .34rem .8rem; border-radius: 999px;
  background: #eee3cf; color: #8b5a1a; font-family: "IBM Plex Mono", monospace;
  font-size: .72rem; font-weight: 700; margin-bottom: .9rem;
}
.profile-summary { color: #6d6254; font-size: .9rem; line-height: 1.55; margin: 0 0 1.25rem; }
.profile-section-title {
  font-family: "IBM Plex Mono", monospace; font-size: .68rem; letter-spacing: .2em;
  text-transform: uppercase; color: #a05d17; margin: 1.1rem 0 .4rem;
}
.profile-main { font-weight: 800; color: #2e2922; margin-bottom: .18rem; }
.profile-sub { color: #766b5d; font-size: .86rem; line-height: 1.4; }
.sentiment-bar { display: flex; height: 11px; border-radius: 999px; overflow: hidden; background: #eadfcc; margin: .65rem 0 .45rem; }
.sent-pos { background: #2BA84A; }
.sent-neu { background: #FFC20A; }
.sent-neg { background: #E0313E; }
.sentiment-labels {
  display: flex; justify-content: space-between; gap: .4rem; color: #6d6254;
  font-family: "IBM Plex Mono", monospace; font-size: .68rem; line-height: 1.35;
}
.metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: .65rem; margin-top: .7rem; }
.mini-metric { background: #eee3cf; border-radius: 5px; padding: .75rem; }
.mini-metric strong { display: block; font-family: "Spectral", Georgia, serif; font-size: 1.35rem; line-height: 1; }
.mini-metric span { display: block; margin-top: .35rem; color: #756b5c; font-size: .76rem; }
.profile-foot {
  border-top: 1px solid #eadfcc; margin-top: 1rem; padding-top: .8rem;
  display: flex; justify-content: space-between; color: #8b806f;
  font-family: "IBM Plex Mono", monospace; font-size: .72rem;
}
@media (max-width: 1050px) { .network-panel { grid-template-columns: 1fr; } .network-card svg { height: 520px; } }
</style>
<div class="network-panel">
  <div class="network-card">
    <svg viewBox="0 0 __WIDTH__ __HEIGHT__" role="img" aria-label="Jaringan ko-reviewer cagar budaya Surabaya">
      <rect x="0" y="0" width="__WIDTH__" height="__HEIGHT__" rx="4" fill="#fbfaf6"/>
      <g>__EDGES__</g>
      <g>__NODES__</g>
    </svg>
    <div class="network-note">
      Ukuran node = weighted degree · ketebalan cincin = betweenness · klik node untuk membuka profil objek.
    </div>
  </div>
  <div id="profile-panel">__LEGEND__</div>
</div>
<script>
const profiles = __PROFILES_JSON__;
const legendHtml = __LEGEND_JSON__;
const panel = document.getElementById("profile-panel");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pct(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function coordText(p) {
  if (p.lat === null || p.lon === null || Number.isNaN(Number(p.lat)) || Number.isNaN(Number(p.lon))) {
    return "Koordinat belum tersedia";
  }
  return `${Number(p.lat).toFixed(5)}, ${Number(p.lon).toFixed(5)}`;
}

function renderLegend() {
  panel.innerHTML = legendHtml;
  document.querySelectorAll(".network-node").forEach(node => node.classList.remove("active"));
}

function renderProfile(nodeId) {
  const p = profiles[nodeId];
  if (!p) return;
  document.querySelectorAll(".network-node").forEach(node => node.classList.remove("active"));
  document.querySelector(`[data-node-id="${nodeId}"]`)?.classList.add("active");
  panel.innerHTML = `
    <article class="profile-card" style="--profile-color:${escapeHtml(p.profileColor || p.communityColor)}">
      <div class="profile-head">
        <button class="profile-close" type="button" aria-label="Tutup profil">×</button>
        <h3>${escapeHtml(p.name)}</h3>
        <div class="profile-community">${escapeHtml(p.community)}</div>
      </div>
      <div class="profile-body">
        <div class="role-pill">${escapeHtml(p.role)}</div>
        <p class="profile-summary">${escapeHtml(p.roleSummary)}</p>

        <div class="profile-section-title">Diskursif · Topik</div>
        <div class="profile-main">${escapeHtml(p.topic)}</div>
        <div class="profile-sub">Topik dominan ${pct(p.topicPct)} · pendamping: ${escapeHtml(p.topicSecondary)}</div>

        <div class="profile-section-title">Spasial · Kawasan</div>
        <div class="profile-main">${escapeHtml(p.spatial)}</div>
        <div class="profile-sub">Koordinat: ${escapeHtml(coordText(p))}</div>

        <div class="profile-section-title">Afektif · Sentimen</div>
        <div class="sentiment-bar">
          <div class="sent-pos" style="width:${Number(p.pos || 0)}%"></div>
          <div class="sent-neu" style="width:${Number(p.netral || 0)}%"></div>
          <div class="sent-neg" style="width:${Number(p.neg || 0)}%"></div>
        </div>
        <div class="sentiment-labels">
          <span>▲ ${pct(p.pos)} positif</span>
          <span>${pct(p.netral)} netral</span>
          <span>▼ ${pct(p.neg)} negatif</span>
        </div>

        <div class="profile-section-title">Struktural · SNA</div>
        <div class="metric-grid">
          <div class="mini-metric"><strong>${Math.round(Number(p.wd || 0))}</strong><span>Weighted degree</span></div>
          <div class="mini-metric"><strong>${Number(p.bc || 0).toFixed(3)}</strong><span>Betweenness</span></div>
        </div>
        <div class="profile-foot">
          <span>${Number(p.totalValid || 0).toLocaleString("id-ID")} ulasan teks</span>
          <span>★ ${Number(p.avgRating || 0).toFixed(2)}</span>
        </div>
      </div>
    </article>
  `;
  panel.querySelector(".profile-close")?.addEventListener("click", renderLegend);
}

document.querySelectorAll(".network-node").forEach(node => {
  node.addEventListener("click", () => renderProfile(node.dataset.nodeId));
});
</script>
"""
    return (
        template.replace("__WIDTH__", str(width))
        .replace("__HEIGHT__", str(height))
        .replace("__EDGES__", "".join(edge_markup))
        .replace("__NODES__", "".join(node_markup))
        .replace("__LEGEND__", legend_html)
        .replace("__PROFILES_JSON__", profiles_json)
        .replace("__LEGEND_JSON__", legend_json)
    )


def community_legend_html(communities: pd.DataFrame) -> str:
    items = []
    for row in communities.sort_values("id").itertuples():
        items.append(
            '<div class="legend-item">'
            f'<span class="legend-swatch" style="background:{row.color}"></span>'
            f'<span>K-{int(row.id)} · {html.escape(str(row.nama))}</span>'
            '</div>'
        )
    return (
        '<div class="network-side-card">'
        '<div class="legend-title">Komunitas Louvain</div>'
        f'{"".join(items)}'
        '<div class="legend-divider"></div>'
        '<div class="legend-note">'
        'Empat komunitas ko-reviewer. Cincin tebal = betweenness tinggi '
        '(simpul penghubung).'
        '</div>'
        '<div class="legend-hint">'
        'Arahkan kursor ke node untuk membaca profil ringkas objek.'
        '</div>'
        '</div>'
    )


def network_legend_html(color_mode: str, communities: pd.DataFrame) -> str:
    if color_mode == "Spasial · Kawasan":
        items = []
        for label, color in SPATIAL_COLORS.items():
            items.append(
                '<div class="legend-item">'
                f'<span class="legend-swatch" style="background:{color}"></span>'
                f'<span>{html.escape(label)}</span>'
                '</div>'
            )
        return (
            '<div class="network-side-card">'
            '<div class="legend-title">Kawasan Spasial</div>'
            f'{"".join(items)}'
            '<div class="legend-divider"></div>'
            '<div class="legend-note">'
            'Warna = kelompok lokasi geografis objek berdasarkan koordinat Google Maps. '
            'Layer ini membantu membaca apakah kedekatan spasial ikut membentuk pola jaringan.'
            '</div>'
            '<div class="legend-hint">'
            'Klik node untuk membuka profil integratif objek.'
            '</div>'
            '</div>'
        )

    if color_mode == "Diskursif · Topik":
        topic_groups = [
            ("Religi", "#1e865a"),
            ("Kuliner & Hospitality", "#c97a2b"),
            ("Museum & Edukasi", "#2c66c9"),
            ("Heritage & Identitas Kota", "#7e4fc0"),
            ("Fasilitas & Operasional", "#c2410c"),
        ]
        items = []
        for label, color in topic_groups:
            items.append(
                '<div class="legend-item">'
                f'<span class="legend-swatch" style="background:{color}"></span>'
                f'<span>{html.escape(label)}</span>'
                '</div>'
            )
        return (
            '<div class="network-side-card">'
            '<div class="legend-title">Rumpun Topik Utama</div>'
            f'{"".join(items)}'
            '<div class="legend-divider"></div>'
            '<div class="legend-note">'
            'Warna = rumpun topik terbesar pada ulasan objek tersebut.'
            '</div>'
            '<div class="legend-hint">'
            'Arahkan kursor ke node untuk membaca profil ringkas objek.'
            '</div>'
            '</div>'
        )

    return community_legend_html(communities)


def community_filter_control(communities: pd.DataFrame) -> list[int]:
    community_options = [int(row.id) for row in communities.sort_values("id").itertuples()]

    if hasattr(st, "pills"):
        selected = st.pills(
            "Filter Komunitas",
            community_options,
            default=community_options,
            format_func=lambda value: f"K-{int(value)}",
            selection_mode="multi",
            label_visibility="collapsed",
            key="network_community_filter",
        )
    else:
        selected = st.multiselect(
            "Filter Komunitas",
            community_options,
            default=community_options,
            format_func=lambda value: f"K-{int(value)}",
            label_visibility="collapsed",
            key="network_community_filter",
        )

    selected = list(selected) if selected else community_options
    return [int(value) for value in selected]


def network_figure(
    objects: pd.DataFrame,
    communities: pd.DataFrame,
    edges: pd.DataFrame,
    color_mode: str,
) -> go.Figure:
    centers = {
        0: (-0.85, 0.55),
        1: (0.9, 0.62),
        2: (-0.65, -0.7),
        3: (0.25, -0.05),
    }
    ordered = objects.sort_values(["komunitas", "wd"], ascending=[True, False]).copy()
    positions: dict[str, tuple[float, float]] = {}

    for community_id, group in ordered.groupby("komunitas"):
        cx, cy = centers[int(community_id)]
        total = max(len(group), 1)
        for rank, row in enumerate(group.itertuples()):
            angle = 6.283 * rank / total + community_id * 0.55
            radius = 0.12 + 0.055 * rank
            positions[row.nama] = (
                cx + radius * __import__("math").cos(angle),
                cy + radius * __import__("math").sin(angle),
            )

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_mid_x: list[float] = []
    edge_mid_y: list[float] = []
    edge_hover: list[str] = []
    visible_edges = edges[
        edges["Source"].isin(positions) & edges["Target"].isin(positions)
    ]
    for row in visible_edges.itertuples():
        source, target = row.Source, row.Target
        if source not in positions or target not in positions:
            continue
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_mid_x.append((x0 + x1) / 2)
        edge_mid_y.append((y0 + y1) / 2)
        edge_hover.append(
            f"<b>{source}</b> ↔ <b>{target}</b><br>"
            f"Ko-reviewer bersama: {int(row.Weight)}"
        )

    if color_mode == "Sentimen positif":
        marker_color = ordered["pos"]
        colorscale = "RdYlGn"
        colorbar = {"title": "% positif"}
        showscale = True
    elif color_mode == "Peran objek":
        roles = sorted(ordered["peran"].unique())
        role_map = {role: index for index, role in enumerate(roles)}
        marker_color = ordered["peran"].map(role_map)
        colorscale = "Turbo"
        colorbar = {
            "title": "Peran",
            "tickvals": list(role_map.values()),
            "ticktext": roles,
        }
        showscale = True
    else:
        marker_color = ordered["komunitas_warna"]
        colorscale = None
        colorbar = None
        showscale = False

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"width": 0.8, "color": "rgba(73,64,52,.25)"},
            hoverinfo="skip",
            name="Edge ko-reviewer",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=edge_mid_x,
            y=edge_mid_y,
            mode="markers",
            marker={"size": 8, "color": "rgba(0,0,0,0)"},
            text=edge_hover,
            hovertemplate="%{text}<extra></extra>",
            name="Bobot edge",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[positions[name][0] for name in ordered["nama"]],
            y=[positions[name][1] for name in ordered["nama"]],
            mode="markers",
            marker={
                "size": (9 + ordered["wd"].pow(0.5) * 2.1).tolist(),
                "color": marker_color,
                "colorscale": colorscale,
                "showscale": showscale,
                "colorbar": colorbar,
                "line": {
                    "width": (1 + ordered["bc"] * 10).tolist(),
                    "color": "#2d2821",
                },
                "opacity": 0.9,
            },
            customdata=ordered[
                ["nama", "komunitas_nama", "peran", "topikUtama", "wd", "bc", "pos", "neg"]
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Peran: %{customdata[2]}<br>Topik: %{customdata[3]}<br>"
                "WD: %{customdata[4]} · BC: %{customdata[5]:.3f}<br>"
                "Positif %{customdata[6]:.1f}% · Negatif %{customdata[7]:.1f}%<extra></extra>"
            ),
            name="Objek",
        )
    )
    fig.update_layout(
        height=650,
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        showlegend=False,
    )
    return fig


def quadrant_figure(objects: pd.DataFrame, color_map: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    x_median = objects["wd"].median()
    y_median = objects["balance"].median()
    x_min = min(0, float(objects["wd"].min()) - 8)
    x_max = float(objects["wd"].max()) * 1.15
    y_min = float(objects["balance"].min()) - 5
    y_max = float(objects["balance"].max()) + 5
    bc_max = max(float(objects["bc"].max()), 0.001)
    bridge_names = set(objects.nlargest(8, "bc")["nama"])

    fig.add_shape(
        type="rect",
        x0=x_median,
        x1=x_max,
        y0=y_median,
        y1=y_max,
        fillcolor="rgba(44, 138, 98, .10)",
        line_width=0,
        layer="below",
    )
    fig.add_shape(
        type="rect",
        x0=x_median,
        x1=x_max,
        y0=y_min,
        y1=y_median,
        fillcolor="rgba(201, 54, 10, .07)",
        line_width=0,
        layer="below",
    )

    for community_id, group in objects.sort_values("komunitas").groupby("komunitas"):
        sizes = 10 + (group["bc"].fillna(0) / bc_max) * 50
        symbols = [
            "star" if str(name) in bridge_names else "circle"
            for name in group["nama"]
        ]
        labels = (
            group["nama"]
            .str.replace("Monumen dan Museum ", "", regex=False)
            .str.replace("Kawasan ", "", regex=False)
            .str.slice(0, 20)
        )
        community_name = str(group["komunitas_nama"].iloc[0])
        fig.add_trace(
            go.Scatter(
                x=group["wd"],
                y=group["balance"],
                mode="markers+text",
                name=f"Kom.{int(community_id)} – {community_name}",
                text=labels,
                textposition="top right",
                textfont={"size": 10, "color": "#222"},
                customdata=group[["peran", "topikUtama", "pos", "neg", "bc"]],
                marker={
                    "size": sizes,
                    "symbol": symbols,
                    "color": NOTEBOOK_COMMUNITY_COLORS.get(int(community_id), "#999999"),
                    "opacity": 0.78,
                    "line": {"color": "#1A1A1A", "width": 1.0},
                },
                hovertemplate=(
                    "<b>%{text}</b><br>%{customdata[0]}<br>"
                    "Topik: %{customdata[1]}<br>"
                    "WD: %{x:.0f}<br>Balance: %{y:.1f}<br>"
                    "Positif: %{customdata[2]:.1f}% · Negatif: %{customdata[3]:.1f}%<br>"
                    "Betweenness: %{customdata[4]:.3f}<extra></extra>"
                ),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Bridge node (BC tinggi)",
            marker={
                "symbol": "star",
                "size": 16,
                "color": "gray",
                "line": {"color": "#1A1A1A", "width": 1},
            },
            hoverinfo="skip",
        )
    )

    fig.add_vline(x=x_median, line_dash="dash", line_color="#a89d8c", line_width=1)
    fig.add_hline(y=y_median, line_dash="dash", line_color="#a89d8c", line_width=1)
    fig.add_annotation(
        x=x_min + (x_max - x_min) * 0.97,
        y=y_min + (y_max - y_min) * 0.96,
        text="ANCHOR<br>sentral & diapresiasi",
        showarrow=False,
        xanchor="right",
        yanchor="top",
        font={"family": "IBM Plex Sans", "size": 13, "color": "#1d6f63"},
    )
    fig.add_annotation(
        x=x_min + (x_max - x_min) * 0.97,
        y=y_min + (y_max - y_min) * 0.04,
        text="ISSUE AMPLIFIER<br>sentral tapi bermasalah",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font={"family": "IBM Plex Sans", "size": 13, "color": "#b5232f"},
    )
    fig.add_annotation(
        x=x_min + (x_max - x_min) * 0.03,
        y=y_min + (y_max - y_min) * 0.96,
        text="NICHE POSITIVE<br>niche tapi disukai",
        showarrow=False,
        xanchor="left",
        yanchor="top",
        font={"family": "IBM Plex Sans", "size": 13, "color": "#4361EE"},
    )
    fig.add_annotation(
        x=x_min + (x_max - x_min) * 0.03,
        y=y_min + (y_max - y_min) * 0.04,
        text="PERIPHERAL<br>kurang sentral & lemah",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font={"family": "IBM Plex Sans", "size": 13, "color": "#6c757d"},
    )
    fig.add_annotation(
        x=x_max,
        y=y_min - ((y_max - y_min) * 0.09),
        text="Weighted Degree (sentralitas ko-kunjungan) →",
        showarrow=False,
        xanchor="right",
        yanchor="top",
        font={"family": "IBM Plex Sans", "size": 12, "color": "#3b342b"},
    )
    fig.update_layout(
        height=720,
        title={
            "text": (
                "Posisi Objek dalam Ekosistem: Sentralitas × Sentimen<br>"
                "<sup>ukuran bubble = betweenness · ★ = bridge node · garis = median</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20, "color": "#11100e"},
        },
        margin={"l": 70, "r": 28, "t": 90, "b": 82},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fbfaf6",
        legend={
            "orientation": "v",
            "y": 0.02,
            "x": 0.01,
            "xanchor": "left",
            "yanchor": "bottom",
            "bgcolor": "rgba(255,255,255,.88)",
            "bordercolor": "#d8d0c2",
            "borderwidth": 1,
            "font": {"size": 11},
            "title": None,
        },
        xaxis={
            "title": "Weighted Degree (sentralitas ko-kunjungan) →",
            "range": [x_min, x_max],
            "gridcolor": "rgba(0,0,0,.10)",
            "zeroline": False,
            "showticklabels": True,
        },
        yaxis={
            "title": "Sentiment Balance  (% positif − % negatif) →",
            "range": [y_min, y_max],
            "gridcolor": "rgba(0,0,0,.10)",
            "zeroline": False,
            "showticklabels": True,
        },
        font={"family": "IBM Plex Sans", "color": "#3b342b"},
    )
    return fig


def quadrant_matplotlib_figure(objects: pd.DataFrame, communities: pd.DataFrame):
    """Matplotlib version aligned with the TA notebook OBP-5 visualization."""
    if not MATPLOTLIB_AVAILABLE:
        raise RuntimeError("Matplotlib belum terinstall di environment Streamlit.")

    d = objects.copy()
    x = d["wd"].astype(float).values
    yb = d["balance"].astype(float).values
    bc = d["bc"].astype(float).values
    x_med, y_med = float(pd.Series(x).median()), float(pd.Series(yb).median())
    bc_max = float(pd.Series(bc).max()) or 1.0
    bridge_names = set(d.nlargest(8, "bc")["nama"])

    community_labels = {
        int(row.id): str(row.nama)
        for row in communities.sort_values("id").itertuples()
    }

    fig, ax = plt.subplots(figsize=(13, 9))
    fig.patch.set_facecolor("#fbfaf6")
    ax.set_facecolor("#fbfaf6")

    ax.axvspan(x_med, x.max() * 1.15, ymin=0.5, color="#2A9D8F", alpha=0.05)
    ax.axvspan(x_med, x.max() * 1.15, ymax=0.5, color="#E63946", alpha=0.05)

    for _, r in d.iterrows():
        community = int(r["komunitas"])
        is_bridge = r["nama"] in bridge_names
        color = NOTEBOOK_COMMUNITY_COLORS.get(community, "#999999")
        size = 120 + (float(r["bc"]) / bc_max) * 1700
        ax.scatter(
            float(r["wd"]),
            float(r["balance"]),
            s=size,
            color=color,
            alpha=0.78,
            edgecolors="#1A1A1A",
            linewidths=1.0,
            marker="*" if is_bridge else "o",
            zorder=5 if is_bridge else 4,
        )
        name = (
            str(r["nama"])
            .replace("Monumen dan Museum ", "")
            .replace("Kawasan ", "")
        )
        ax.annotate(
            name[:20],
            (float(r["wd"]), float(r["balance"])),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=7,
            color="#222",
        )

    ax.axvline(x_med, color="#666", linestyle="--", linewidth=1.1)
    ax.axhline(y_med, color="#666", linestyle="--", linewidth=1.1)

    xr, yr = ax.get_xlim(), ax.get_ylim()
    quad = [
        (0.97, 0.96, "ANCHOR\nsentral & diapresiasi", "#1d6f63", "right", "top"),
        (0.97, 0.04, "ISSUE AMPLIFIER\nsentral tapi bermasalah", "#b5232f", "right", "bottom"),
        (0.03, 0.96, "NICHE POSITIVE\nniche tapi disukai", "#4361EE", "left", "top"),
        (0.03, 0.04, "PERIPHERAL\nkurang sentral & lemah", "#6c757d", "left", "bottom"),
    ]
    for fx, fy, text, color, ha, va in quad:
        ax.text(
            xr[0] + (xr[1] - xr[0]) * fx,
            yr[0] + (yr[1] - yr[0]) * fy,
            text,
            fontsize=9.5,
            fontweight="bold",
            color=color,
            ha=ha,
            va=va,
            alpha=0.85,
        )

    ax.set_xlabel("Weighted Degree (sentralitas ko-kunjungan) →", fontsize=11)
    ax.set_ylabel("Sentiment Balance  (% positif − % negatif) →", fontsize=11)
    ax.set_title(
        "Posisi Objek dalam Ekosistem: Sentralitas × Sentimen\n"
        "ukuran bubble = betweenness · ★ = bridge node · garis = median",
        fontsize=12.5,
        fontweight="bold",
        pad=12,
    )
    ax.grid(True, alpha=0.2)

    legend_comm = [
        mpatches.Patch(
            color=NOTEBOOK_COMMUNITY_COLORS[k],
            label=f"Kom.{k} – {community_labels.get(k, f'Komunitas {k}')}",
        )
        for k in sorted(NOTEBOOK_COMMUNITY_COLORS)
        if k in d["komunitas"].dropna().astype(int).unique()
    ]
    legend_comm.append(
        ax.scatter(
            [],
            [],
            marker="*",
            s=180,
            color="gray",
            edgecolors="#1A1A1A",
            label="Bridge node (BC tinggi)",
        )
    )
    ax.legend(handles=legend_comm, fontsize=8.5, loc="lower left", framealpha=0.92)

    fig.tight_layout()
    return fig


def matplotlib_svg_html(fig) -> str:
    """Render a Matplotlib figure as responsive SVG for crisp browser display."""
    buffer = io.StringIO()
    fig.savefig(
        buffer,
        format="svg",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    svg = buffer.getvalue()
    plt.close(fig)
    return f"""
    <style>
      html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
      }}
      .svg-plot {{
        width: 100%;
        background: #fbfaf6;
        border: 1px solid #d8d0c2;
        border-radius: 12px;
        padding: 0.55rem;
        box-sizing: border-box;
        overflow: hidden;
      }}
      .svg-plot svg {{
        width: 100% !important;
        height: auto !important;
        display: block;
      }}
    </style>
    <div class="svg-plot">{svg}</div>
    """


def topic_figure(topics: pd.DataFrame) -> go.Figure:
    ordered = topics.sort_values("n", ascending=True)
    fig = px.bar(
        ordered,
        x="n",
        y="label",
        orientation="h",
        color="rumpun",
        text="pct",
        custom_data=["id", "keywords", "rumpun"],
        labels={"n": "Jumlah ulasan", "label": "", "rumpun": "Rumpun"},
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>ID: %{customdata[0]}<br>"
        "Ulasan: %{x}<br>Proporsi: %{text:.1f}%<br>"
        "Kata kunci: %{customdata[1]}<extra></extra>",
    )
    fig.update_layout(
        height=720,
        margin={"l": 10, "r": 50, "t": 25, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.35)",
        legend={"orientation": "h", "y": -0.12},
    )
    return fig


def sentiment_composition_figure(objects: pd.DataFrame) -> go.Figure:
    ordered = objects.sort_values(["komunitas", "neg"], ascending=[True, False])
    fig = go.Figure()
    for column, label, color in [
        ("neg", "Negatif", "#d9584d"),
        ("netral", "Netral", "#c8c1b5"),
        ("pos", "Positif", "#2c947e"),
    ]:
        fig.add_bar(
            y=ordered["objek_short"],
            x=ordered[column],
            orientation="h",
            name=label,
            marker_color=color,
            customdata=ordered[["nama", "komunitas_nama"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
            f"{label}: %{{x:.1f}}%<extra></extra>",
        )
    fig.update_layout(
        barmode="stack",
        height=820,
        xaxis={"range": [0, 100], "title": "Proporsi sentimen (%)"},
        yaxis={"autorange": "reversed"},
        margin={"l": 10, "r": 10, "t": 25, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.35)",
        legend={"orientation": "h", "y": -0.05},
    )
    return fig


payload = load_app_data()
data = payload["bab4"]
topics = payload["topics"]
communities = payload["communities"]
objects = enrich_object_labels(payload["objects"], communities)
edges = payload["edges"]
obp = payload["obp"]
source_status = payload["source_status"]
inject_css()

meta = dict(data["meta"])
meta["ulasanTeksValid"] = int(topics["n"].sum())
meta["jumlahObjek"] = int(objects["nama"].nunique())
meta["jumlahTopikFinal"] = int(topics["id"].nunique())
meta["jumlahKomunitas"] = int(communities["id"].nunique())
st.markdown(
    f"""
    <section class="hero">
      <div class="hero-kicker">Dashboard Narasi Integratif · Tugas Akhir 2026</div>
      <h1>Ekosistem Pengalaman Publik Cagar Budaya Surabaya</h1>
      <p>
        Dashboard naratif yang membaca <b>{meta["jumlahObjek"]} objek cagar budaya</b>
        bukan sebagai situs yang berdiri sendiri, melainkan sebagai simpul yang
        saling terhubung — lewat apa yang dibicarakan pengunjung, bagaimana mereka
        menilainya, dan bagaimana objek terjalin dalam jaringan ko-reviewer.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Filter eksplorasi")
    community_options = communities["nama"].tolist()
    selected_communities = st.multiselect(
        "Komunitas Louvain",
        community_options,
        default=community_options,
    )
    role_options = sorted(objects["peran"].unique())
    selected_roles = st.multiselect("Peran objek", role_options, default=role_options)
    st.divider()
    st.markdown("### Status integrasi")
    source_labels = {
        "topik": "Topik per ulasan",
        "sentimen_objek": "Sentimen per objek",
        "sna_nodes": "Node & sentralitas SNA",
        "sna_edges": "Edge ko-reviewer",
        "obp": "Profil OBP",
    }
    for key, label in source_labels.items():
        icon = "✅" if source_status[key] else "⚠️"
        st.caption(f"{icon} {label}")
    if source_status.get("obp_profile"):
        st.caption("✅ Sumber OBP: `obp_object_profile_final.xlsx` dari notebook.")
    else:
        st.caption(
            "⚠️ Sumber OBP masih fallback ke `integrasi_sna_topik_final.xlsx`; "
            "copy export notebook terbaru agar balance sentimen sama persis."
        )
    st.caption(
        "`bab4.json` kini hanya menjadi sumber narasi, warna komunitas, "
        "koordinat, dan prioritas interpretif."
    )

filtered = objects[
    objects["komunitas_nama"].isin(selected_communities)
    & objects["peran"].isin(selected_roles)
].copy()
filtered_names = set(filtered["nama"])
filtered_edges = edges[
    edges["Source"].isin(filtered_names) & edges["Target"].isin(filtered_names)
].copy()

if filtered.empty:
    st.warning("Tidak ada objek yang cocok dengan kombinasi filter saat ini.")
    st.stop()

tab_overview, tab_objects, tab_topics, tab_priorities = st.tabs(
    ["Ringkasan", "Jaringan Ko-Reviewer", "Topik & Sentimen", "Prioritas Objek"]
)

with tab_overview:
    dimension_cols = st.columns(3)
    dimensions = [
        ("Diskursif", "Topic Modeling", "Apa yang dibicarakan pengunjung — 16 topik dari BERTopic.", "#2C66C9"),
        ("Afektif", "Sentiment", "Bagaimana dinilai — positif, netral, negatif (XLM-T + XGBoost).", "#1E865A"),
        ("Struktural", "SNA", "Bagaimana terhubung — jaringan ko-reviewer & komunitas Louvain.", "#7E4FC0"),
    ]
    for column, (title, method, description, color) in zip(dimension_cols, dimensions):
        column.markdown(
            f"""
            <div class="dimension-card" style="--accent:{color}">
              <span class="method">{method}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:1.15rem"></div>', unsafe_allow_html=True)
    metric_cards(meta)
    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)

    findings = [
        "Objek strategis seperti De Javasche Bank & Masjid Sunan Ampel menghubungkan banyak komunitas, tetapi pengalamannya belum maksimal.",
        "Keluhan parkir, jam operasional, & fasilitas muncul lintas komunitas — isu praktis, bukan penolakan nilai sejarah.",
        "Cagar budaya Surabaya membentuk satu ekosistem pengalaman, bukan kumpulan situs yang terpisah.",
    ]

    insight_left, insight_right = st.columns([1.05, 1])
    with insight_left:
        st.markdown(
            """
            <div class="dark-card">
              <div class="eyebrow">Temuan Inti</div>
              <h2>Sentralitas jaringan tidak selalu sejalan dengan kepuasan pengunjung.</h2>
              <p>
                Objek yang paling strategis dalam jaringan — seperti De Javasche Bank
                atau Masjid Sunan Ampel — belum tentu objek yang paling disukai.
                Sebaliknya, objek dengan sentimen sangat positif sering justru
                periferal. Pengelolaan cagar budaya karenanya perlu membaca posisi
                struktural, bukan sekadar tingkat kepuasan.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with insight_right:
        finding_html = '<div class="finding-list-title">Apa yang ditemukan integrasi</div>'
        for number, finding in enumerate(findings, 1):
            finding_html += (
                f'<div class="finding-item"><span class="finding-number">{number}</span>'
                f'<span>{finding}</span></div>'
            )
        st.markdown(finding_html, unsafe_allow_html=True)

with tab_objects:
    control_left, control_right = st.columns([1.15, 1])
    with control_left:
        color_mode = st.radio(
            "Dimensi warna",
            ["Struktural · SNA", "Diskursif · Topik", "Spasial · Kawasan"],
            horizontal=True,
            label_visibility="collapsed",
            key="network_color_mode",
        )
    with control_right:
        filter_left, filter_right = st.columns([1.05, 1])
        with filter_left:
            st.markdown(
                '<div class="network-kicker">Filter Komunitas</div>',
                unsafe_allow_html=True,
            )
            selected_communities = community_filter_control(communities)
        with filter_right:
            role_filter = st.selectbox(
                "Filter Peran",
                ["Semua peran"] + sorted(objects["peran"].unique()),
                key="network_role_filter",
            )

    network_objects = objects[objects["komunitas"].isin(selected_communities)].copy()
    if role_filter != "Semua peran":
        network_objects = network_objects[network_objects["peran"] == role_filter].copy()

    if network_objects.empty:
        st.info("Tidak ada objek yang sesuai dengan kombinasi filter komunitas dan peran ini.")
    else:
        network_names = set(network_objects["nama"])
        network_edges = edges[
            edges["Source"].isin(network_names) & edges["Target"].isin(network_names)
        ].copy()

        community_colors = communities.set_index("id")["color"].to_dict()
        components.html(
            build_network_panel(
                network_objects,
                network_edges,
                color_mode,
                community_colors,
                communities,
            ),
            height=735,
            scrolling=False,
        )

with tab_topics:
    classified_reviews = f'{int(topics["n"].sum()):,}'.replace(",", ".")
    st.markdown(
        f"""
        <div class="topic-kicker">16 Topik Final · BERTopic</div>
        <p class="topic-copy">
          Distribusi <b>{classified_reviews}</b> ulasan terklasifikasi.
          Warna menandai rumpun tema. Topik fasilitas & operasional menjadi
          sumber isu praktis utama, sementara topik religi, museum, dan kuliner
          menunjukkan identitas pengalaman yang lebih kuat.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(topic_bars_html(topics), unsafe_allow_html=True)

    if MATPLOTLIB_AVAILABLE:
        components.html(
            matplotlib_svg_html(quadrant_matplotlib_figure(filtered, communities)),
            height=835,
            scrolling=False,
        )
    else:
        st.warning(
            "Matplotlib belum terinstall. Jalankan `pip install -r dashboard/requirements.txt` "
            "agar visualisasi ini tampil sama seperti notebook."
        )
        community_color_map = communities.set_index("nama")["color"].to_dict()
        st.plotly_chart(
            quadrant_figure(filtered, community_color_map),
            width="stretch",
            config={"displayModeBar": False},
        )
    st.markdown(
        f"""
        <div class="plot-note">
          median WD {filtered["wd"].median():.0f} · median balance {filtered["balance"].median():.1f}
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_priorities:
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.markdown('<div class="priority-kicker">Lima Kelompok Prioritas</div>', unsafe_allow_html=True)
        accent_colors = ["#1F8A5B", "#8754C9", "#C2410C", "#2A6FDB", "#9A8B6E"]
        for priority, accent in zip(data["prioritas"], accent_colors):
            chips = "".join(
                f'<span class="chip">{html.escape(str(name))}</span>'
                for name in priority["objek"]
            )
            st.markdown(
                f"""
                <div class="priority-card" style="--accent:{accent}">
                  <h4>{html.escape(priority["grup"])}</h4>
                  <div>{chips}</div>
                  <p><b>Implikasi.</b> {html.escape(priority["implikasi"])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right_col:
        st.markdown(
            """
            <div class="strategy-card">
              <div class="priority-kicker">Tiga Strategi Pengelolaan</div>
              <div class="strategy-item">
                <div class="strategy-number">1</div>
                <div>
                  <div class="strategy-title">Pertahankan objek positif</div>
                  <div class="strategy-copy">Jadikan anchor promosi & ikon tematik dalam rute heritage.</div>
                </div>
              </div>
              <div class="strategy-item">
                <div class="strategy-number">2</div>
                <div>
                  <div class="strategy-title">Perkuat objek strategis</div>
                  <div class="strategy-copy">Anchor & bridge — perbaikannya berdampak lintas komunitas.</div>
                </div>
              </div>
              <div class="strategy-item">
                <div class="strategy-number">3</div>
                <div>
                  <div class="strategy-title">Perbaiki isu operasional</div>
                  <div class="strategy-copy">Parkir, akses, fasilitas, jam kunjungan agar pengalaman naik.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        role_items = "".join(
            f"""
            <div class="role-def-item">
              <h4>{html.escape(str(role))}</h4>
              <p>{html.escape(str(definition))}</p>
            </div>
            """
            for role, definition in data["peranDef"].items()
        )
        st.markdown(
            f"""
            <div class="role-def-card">
              <div class="priority-kicker">Tujuh Peran Objek</div>
              {role_items}
            </div>
            """,
            unsafe_allow_html=True,
        )

