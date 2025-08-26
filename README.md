
# Warehouse Mapper (Streamlit) — Two-file layout

This version splits the app into:
- `app.py` — main UI flow
- `visualization.py` — data loading, validation, editor, and map rendering

## CSV format
- **Latitude** in one column, **Longitude** in another (defaults to first two columns if unlabeled).
- Optional: a `color` column (hex like `#FF0000`). If missing, the app creates one you can edit.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. New app → select your repo/branch → Main file `app.py` → Deploy.

## Notes
- Uses pydeck ScatterplotLayer with per-point colors.
- If your Streamlit version lacks `ColorColumn`, the editor falls back to a text hex field.
