
import io
from typing import List
import pandas as pd
import streamlit as st
import pydeck as pdk

@st.cache_data
def load_csv(file) -> pd.DataFrame:
    "Read CSV whether it has headers or not."
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
    # Ensure a color column exists
    if "color" not in out.columns:
        out["color"] = "#3388ff"
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

def render_editor_and_map(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    "Show a data editor with per-row color editing and render a pydeck map."
    st.subheader("2) Customize colors for each warehouse")
    st.caption("Edit the **color** column below. Tip: paste a hex color like `#FF8800`.")

    # Compatibility: use ColorColumn if available, else TextColumn fallback
    has_color_column = hasattr(st.column_config, "ColorColumn")
    if has_color_column:
        color_cfg = st.column_config.ColorColumn("Color")
    else:
        color_cfg = st.column_config.TextColumn("Color (hex like #3388ff)")

    edited_df = st.data_editor(
        df[[lat_col, lon_col, "color"]],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            lat_col: st.column_config.NumberColumn("Latitude", format="%.6f", step=0.000001, disabled=True),
            lon_col: st.column_config.NumberColumn("Longitude", format="%.6f", step=0.000001, disabled=True),
            "color": color_cfg,
        },
        key="editor",
    )

    # Sanitize colors if TextColumn fallback is used
    if not has_color_column:
        edited_df["color"] = edited_df["color"].astype(str).str.strip()
        edited_df["color"] = edited_df["color"].apply(
            lambda c: c if isinstance(c, str) and c.startswith("#") and len(c) in (4, 7) else "#3388ff"
        )

    # Compute RGB columns
    rgb = edited_df["color"].map(hex_to_rgb)
    edited_df["r"] = rgb.map(lambda x: x[0])
    edited_df["g"] = rgb.map(lambda x: x[1])
    edited_df["b"] = rgb.map(lambda x: x[2])

    # Map
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
    deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
    st.pydeck_chart(deck, use_container_width=True)

    return edited_df

def to_geojson_bytes(df: pd.DataFrame, lat_col: str, lon_col: str) -> io.BytesIO:
    geojson_str = '{"type":"FeatureCollection","features":[' + ",".join([
        f'{{"type":"Feature","geometry":{{"type":"Point","coordinates":[{float(row[lon_col])},{float(row[lat_col])}]}},'
        f'"properties":{{"color":"{row["color"]}"}}}}'
        for _, row in df.iterrows()
    ]) + ']}'
    return io.BytesIO(geojson_str.encode("utf-8"))
