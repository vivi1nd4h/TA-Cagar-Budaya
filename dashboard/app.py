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
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700;800&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap');
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
            --overview-zoom: .92;
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
            max-width: 1500px;
            padding: .45rem 1.25rem 1rem;
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
        h2 {font-size: 1.35rem !important; margin: 1rem 0 .55rem !important;}
        h3 {font-size: .98rem !important;}
        .hero {
            position: relative;
            padding: .15rem 0 .65rem;
            margin: 0 0 .45rem;
            border: 0;
            background: transparent;
            box-shadow: none;
            text-align: center;
            zoom: var(--overview-zoom);
        }
        .hero-kicker, .eyebrow {
            font-family: "IBM Plex Mono", monospace;
            font-size: .76rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
        }
        .hero-kicker {display: none;}
        .hero::after {
            content: "";
            position: absolute;
            left: 50%;
            bottom: 0;
            width: 128px;
            height: 2px;
            border-radius: 999px;
            background: #a05d17;
            transform: translateX(-50%);
        }
        .hero h1 {
            position: relative;
            z-index: 1;
            font-size: clamp(2.15rem, 2.7vw, 3rem);
            line-height: 1.04;
            text-transform: none;
            letter-spacing: -.018em;
            margin: 0 auto;
            max-width: 1120px;
        }
        .hero h1 .title-line {
            display: inline;
        }
        .hero h1 .title-place {
            display: inline;
            margin-top: 0;
        }
        .hero-title-frame {
            position: relative;
            min-height: 68px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 190px;
        }
        .hero-motif {
            position: absolute;
            top: 50%;
            width: 104px;
            height: 24px;
            transform: translateY(-50%);
            opacity: 1;
            pointer-events: none;
            color: #b3482d;
        }
        .hero-motif svg {
            width: 100%;
            height: 100%;
            display: block;
            overflow: visible;
        }
        .hero-motif-left {left: 7rem;}
        .hero-motif-right {right: 7rem; transform: translateY(-50%) scaleX(-1);}
        .hero p {
            font-size: .86rem;
            line-height: 1.32;
            color: #4f493f;
            max-width: 1220px;
            margin: 0;
        }
        .metric-card {
            padding: .8rem .9rem;
            height: 88px;
            border: 1px solid color-mix(in srgb, var(--accent, #a05d17) 22%, var(--line));
            border-top: 3px solid var(--accent, #a05d17);
            border-radius: 6px;
            background: var(--soft, rgba(251, 250, 246, .58));
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .metric-card .value {
            font-family: "IBM Plex Sans", sans-serif;
            font-size: 1.78rem;
            line-height: 1;
            font-weight: 800;
            color: var(--accent, #211d17);
            letter-spacing: -.015em;
        }
        .metric-card .label {
            font-size: .75rem;
            color: #433c33;
            font-weight: 500;
            margin-top: .36rem;
        }
        .overview-layout {
            display: grid;
            gap: .72rem;
            zoom: var(--overview-zoom);
        }
        .overview-dimensions,
        .overview-metrics,
        .overview-main,
        .overview-left-stack {
            display: grid;
            gap: .72rem;
        }
        .overview-dimensions {grid-template-columns: repeat(3, minmax(0, 1fr));}
        .overview-metrics {grid-template-columns: repeat(5, minmax(0, 1fr));}
        .overview-main {grid-template-columns: minmax(0, 1.55fr) minmax(360px, 1fr); align-items: stretch;}
        .overview-left-stack {display: block;}
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
            background: var(--soft);
            border: 1px solid color-mix(in srgb, var(--accent) 16%, var(--line));
            border-radius: 8px;
            padding: .95rem 1.05rem;
            height: 94px;
            margin-bottom: 0;
            display: flex;
            align-items: center;
            gap: .9rem;
            overflow: hidden;
        }
        .dimension-icon {
            width: 50px;
            height: 50px;
            border-radius: 11px;
            flex: 0 0 50px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: #fffaf1;
        }
        .dimension-icon svg {
            width: 27px;
            height: 27px;
            stroke-width: 2.1;
        }
        .dimension-copy {min-width: 0;}
        .dimension-card .method {
            display: inline;
            margin-left: .35rem;
            font-family: "IBM Plex Mono", monospace;
            font-size: .58rem;
            letter-spacing: .15em;
            text-transform: uppercase;
            color: color-mix(in srgb, var(--accent) 78%, #211d17);
            font-weight: 600;
        }
        .dimension-card h3 {
            font-family: "IBM Plex Sans", sans-serif !important;
            font-size: 1.2rem !important;
            line-height: 1.1 !important;
            margin: 0 0 .38rem !important;
            color: color-mix(in srgb, var(--accent) 38%, #211d17);
            font-weight: 800 !important;
        }
        .dimension-card p {
            color: #3f382f;
            font-size: .77rem;
            line-height: 1.25;
            margin: 0;
            min-height: 0;
            font-weight: 500;
        }
        .discourse-card {
            background: rgba(251, 250, 246, .78);
            border: 1px solid rgba(222, 213, 198, .78);
            border-radius: 7px;
            padding: 1.18rem 1.35rem;
            min-height: 136px;
        }
        .dark-card .discourse-card {
            background: transparent;
            border: 0;
            border-radius: 0;
            padding: 0 0 1.25rem;
            min-height: 0;
            border-bottom: 1px solid rgba(240, 230, 213, .18);
            margin-bottom: 1.25rem;
        }
        .discourse-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .8rem;
        }
        .discourse-card h3 {
            font-family: "IBM Plex Sans", sans-serif !important;
            font-size: 1.1rem !important;
            margin: 0 !important;
            line-height: 1.1 !important;
            font-weight: 800 !important;
            color: #11100d;
        }
        .dark-card .discourse-card h3 {
            color: #fff8ed;
        }
        .discourse-total {
            font-family: "IBM Plex Mono", monospace;
            color: #5d5346;
            font-size: .68rem;
            white-space: nowrap;
            font-weight: 600;
        }
        .dark-card .discourse-total {
            color: #d8c8ad;
        }
        .discourse-bar {
            height: 34px;
            border-radius: 7px;
            overflow: hidden;
            display: flex;
            background: #e8dfcf;
        }
        .dark-card .discourse-bar {
            background: rgba(255, 250, 241, .14);
            box-shadow: inset 0 0 0 1px rgba(255, 250, 241, .08);
        }
        .discourse-segment {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #fffaf1;
            font-size: .68rem;
            font-weight: 800;
            min-width: 34px;
        }
        .discourse-legend {
            display: flex;
            flex-wrap: wrap;
            gap: .45rem .85rem;
            margin-top: .75rem;
            color: #3f382f;
            font-size: .72rem;
            font-weight: 500;
        }
        .dark-card .discourse-legend {
            color: #f0e6d5;
        }
        .discourse-legend-item {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            white-space: nowrap;
        }
        .discourse-swatch {
            width: 11px;
            height: 11px;
            border-radius: 3px;
            display: inline-block;
        }
        .dark-card {
            background: #26221b;
            color: #f8f2e7;
            border-radius: 8px;
            padding: 1.55rem 1.7rem 1.65rem;
            min-height: 329px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .dark-card .eyebrow {
            color: #f0a33b;
            font-weight: 600;
        }
        .dark-card h2 {
            font-family: "IBM Plex Sans", sans-serif !important;
            color: #fff8ed;
            font-size: 1.42rem !important;
            line-height: 1.18;
            margin: .85rem 0 .95rem !important;
            max-width: 760px;
            font-weight: 800 !important;
            letter-spacing: -.01em;
        }
        .dark-card p {
            color: #f0e6d5;
            font-size: .9rem;
            line-height: 1.5;
            margin: 0;
            max-width: 760px;
            font-weight: 600;
        }
        .findings-card {
            background: rgba(251, 250, 246, .66);
            border: 1px solid rgba(222, 213, 198, .78);
            border-radius: 8px;
            padding: 1.45rem 1.65rem 1.55rem;
            min-height: 329px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-evenly;
        }
        .finding-list-title {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            color: #9a5412;
            text-transform: uppercase;
            margin: 0;
            font-weight: 600;
        }
        .finding-item {
            display: grid;
            grid-template-columns: 36px minmax(0, 1fr);
            gap: .9rem;
            align-items: start;
            margin: 0;
            color: #191611;
            font-size: 1rem;
            line-height: 1.46;
            font-weight: 600;
        }
        .finding-number {
            width: 32px;
            height: 32px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: #fffaf1;
            font-family: "IBM Plex Mono", monospace;
            font-weight: 600;
            font-size: .84rem;
            margin-top: .05rem;
        }
        .topic-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .82rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            margin: 0 0 .5rem;
            font-weight: 600;
        }
        .topic-copy {
            color: #4f463b;
            max-width: 940px;
            font-size: 1rem;
            line-height: 1.42;
            margin: 0 0 1rem;
            font-weight: 500;
        }
        .topic-bars-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .75rem 1.3rem;
            margin-bottom: .85rem;
        }
        .topic-row {margin-bottom: .62rem;}
        .topic-row-head {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: .65rem;
            align-items: end;
            margin-bottom: .25rem;
        }
        .topic-row-title {
            color: #090806;
            font-size: .88rem;
            font-weight: 800;
            line-height: 1.18;
        }
        .topic-row-meta {
            color: #6a5f51;
            font-family: "IBM Plex Mono", monospace;
            font-size: .78rem;
            white-space: nowrap;
            font-weight: 600;
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
            gap: .5rem .85rem;
            align-items: center;
            margin: .75rem 0 .5rem;
            color: #4f463b;
            font-size: .86rem;
            font-weight: 500;
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
        .topic-panel {
            background: rgba(251, 250, 246, .78);
            border: 1px solid rgba(222, 213, 198, .9);
            border-radius: 8px;
            padding: 1rem 1.05rem .95rem;
            min-height: 590px;
        }
        .topic-panel-head {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .5rem;
        }
        .topic-panel h3 {
            font-family: "IBM Plex Sans", sans-serif !important;
            font-size: 1.12rem !important;
            line-height: 1.1 !important;
            margin: 0 !important;
            font-weight: 800 !important;
            letter-spacing: 0;
        }
        .topic-panel .method {
            font-family: "IBM Plex Mono", monospace;
            font-size: .64rem;
            letter-spacing: .2em;
            color: var(--brown);
            text-transform: uppercase;
            font-weight: 600;
        }
        .topic-panel .topic-copy {
            font-size: .78rem;
            line-height: 1.32;
            margin: 0 0 .72rem;
        }
        .topic-panel .topic-bars-grid {
            display: block;
            margin-bottom: .7rem;
        }
        .topic-panel .topic-row {
            margin-bottom: .47rem;
        }
        .topic-panel .topic-row-head {
            margin-bottom: .17rem;
        }
        .topic-panel .topic-row-title {
            font-size: .72rem;
            line-height: 1.14;
        }
        .topic-panel .topic-row-meta {
            font-size: .66rem;
        }
        .topic-panel .topic-track {
            height: 6px;
        }
        .topic-panel .topic-legend {
            border-top: 1px solid #e2d8c7;
            padding-top: .7rem;
            margin: .75rem 0 0;
            font-size: .72rem;
            gap: .45rem .7rem;
        }
        .topic-panel .topic-legend-swatch {
            width: 11px;
            height: 11px;
        }
        .quadrant-head {
            margin: .15rem 0 .7rem;
        }
        .quadrant-head h3 {
            font-family: "IBM Plex Sans", sans-serif !important;
            font-size: 1.25rem !important;
            line-height: 1.15 !important;
            margin: 0 0 .38rem !important;
            font-weight: 800 !important;
            letter-spacing: 0;
        }
        .quadrant-head p {
            color: #4f463b;
            font-size: .88rem;
            line-height: 1.4;
            margin: 0;
            font-weight: 500;
        }
        .quadrant-mini-legend {
            display: flex;
            align-items: center;
            gap: .85rem;
            margin-top: .62rem;
            color: #6d6254;
            font-family: "IBM Plex Mono", monospace;
            font-size: .78rem;
            font-weight: 600;
        }
        .legend-dot {
            width: 14px;
            height: 14px;
            border-radius: 999px;
            display: inline-block;
            background: #b8ad9b;
            vertical-align: -2px;
            margin-right: .35rem;
        }
        .community-inline-legend {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .62rem 1.15rem;
            align-items: start;
            margin: .25rem 0 .35rem;
            color: #4b443a;
            font-size: .8rem;
            font-weight: 600;
            line-height: 1.25;
        }
        .community-inline-item {
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            min-width: 0;
        }
        .community-inline-item .topic-legend-swatch {
            flex: 0 0 13px;
            width: 13px;
            height: 13px;
            border-radius: 999px;
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
        div[data-testid="stVerticalBlock"] {gap: .55rem;}
        div[data-testid="stHorizontalBlock"] {gap: .55rem;}
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 1px solid #d8cfc0;
            margin-bottom: .8rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 34px;
            padding: 0 .95rem;
            color: #8a8070;
            font-size: .76rem;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {color: #11100e !important;}
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #1e1b16 !important;
            height: 2px !important;
        }
        .priority-card {
            padding: .78rem .9rem .72rem;
            border: 1px solid var(--line);
            border-left: 5px solid var(--accent);
            border-radius: 7px;
            background: #fbfaf6;
            margin-bottom: .46rem;
            min-height: 102px;
        }
        .priority-card h4 {
            margin: 0 0 .45rem;
            font-family: "IBM Plex Sans", sans-serif;
            font-size: .98rem;
            line-height: 1.18;
            color: #11100e;
            font-weight: 800;
        }
        .priority-card p {
            margin: .45rem 0 0;
            color: #4f463b;
            font-size: .78rem;
            line-height: 1.34;
            font-weight: 500;
        }
        .chip {
            display: inline-block;
            padding: .18rem .5rem;
            margin: .08rem .12rem .08rem 0;
            border-radius: 999px;
            background: #eee7da;
            color: #40382f;
            font-size: .66rem;
            line-height: 1.25;
            font-weight: 500;
        }
        .priority-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .68rem;
            letter-spacing: .24em;
            text-transform: uppercase;
            color: var(--brown);
            margin: .05rem 0 .5rem;
            font-weight: 600;
        }
        .strategy-card {
            background: #211d17;
            border-radius: 7px;
            padding: .95rem 1.05rem .9rem;
            color: #f8f2e8;
            margin-bottom: .48rem;
            min-height: 172px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .strategy-card .priority-kicker {
            color: #d58a2e;
            margin-top: 0;
        }
        .strategy-item {
            display: grid;
            grid-template-columns: 1.25rem 1fr;
            gap: .55rem;
            margin: .55rem 0;
        }
        .strategy-number {
            font-family: "IBM Plex Sans", sans-serif;
            color: #d58a2e;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1;
        }
        .strategy-title {
            color: #fbfaf6;
            font-weight: 800;
            font-size: .82rem;
            margin-bottom: .12rem;
        }
        .strategy-copy {
            color: #e6dac8;
            font-size: .7rem;
            line-height: 1.3;
            font-weight: 500;
        }
        .role-def-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 7px;
            padding: .88rem 1rem;
        }
        .role-def-item {
            margin: .46rem 0 .54rem;
        }
        .role-def-item h4 {
            margin: 0 0 .12rem;
            color: #211d17;
            font-family: "IBM Plex Sans", sans-serif;
            font-size: .76rem;
            font-weight: 800;
        }
        .role-def-item p {
            margin: 0;
            color: #5f5548;
            font-size: .66rem;
            line-height: 1.28;
            font-weight: 500;
        }
        div[data-testid="stPlotlyChart"] {
            border: 1px solid var(--line); border-radius: 6px;
            background: #fbfaf6; overflow: hidden;
        }
        .network-kicker {
            font-family: "IBM Plex Mono", monospace;
            font-size: .94rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            font-weight: 600;
            margin: 0 0 .6rem;
        }
        .network-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 385px;
            gap: .9rem;
            align-items: start;
        }
        .network-controls {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .7rem;
            margin: 0 0 .55rem;
        }
        .dimension-pills {
            display: inline-flex;
            padding: .25rem;
            background: #e7dfd0;
            border-radius: 6px;
        }
        .dimension-pill {
            display: inline-block;
            padding: .7rem 1.18rem;
            border-radius: 5px;
            font-size: 1.12rem;
            color: #665e52;
            font-weight: 800;
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
            min-width: 40px;
            height: 34px;
            padding: 0 .65rem;
            border-radius: 6px;
            color: #fff;
            font-weight: 800;
            font-size: .82rem;
        }
        div[data-testid="stPills"] {
            margin-top: -.15rem;
        }
        div[data-testid="stPills"] button {
            min-width: 46px !important;
            height: 38px !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
            font-size: 1.05rem !important;
        }
        .role-select-label {
            font-family: "IBM Plex Mono", monospace;
            font-size: .72rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            margin-bottom: .55rem;
        }
        .network-panel-lift {
            height: 0;
            margin-bottom: -.45rem;
        }
        .network-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: .5rem .5rem .35rem;
        }
        .network-card svg {
            display: block;
            width: 100%;
            height: auto;
            min-height: 440px;
        }
        .network-note {
            border-top: 1px solid #e4daca;
            margin-top: .25rem;
            padding: .48rem .3rem .15rem;
            color: #9a8d7b;
            font-family: "IBM Plex Mono", monospace;
            font-size: .86rem;
            font-weight: 500;
        }
        .network-side-card {
            background: #fbfaf6;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: .9rem 1rem;
        }
        .legend-title {
            font-family: "IBM Plex Mono", monospace;
            font-size: .9rem;
            letter-spacing: .22em;
            color: var(--brown);
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: .65rem;
        }
        .legend-item {
            display: grid;
            grid-template-columns: 18px 1fr;
            gap: .5rem;
            align-items: start;
            margin-bottom: .68rem;
            color: #211d17;
            font-size: 1.02rem;
            line-height: 1.28;
            font-weight: 600;
        }
        .legend-swatch {
            width: 15px;
            height: 15px;
            border-radius: 4px;
            margin-top: .17rem;
        }
        .legend-divider {
            height: 1px;
            background: #e2d8c7;
            margin: .8rem 0 .65rem;
        }
        .legend-note {
            color: #4f463b;
            font-size: 1rem;
            line-height: 1.34;
            margin-bottom: .6rem;
            font-weight: 500;
        }
        .legend-hint {
            color: #756a5b;
            font-size: .94rem;
            font-style: italic;
            line-height: 1.3;
            font-weight: 500;
        }
        div[data-testid="stSelectbox"] label {
            font-family: "IBM Plex Mono", monospace;
            font-size: .94rem;
            letter-spacing: .22em;
            text-transform: uppercase;
            color: var(--brown);
            font-weight: 600;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] {
            min-height: 48px;
            font-size: 1.12rem;
            font-weight: 700;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] * {
            font-size: 1.12rem;
            font-weight: 700;
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
            min-height: 40px;
            padding: 0 .95rem;
            margin: 0;
            border-radius: 5px;
            color: #665e52;
            font-weight: 800;
            font-size: 1.08rem;
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


def topic_panel_html(topics: pd.DataFrame, total_label: str) -> str:
    ordered = topics.sort_values("n", ascending=False).reset_index(drop=True)
    max_n = max(float(ordered["n"].max()), 1)

    rows = []
    for _, row in ordered.iterrows():
        color = TOPIC_RUMPUN_COLORS.get(str(row["rumpun"]), "#7E4FC0")
        width = max(float(row["n"]) / max_n * 100, 1)
        pct = f'{float(row["pct"]):.1f}'.replace(".", ",")
        rows.append(
            '<div class="topic-row">'
            '<div class="topic-row-head">'
            f'<div class="topic-row-title">{html.escape(str(row["label_short"]))}</div>'
            f'<div class="topic-row-meta">{pct}%</div>'
            '</div>'
            '<div class="topic-track">'
            f'<div class="topic-fill" style="width:{width:.2f}%; background:{color}"></div>'
            '</div>'
            '</div>'
        )

    legend_html = "".join(
        '<span class="topic-legend-item">'
        f'<span class="topic-legend-swatch" style="background:{color}"></span>'
        f'{html.escape(label)}'
        '</span>'
        for label, color in TOPIC_RUMPUN_COLORS.items()
    )
    return (
        '<div class="topic-panel">'
        '<div class="topic-panel-head">'
        '<h3>16 Topik Final</h3>'
        '<span class="method">BERTopic</span>'
        '</div>'
        f'<p class="topic-copy">Distribusi <b>{html.escape(total_label)}</b> ulasan; warna = rumpun tema.</p>'
        '<div class="topic-bars-grid">'
        f'{"".join(rows)}'
        '</div>'
        f'<div class="topic-legend">{legend_html}</div>'
        '</div>'
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
.network-panel { display: grid; grid-template-columns: minmax(0, 2.45fr) .92fr; gap: .8rem; align-items: start; }
.network-card, .network-side-card, .profile-card {
  background: #fbfaf6; border: 1px solid #ded5c6; border-radius: 6px; overflow: hidden;
}
.network-card { padding: .45rem .45rem 0; }
.network-card svg { width: 100%; height: 500px; display: block; }
.network-note {
  border-top: 1px solid #eadfcc; padding: .45rem .35rem .5rem;
  color: #8e7f6b; font-family: "IBM Plex Mono", monospace; font-size: .84rem; font-weight: 500;
}
.network-node { cursor: pointer; transition: opacity .15s ease, stroke-width .15s ease, filter .15s ease; }
.network-node:hover { opacity: 1; filter: drop-shadow(0 3px 5px rgba(38,34,27,.22)); }
.network-node.active { stroke-width: 5.5px; }
.network-side-card { padding: .85rem; min-height: 190px; }
.legend-title {
  font-family: "IBM Plex Mono", monospace; font-size: .9rem; letter-spacing: .2em;
  text-transform: uppercase; color: #a05d17; margin-bottom: .7rem; font-weight: 600;
}
.legend-item { display: flex; gap: .58rem; align-items: flex-start; margin: .65rem 0; color: #211d17; font-size: 1.02rem; font-weight: 600; line-height: 1.3; }
.legend-swatch { width: 15px; height: 15px; flex: 0 0 15px; border-radius: 4px; margin-top: .18rem; }
.legend-divider { border-top: 1px solid #eadfcc; margin: .7rem 0 .55rem; }
.legend-note { color: #4f463b; font-size: .98rem; font-weight: 500; line-height: 1.36; }
.legend-hint { color: #746857; font-size: .9rem; font-style: italic; font-weight: 500; line-height: 1.3; margin-top: .55rem; }
.profile-card { padding: 0; }
.profile-head {
  position: relative; background: var(--profile-color, #c9772f); color: #fffaf0;
  padding: .95rem 1.05rem 1rem;
}
.profile-close {
  position: absolute; right: .7rem; top: .7rem; width: 26px; height: 26px; border: 0;
  border-radius: 999px; background: rgba(255,255,255,.22); color: #fffaf0;
  font-size: 1.1rem; cursor: pointer; line-height: 1;
}
.profile-head h3 {
  font-family: "IBM Plex Sans", sans-serif; font-size: 1.16rem; line-height: 1.15;
  margin: 0 1.85rem .5rem 0; color: #fffaf0; font-weight: 800;
}
.profile-community {
  font-family: "IBM Plex Mono", monospace; font-size: .72rem; letter-spacing: .08em;
  font-weight: 700; line-height: 1.35;
}
.profile-body { padding: .95rem 1.05rem 1rem; }
.role-pill {
  display: inline-block; padding: .3rem .68rem; border-radius: 999px;
  background: #eee3cf; color: #8b5a1a; font-family: "IBM Plex Mono", monospace;
  font-size: .7rem; font-weight: 800; margin-bottom: .65rem;
}
.profile-summary { color: #4f463b; font-size: .82rem; line-height: 1.38; margin: 0 0 .85rem; font-weight: 500; }
.profile-section-title {
  font-family: "IBM Plex Mono", monospace; font-size: .68rem; letter-spacing: .18em;
  text-transform: uppercase; color: #a05d17; margin: .85rem 0 .34rem; font-weight: 600;
}
.profile-main { font-weight: 800; color: #211d17; margin-bottom: .1rem; font-size: .9rem; }
.profile-sub { color: #5f5548; font-size: .78rem; line-height: 1.3; font-weight: 500; }
.sentiment-bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden; background: #eadfcc; margin: .5rem 0 .36rem; }
.sent-pos { background: #2BA84A; }
.sent-neu { background: #FFC20A; }
.sent-neg { background: #E0313E; }
.sentiment-labels {
  display: flex; justify-content: space-between; gap: .4rem; color: #6d6254;
  font-family: "IBM Plex Mono", monospace; font-size: .66rem; line-height: 1.25; font-weight: 600;
}
.metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: .7rem; margin-top: .85rem; }
.mini-metric { background: #eee3cf; border-radius: 5px; padding: .65rem; }
.mini-metric strong { display: block; font-family: "IBM Plex Sans", sans-serif; font-size: 1.12rem; line-height: 1; font-weight: 800; color: #211d17; }
.mini-metric span { display: block; margin-top: .3rem; color: #5f5548; font-size: .68rem; font-weight: 500; }
.profile-foot {
  border-top: 1px solid #eadfcc; margin-top: .8rem; padding-top: .65rem;
  display: flex; justify-content: space-between; color: #8b806f;
  font-family: "IBM Plex Mono", monospace; font-size: .68rem; font-weight: 600;
}
@media (max-width: 1050px) { .network-panel { grid-template-columns: 1fr; } .network-card svg { height: 440px; } }
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
        height=520,
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
        height=560,
        title={
            "text": (
                "Posisi Objek dalam Ekosistem: Sentralitas × Sentimen<br>"
                "<sup>ukuran bubble = betweenness · ★ = bridge node · garis = median</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 15, "color": "#11100e"},
        },
        margin={"l": 54, "r": 22, "t": 62, "b": 58},
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

    fig, ax = plt.subplots(figsize=(12.2, 6.8))
    fig.patch.set_facecolor("#fbfaf6")
    ax.set_facecolor("#fbfaf6")

    ax.axvspan(x_med, x.max() * 1.15, ymin=0.5, color="#2A9D8F", alpha=0.05)
    ax.axvspan(x_med, x.max() * 1.15, ymax=0.5, color="#E63946", alpha=0.05)

    for _, r in d.iterrows():
        community = int(r["komunitas"])
        is_bridge = r["nama"] in bridge_names
        color = NOTEBOOK_COMMUNITY_COLORS.get(community, "#999999")
        size = 90 + (float(r["bc"]) / bc_max) * 1250
        ax.scatter(
            float(r["wd"]),
            float(r["balance"]),
            s=size,
            color=color,
            alpha=0.78,
            edgecolors="#1A1A1A",
            linewidths=0.9,
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
            fontsize=7.1,
            color="#222",
        )

    ax.axvline(x_med, color="#666", linestyle="--", linewidth=1.0)
    ax.axhline(y_med, color="#666", linestyle="--", linewidth=1.0)

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
            fontsize=9.0,
            fontweight="bold",
            color=color,
            ha=ha,
            va=va,
            alpha=0.85,
        )

    ax.set_xlabel("Weighted Degree (sentralitas ko-kunjungan) →", fontsize=10.0)
    ax.set_ylabel("Sentiment Balance  (% positif − % negatif) →", fontsize=10.0)
    ax.set_title("")
    ax.tick_params(axis="both", labelsize=8.4)
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
            s=145,
            color="gray",
            edgecolors="#1A1A1A",
            label="Bridge node (BC tinggi)",
        )
    )
    ax.legend(handles=legend_comm, fontsize=7.7, loc="lower left", framealpha=0.92)

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
        height: 100%;
        background: #fbfaf6;
        border: 1px solid #d8d0c2;
        border-radius: 8px;
        padding: 1.1rem 0.35rem 1.05rem;
        box-sizing: border-box;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .svg-plot svg {{
        width: 100% !important;
        height: auto !important;
        max-height: 100%;
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
        height=560,
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
        height=560,
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
      <div class="hero-title-frame">
        <span class="hero-motif hero-motif-left" aria-hidden="true">
          <svg viewBox="0 0 104 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 12H50" stroke="#B56E24" stroke-width="2"/>
            <circle cx="58" cy="12" r="2.6" fill="currentColor"/>
            <path d="M71 4L79 12L71 20L63 12L71 4Z" stroke="currentColor" stroke-width="2.1"/>
            <path d="M87 12H104" stroke="#B56E24" stroke-width="2"/>
          </svg>
        </span>
        <h1><span class="title-line">Ekosistem Pengalaman Publik Cagar Budaya</span> <span class="title-place">Surabaya</span></h1>
        <span class="hero-motif hero-motif-right" aria-hidden="true">
          <svg viewBox="0 0 104 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 12H50" stroke="#B56E24" stroke-width="2"/>
            <circle cx="58" cy="12" r="2.6" fill="currentColor"/>
            <path d="M71 4L79 12L71 20L63 12L71 4Z" stroke="currentColor" stroke-width="2.1"/>
            <path d="M87 12H104" stroke="#B56E24" stroke-width="2"/>
          </svg>
        </span>
      </div>
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
    dimensions = [
        (
            "Diskursif",
            "Topic Modeling",
            "Apa yang dibicarakan — 16 topik BERTopic.",
            "#A76B2A",
            "#F5ECDE",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7A8.4 8.4 0 0 1 4 11.5a8.5 8.5 0 1 1 17 0Z"/></svg>',
        ),
        (
            "Afektif",
            "Sentiment",
            "Bagaimana dinilai — positif · netral · negatif.",
            "#5D7442",
            "#EEF4E5",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M19.5 12.6 12 20l-7.5-7.4a4.7 4.7 0 0 1 0-6.7 4.8 4.8 0 0 1 6.8 0l.7.7.7-.7a4.8 4.8 0 0 1 6.8 0 4.7 4.7 0 0 1 0 6.7Z"/></svg>',
        ),
        (
            "Struktural",
            "SNA",
            "Bagaimana terhubung — komunitas Louvain.",
            "#76506D",
            "#F2E8EE",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg"><circle cx="6" cy="7" r="2.4"/><circle cx="18" cy="7" r="2.4"/><circle cx="12" cy="17" r="2.4"/><path d="M8.2 8.2 10.3 15M15.8 8.2 13.7 15M8.3 7h7.4"/></svg>',
        ),
    ]
    findings = [
        "Objek strategis seperti De Javasche Bank & Masjid Sunan Ampel menghubungkan banyak komunitas, tetapi pengalamannya belum maksimal.",
        "Keluhan parkir, jam operasional, & fasilitas muncul lintas komunitas — isu praktis, bukan penolakan nilai sejarah.",
        "Cagar budaya Surabaya membentuk satu ekosistem pengalaman, bukan kumpulan situs yang terpisah.",
    ]
    metrics = [
        (f"{meta['dataReviews']:,}".replace(",", "."), "data review Google Maps", "#B85C2D", "#F4E5D9"),
        (f"{meta['ulasanTeksValid']:,}".replace(",", "."), "ulasan teks valid", "#5D7442", "#EBF2E2"),
        (meta["jumlahObjek"], "objek cagar budaya", "#76506D", "#EFE5ED"),
        (meta["jumlahTopikFinal"], "topik final", "#A76B2A", "#F4EAD6"),
        (meta["jumlahKomunitas"], "komunitas ko-reviewer", "#2E7371", "#E3F0ED"),
    ]
    dimension_html = "".join(
        f'<div class="dimension-card" style="--accent:{color};--soft:{soft}">'
        f'<span class="dimension-icon">{icon}</span>'
        '<div class="dimension-copy">'
        f'<h3>{html.escape(title)} <span class="method">{html.escape(method)}</span></h3>'
        f'<p>{html.escape(description)}</p>'
        '</div>'
        '</div>'
        for title, method, description, color, soft, icon in dimensions
    )
    metric_html = "".join(
        f'<div class="metric-card" style="--accent:{color};--soft:{soft}"><div class="value">{html.escape(str(value))}</div>'
        f'<div class="label">{html.escape(label)}</div></div>'
        for value, label, color, soft in metrics
    )
    topic_composition = (
        topics.groupby("rumpun", as_index=False)["n"]
        .sum()
        .assign(pct=lambda df: df["n"] / max(float(df["n"].sum()), 1.0) * 100)
    )
    topic_composition["order"] = topic_composition["rumpun"].map(
        {name: idx for idx, name in enumerate(TOPIC_RUMPUN_COLORS)}
    )
    topic_composition = topic_composition.sort_values(["order", "n"], ascending=[True, False])
    discourse_segments = "".join(
        '<span class="discourse-segment" '
        f'style="width:{float(row["pct"]):.2f}%; background:{TOPIC_RUMPUN_COLORS.get(str(row["rumpun"]), "#7E4FC0")}">'
        f'{float(row["pct"]):.0f}%</span>'
        for _, row in topic_composition.iterrows()
    )
    discourse_legend = "".join(
        '<span class="discourse-legend-item">'
        f'<span class="discourse-swatch" style="background:{TOPIC_RUMPUN_COLORS.get(str(row["rumpun"]), "#7E4FC0")}"></span>'
        f'{html.escape(str(row["rumpun"]))}'
        '</span>'
        for _, row in topic_composition.iterrows()
    )
    finding_items = "".join(
        f'<div class="finding-item" style="--accent:{color}"><span class="finding-number">{number}</span>'
        f'<span>{html.escape(finding)}</span></div>'
        for (number, finding), color in zip(enumerate(findings, 1), ["#76506D", "#B85C2D", "#5D7442"])
    )
    overview_html = (
        '<section class="overview-layout">'
        f'<div class="overview-dimensions">{dimension_html}</div>'
        f'<div class="overview-metrics">{metric_html}</div>'
        '<div class="overview-main">'
        '<div class="overview-left-stack">'
        '<div class="dark-card">'
        '<div class="discourse-card">'
        '<div class="discourse-head"><h3>Komposisi Diskursus menurut Rumpun Tema</h3>'
        f'<span class="discourse-total">{html.escape(str(meta["ulasanTeksValid"]))} ulasan</span></div>'
        f'<div class="discourse-bar">{discourse_segments}</div>'
        f'<div class="discourse-legend">{discourse_legend}</div>'
        '</div>'
        '<div class="eyebrow">◆ Temuan Inti</div>'
        '<h2>Sentralitas jaringan tidak selalu sejalan dengan kepuasan pengunjung.</h2>'
        '<p>Objek paling strategis — <strong>De Javasche Bank</strong> atau <strong>Masjid Sunan Ampel</strong> — belum tentu paling disukai; objek bersentimen sangat positif justru sering periferal. Kelola berdasarkan posisi struktural, bukan sekadar kepuasan.</p></div>'
        '</div>'
        '<div class="findings-card">'
        '<div class="finding-list-title">Apa yang ditemukan integrasi</div>'
        f'{finding_items}'
        '</div>'
        '</div>'
        '</section>'
    )
    st.markdown(overview_html, unsafe_allow_html=True)

with tab_objects:
    control_left, control_right = st.columns([2.45, .92])
    with control_left:
        mode_col, community_col = st.columns([1.65, 1])
        with mode_col:
            color_mode = st.radio(
                "Dimensi warna",
                ["Struktural · SNA", "Diskursif · Topik", "Spasial · Kawasan"],
                horizontal=True,
                label_visibility="collapsed",
                key="network_color_mode",
            )
        with community_col:
            st.markdown(
                '<div class="network-kicker">Filter Komunitas</div>',
                unsafe_allow_html=True,
            )
            selected_communities = community_filter_control(communities)
    with control_right:
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
        st.markdown('<div class="network-panel-lift"></div>', unsafe_allow_html=True)
        components.html(
            build_network_panel(
                network_objects,
                network_edges,
                color_mode,
                community_colors,
                communities,
            ),
            height=570,
            scrolling=False,
        )

with tab_topics:
    classified_reviews = f'{int(topics["n"].sum()):,}'.replace(",", ".")
    quadrant_col, topic_col = st.columns([1.65, .95])
    community_inline_legend = "".join(
        '<span class="community-inline-item">'
        f'<span class="topic-legend-swatch" style="background:{NOTEBOOK_COMMUNITY_COLORS.get(int(row.id), "#999")}"></span>'
        f'K-{int(row.id)} · {html.escape(str(row.nama))}'
        '</span>'
        for row in communities.sort_values("id").itertuples()
        if int(row.id) in NOTEBOOK_COMMUNITY_COLORS
    )

    with quadrant_col:
        st.markdown(
            f"""
            <div class="quadrant-head">
              <h3>Posisi Objek: Sentralitas × Sentimen</h3>
              <p>Sumbu-X = sentralitas jaringan · sumbu-Y = keseimbangan sentimen (positif − negatif). Garis putus = median.</p>
              <div class="quadrant-mini-legend">★ bridge <span><span class="legend-dot"></span>= betweenness</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if MATPLOTLIB_AVAILABLE:
            components.html(
                matplotlib_svg_html(quadrant_matplotlib_figure(filtered, communities)),
                height=500,
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
            f'<div class="community-inline-legend">{community_inline_legend}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="plot-note">
              median WD {filtered["wd"].median():.0f} · median balance {filtered["balance"].median():.1f}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with topic_col:
        st.markdown(topic_panel_html(topics, classified_reviews), unsafe_allow_html=True)

with tab_priorities:
    left_col, right_col = st.columns([1.42, 1])

    with left_col:
        st.markdown(
            '<div class="priority-kicker">Lima Kelompok Prioritas</div>'
            '<p class="section-explain">Prioritas dibaca dari gabungan sentimen, topik dominan, dan posisi jaringan.</p>',
            unsafe_allow_html=True,
        )
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
                  <div class="strategy-copy">Jaga objek bersentimen kuat sebagai anchor narasi, promosi, dan rute heritage.</div>
                </div>
              </div>
              <div class="strategy-item">
                <div class="strategy-number">2</div>
                <div>
                  <div class="strategy-title">Perkuat objek strategis</div>
                  <div class="strategy-copy">Bridge node berdampak lintas komunitas; prioritaskan akses, fasilitas, dan informasi.</div>
                </div>
              </div>
              <div class="strategy-item">
                <div class="strategy-number">3</div>
                <div>
                  <div class="strategy-title">Perbaiki isu operasional</div>
                  <div class="strategy-copy">Tangani parkir, fasilitas, tarif, kebersihan, dan jam kunjungan yang muncul lintas objek.</div>
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

