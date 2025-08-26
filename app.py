
import io
from typing import Tuple, List

import pandas as pd
import streamlit as st
import pydeck as pdk

st.set_page_config(page_title="Warehouse Mapper", page_icon="🗺️", layout="wide")
st.title("🗺️ Warehouse Mapper")
st.write(
    "Upload a CSV with **latitude in column A** and **longitude in column B** (or choose the columns), "
    "then pick a custom color for **each** warehouse."
)

@st.cache_data
def load_csv(file) -> pd.DataFrame:
    # Try reading with header; if first two columns aren't numeric, try no header.
    try:
        df = pd.read_csv(file)
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, header=None)
    return df

def coerce_latlon(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    out = df.copy()
    out[lat_col] = pd.to_numeric(out[lat_col], errors="coerce")
    out[lon_col] = pd.to_numeric(out[lon_col], errors="coerce")
    out = out.dropna(subset=[lat_col, lon_col])
    return out

def hex_to_rgb(hex_color: str) -> List[int]:
    if not isinstance(hex_color, str):
        return [51, 136, 255]  # default bluish
    hc = hex_color.strip().lstrip("#")
    if len(hc) == 3:
        hc = "".join(ch*2 for ch in hc)
    if len(hc) != 6:
        return [51, 136, 255]
    try:
        return [int(hc[i:i+2], 16) for i in (0, 2, 4)]
    except Exception:
        return [51, 136, 255]

def make_view_state(df: pd.DataFrame, lat_col: str, lon_col: str) -> pdk.ViewState:
    if df.empty:
        return pdk.ViewState(latitude=39.8283, longitude=-98.5795, zoom=3)  # USA centroid
    lat = df[lat_col].mean()
    lon = df[lon_col].mean()
    return pdk.ViewState(latitude=float(lat), longitude=float(lon), zoom=4)

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

# Load CSV
df_raw = load_csv(uploaded)
df_raw_columns = list(df_raw.columns)
default_lat_col = df_raw_columns[0] if len(df_raw_columns) > 0 else None
default_lon_col = df_raw_columns[1] if len(df_raw_columns) > 1 else None

st.subheader("1) Choose latitude & longitude columns")
col1, col2 = st.columns(2)
with col1:
    lat_col = st.selectbox("Latitude column", options=df_raw_columns, index=0 if default_lat_col in df_raw_columns else 0)
with col2:
    lon_col = st.selectbox("Longitude column", options=df_raw_columns, index=1 if default_lon_col in df_raw_columns else 0)

df = coerce_latlon(df_raw, lat_col, lon_col)
if df.empty:
    st.error("No valid latitude/longitude values found after parsing. Please check your CSV.")
    st.stop()

# Ensure a color column exists
if "color" not in df.columns:
    df["color"] = "#3388ff"

st.subheader("2) Customize colors for each warehouse")
st.caption("Edit the **color** column below. Tip: you can copy/paste a hex color starting with #.")
edited_df = st.data_editor(
    df[[lat_col, lon_col, "color"]],
    use_container_width=True,
    num_rows="fixed",
    column_config={
        lat_col: st.column_config.NumberColumn("Latitude", format="%.6f", step=0.000001, disabled=True),
        lon_col: st.column_config.NumberColumn("Longitude", format="%.6f", step=0.000001, disabled=True),
        "color": st.column_config.ColorColumn("Color"),
    },
    key="editor",
)

# Compute RGB columns for pydeck
rgb = edited_df["color"].map(hex_to_rgb)
edited_df["r"] = rgb.map(lambda x: x[0])
edited_df["g"] = rgb.map(lambda x: x[1])
edited_df["b"] = rgb.map(lambda x: x[2])

# PyDeck layer
st.subheader("3) Map preview")
tooltip = {
    "html": f"<b>Lat:</b> {{{lat_col}}}<br/><b>Lon:</b> {{{lon_col}}}<br/><b>Color:</b> {{{{color}}}}",
    "style": {"backgroundColor": "steelblue", "color": "white"}
}
layer = pdk.Layer(
    "ScatterplotLayer",
    data=edited_df,
    get_position=[lon_col, lat_col],
    get_fill_color="[r, g, b]",
    get_radius=7000,
    pickable=True,
    auto_highlight=True,
)
view_state = make_view_state(edited_df, lat_col, lon_col)
deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style="mapbox://styles/mapbox/light-v10")
st.pydeck_chart(deck, use_container_width=True)

st.subheader("4) Export edited data")
left, right = st.columns(2)
csv_bytes = edited_df[[lat_col, lon_col, "color"]].to_csv(index=False).encode("utf-8")
with left:
    st.download_button("⬇️ Download CSV with colors", csv_bytes, file_name="warehouses_with_colors.csv", mime="text/csv")

# Export as GeoJSON
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row[lon_col]), float(row[lat_col]) ]},
            "properties": {"color": row["color"]},
        }
        for _, row in edited_df.iterrows()
    ],
}
with right:
    st.download_button("⬇️ Download GeoJSON", data=io.BytesIO(bytes(str(geojson), "utf-8")), file_name="warehouses.geojson", mime="application/geo+json")

st.markdown("---")
with st.expander("Notes & Tips"):
    st.markdown(
        "- Column order doesn't matter—you can choose which columns hold latitude/longitude.\n"
        "- If your CSV already contains a **color** column (hex like `#FF8800`), it will be used.\n"
        "- The map uses **pydeck** so each point can have its own color."
    )
