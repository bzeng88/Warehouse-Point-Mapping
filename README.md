
# Warehouse Mapper (Streamlit)

A lightweight Streamlit app that maps warehouse locations from a CSV and lets you set a custom color for **each** warehouse.

## CSV format
- Put **latitude** in column A and **longitude** in column B (or just choose the columns after upload).
- Optional: include a `color` column (hex like `#FF0000`). If missing, the app adds one you can edit.

## Quick start (local)
```bash
# 1) Create & activate a virtual env (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Deploy to Streamlit Community Cloud
1. Push this folder to a public GitHub repo.
2. Go to Streamlit Community Cloud → New app → select your repo/branch → set **Main file path** to `app.py`.
3. Deploy.

## How it works
- Upload a CSV → choose which columns are latitude/longitude.
- Edit the `color` column via Streamlit's color editor.
- Points are rendered with **pydeck ScatterplotLayer**, which supports per-point colors.
- Download the edited CSV (with colors) or a GeoJSON for use elsewhere.

## Troubleshooting
- If nothing shows on the map, confirm your lat/lon columns are numeric (no text).
- If your CSV lacks headers, the app will still load; you'll be able to pick the first two columns.
