# Dashboard Native Streamlit

Versi native dari prototype Dashboard Narasi Integratif Tugas Akhir.

## Menjalankan aplikasi

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Sumber data

Dashboard memakai input kanonik di `data/input/`:

- `df_final_topic_gmaps.xlsx`
- `obp_object_profile_final.xlsx` — prioritas utama untuk profil OBP dan visual
  Sentralitas × Sentimen, karena berisi `sentiment_balance = pct_positive -
  pct_negative` dari hasil prediksi adaptif notebook.
- `integrasi_sna_topik_final.xlsx` — fallback jika file OBP final belum tersedia.
- `GMaps_Reviews_Merged_Clean.xlsx`
- `GMaps_Reviews_With_Coordinates.xlsx`

`data_pipeline.py` mengolahnya menjadi:

- ringkasan 16 topik final dari data per ulasan;
- profil topik, sentimen, sentralitas, dan koordinat spasial untuk 27 objek;
- 183 edge ko-reviewer empiris dengan bobot minimal 2;
- tabel Object-Based Profile (OBP) dengan aturan klasifikasi yang sama seperti notebook.

File `data/bab4.json` tetap digunakan hanya untuk narasi, warna komunitas,
fallback koordinat objek, definisi peran, dan prioritas interpretif. Hasil olahan cache
disimpan di `data/processed/`.

Untuk membangun ulang seluruh hasil olahan:

```bash
python data_pipeline.py
```
