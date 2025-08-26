
import io
import pandas as pd
import streamlit as st

from visualization import (
    load_csv,
    coerce_latlon,
    render_editor_and_map,
    to_geojson_bytes,
)

st.set_page_config(page_title="Warehouse Mapper", page_icon="🗺️", layout="wide")
st.title("🗺️ Warehouse Mapper")
st.write(
    "Upload a CSV with **latitude in column A** and **longitude in column B** (or choose the columns), "
    "then pick a custom color for **each** warehouse."
)

uploaded = st.file_uploader("Upload CSV", type=["csv"])

with st.expander("Need a sample? Click to download a template CSV.", expanded=False):
    sample = pd.DataFrame({
        "latitude": [34.0522, 40.7128, 41.8781],
        "longitude": [-118.2437, -74.0060, -87.6298],
    })
    st.download_button("Download sample.csv", sample.to_csv(index=False).encode("utf-8"), file_name="sample.csv", mime="text/csv")

if not uploaded:
    st.info("Upload a CSV to get started.")
    st.stop()

# Load CSV (header/no-header safe)
df_raw = load_csv(uploaded)
df_raw_columns = list(df_raw.columns)
if len(df_raw_columns) < 2:
    st.error("Your CSV needs at least two columns for latitude and longitude.")
    st.stop()

st.subheader("1) Choose latitude & longitude columns")
col1, col2 = st.columns(2)
with col1:
    lat_col = st.selectbox("Latitude column", options=df_raw_columns, index=0)
with col2:
    lon_col = st.selectbox("Longitude column", options=df_raw_columns, index=1 if len(df_raw_columns) > 1 else 0)

df = coerce_latlon(df_raw, lat_col, lon_col)
if df.empty:
    st.error("No valid latitude/longitude values found after parsing. Please check your CSV.")
    st.stop()

# 2) Editor + Map
edited_df = render_editor_and_map(df, lat_col, lon_col)

# 3) Downloads
st.subheader("4) Export edited data")
left, right = st.columns(2)
csv_bytes = edited_df[[lat_col, lon_col, "color"]].to_csv(index=False).encode("utf-8")
with left:
    st.download_button("⬇️ Download CSV with colors", csv_bytes, file_name="warehouses_with_colors.csv", mime="text/csv")
with right:
    st.download_button("⬇️ Download GeoJSON", data=to_geojson_bytes(edited_df, lat_col, lon_col), file_name="warehouses.geojson", mime="application/geo+json")

st.markdown("---")
with st.expander("Notes & Tips"):
    st.markdown(
        "- Column order doesn't matter—you can choose which columns hold latitude/longitude.\n"
        "- If your CSV already contains a **color** column (hex like `#FF8800`), it will be used.\n"
        "- The map uses **pydeck** so each point can have its own color.\n"
        "- If your Streamlit version is older and lacks `ColorColumn`, this app falls back to a text hex editor."
    )
