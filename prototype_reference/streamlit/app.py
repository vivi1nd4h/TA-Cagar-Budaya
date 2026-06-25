# app.py — Dashboard Narasi Integratif (Cagar Budaya Surabaya)
# Jalur A: menampilkan dashboard HTML mandiri apa adanya di dalam Streamlit.
#
# Jalankan:
#   pip install streamlit
#   streamlit run app.py
#
# Letakkan file ini sefolder dengan dashboard.html

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Narasi Integratif — Cagar Budaya Surabaya",
    layout="wide",
)

# Hilangkan padding bawaan Streamlit agar dashboard tampil penuh
st.markdown(
    "<style>.block-container{padding:0 !important;max-width:100% !important;}</style>",
    unsafe_allow_html=True,
)

html = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
st.components.v1.html(html, height=1600, scrolling=True)
