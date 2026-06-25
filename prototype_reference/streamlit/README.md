# Paket Streamlit — Dashboard Narasi Integratif

Isi folder ini:

| File | Untuk apa |
|------|-----------|
| `dashboard.html` | Dashboard lengkap, **satu file mandiri** (offline, semua aset inline). |
| `app.py` | Aplikasi Streamlit yang menampilkan `dashboard.html` apa adanya. |
| `bab4.json` | **Semua data Bab 4** terstruktur (27 objek, 16 topik, 4 komunitas, sentralitas, sentimen, prioritas) — untuk kalau kamu mau bangun ulang visualisasi pakai widget Python. |

---

## Jalur A — Tampilkan dashboard apa adanya (paling cepat)

```bash
pip install streamlit
streamlit run app.py
```

Streamlit jadi "bingkai" — semua interaktivitas (graph, toggle dimensi, filter, panel detail, scatter kuadran) tetap berjalan dari dalam `dashboard.html`. Tidak perlu menulis ulang apa pun.

> Catatan: atur tinggi lewat parameter `height=` di `app.py` bila perlu.

---

## Jalur B — Bangun ulang native di Streamlit

Kalau kamu ingin pakai widget Python (`st.tabs`, Plotly, networkx/pyvis), pakai `bab4.json` sebagai sumber data:

```python
import json, pandas as pd, streamlit as st
import plotly.express as px

data = json.load(open("bab4.json", encoding="utf-8"))
obj = pd.DataFrame(data["objek"])
kom = {k["id"]: k for k in data["komunitas"]}

# contoh: scatter kuadran Sentralitas × Sentimen
obj["balance"] = obj["pos"] - obj["neg"]
obj["komunitas_nama"] = obj["komunitas"].map(lambda i: kom[i]["nama"])
fig = px.scatter(
    obj, x="wd", y="balance", size="bc", color="komunitas_nama",
    hover_name="nama", size_max=40,
    labels={"wd": "Weighted degree", "balance": "Sentiment balance (pos − neg)"},
)
fig.add_vline(x=obj["wd"].median(), line_dash="dash")
fig.add_hline(y=obj["balance"].median(), line_dash="dash")
st.plotly_chart(fig, use_container_width=True)
```

Struktur `bab4.json`:
- `meta` — angka ringkasan (jumlah review, objek, topik, dst).
- `objek[]` — `nama, komunitas, peran, topikUtama, topikPendamping, wd` (weighted degree), `bc` (betweenness), `pos/neg` (% sentimen), `reviews, teks, lat, lon`.
- `topik[]` — 16 topik final + `n, pct, keywords, rumpun`.
- `komunitas[]` — 4 komunitas Louvain + bridge node & peran.
- `prioritas[]` — 5 kelompok prioritas + implikasi pengelolaan.

Untuk jaringan ko-reviewer, gunakan `wd`/`bc` + komunitas tiap objek dengan `networkx` lalu render via `pyvis` atau `st.plotly_chart`.

---

**Rekomendasi:** mulai dari **Jalur A** untuk demo/sidang (cepat & persis), lalu migrasi bertahap ke **Jalur B** kalau perlu kontrol penuh ala Python.
