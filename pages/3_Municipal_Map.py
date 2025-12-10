# 3_Municipal_Map.py

from __future__ import annotations
import json
import geopandas as gpd
import pandas as pd
import streamlit as st
import pydeck as pdk

from src.utils_mun import (
    load_municipal_geometries,
    load_municipal_turnout,
    get_available_years,
    prepare_municipal_year_gdf,
    compute_turnout_summary,
)

# ------------------------------------------------------
# Page Config
# ------------------------------------------------------
st.set_page_config(
    page_title="Toronto Municipal Voter Turnout Map",
    layout="wide",
)

# ------------------------------------------------------
# Cache Loaders
# ------------------------------------------------------
@st.cache_data
def get_turnout_df():
    return load_municipal_turnout()

@st.cache_data
def get_geom_gdf():
    return load_municipal_geometries()


# ------------------------------------------------------
# Main Page
# ------------------------------------------------------
def main():

    st.title("Toronto Municipal Election — Voter Turnout Map")

    turnout_df = get_turnout_df()
    geom_gdf = get_geom_gdf()

    # ------------------------------
    # Year Selector (TOP)
    # ------------------------------
    years = get_available_years(turnout_df)
    year = st.selectbox("Select Election Year", years, index=len(years)-1)

    # Load year-specific geometry + turnout
    gdf_year = prepare_municipal_year_gdf(year, geom_gdf, turnout_df)

    # Summary stats (PctVoted is 0–1 => convert to 0–100)
    summary = compute_turnout_summary(gdf_year)

    avg_turnout = summary["mean"] * 100 if summary["mean"] is not None else None
    min_turnout = summary["min"] * 100 if summary["min"] is not None else None
    max_turnout = summary["max"] * 100 if summary["max"] is not None else None

    # Determine highest / lowest turnout subdivisions
    if len(gdf_year) > 0:
        max_row = gdf_year.loc[gdf_year["PctVoted"].idxmax()]
        min_row = gdf_year.loc[gdf_year["PctVoted"].idxmin()]

        highest_label = f"Ward {max_row['Ward']} – Sub {max_row['Sub']}"
        lowest_label = f"Ward {min_row['Ward']} – Sub {min_row['Sub']}"

        highest_val = max_row["PctVoted"] * 100
        lowest_val = min_row["PctVoted"] * 100
    else:
        highest_label = lowest_label = "N/A"
        highest_val = lowest_val = None

    # ------------------------------
    # KPI Cards (Consistent Style)
    # ------------------------------
    c3, c1, c2, c4 = st.columns(4)

    with c3:
        st.markdown("### Average Turnout")
        st.markdown(
            f"<h2 style='margin-top:-10px'>{avg_turnout:.2f}%</h2>"
            if avg_turnout is not None else "<h2>N/A</h2>",
            unsafe_allow_html=True
        )

    with c1:
        st.markdown("### Highest Turnout")
        st.markdown(f"**{highest_label}**")
        st.markdown(
            f"<h2 style='margin-top:-10px'>{highest_val:.2f}%</h2>"
            if highest_val is not None else "<h2>N/A</h2>",
            unsafe_allow_html=True
        )

    with c2:
        st.markdown("### Lowest Turnout")
        st.markdown(f"**{lowest_label}**")
        st.markdown(
            f"<h2 style='margin-top:-10px'>{lowest_val:.2f}%</h2>"
            if lowest_val is not None else "<h2>N/A</h2>",
            unsafe_allow_html=True
        )

    with c4:
        st.markdown("### Total Subdivisions")
        st.markdown(f"<h2 style='margin-top:-10px'>{summary['n']}</h2>", unsafe_allow_html=True)

    # ------------------------------------------------------
    # TRUE PROVINCIAL BLUE GRADIENT (EXACT MATCH)
    # ------------------------------------------------------
    def turnout_to_color(p):
        if p is None or pd.isna(p):
            return [210, 210, 210]  # grey

        # Convert 0–1 → 0–100
        p = p * 100
        ratio = max(0, min(p / 100, 1))

        # Provincial gradient:
        # light => medium => dark
        light = (222, 235, 247)   # #deebf7
        mid   = (158, 202, 225)   # #9ecae1
        dark  = (49, 130, 189)    # #3182bd

        # Two-step interpolation
        if ratio < 0.5:
            t = ratio / 0.5
            r = int(light[0] + (mid[0] - light[0]) * t)
            g = int(light[1] + (mid[1] - light[1]) * t)
            b = int(light[2] + (mid[2] - light[2]) * t)
        else:
            t = (ratio - 0.5) / 0.5
            r = int(mid[0] + (dark[0] - mid[0]) * t)
            g = int(mid[1] + (dark[1] - mid[1]) * t)
            b = int(mid[2] + (dark[2] - mid[2]) * t)

        return [r, g, b]

    # Build GeoJSON with consistent colors
    gjson = json.loads(gdf_year.to_json())
    for f in gjson["features"]:
        p = f["properties"].get("PctVoted", None)
        f["properties"]["color"] = turnout_to_color(p)

    # ------------------------------
    # PyDeck Layer
    # ------------------------------
    layer = pdk.Layer(
        "GeoJsonLayer",
        gjson,
        opacity=0.85,
        stroked=True,
        filled=True,
        get_fill_color="properties.color",
        get_line_color=[70, 70, 70],
        line_width_min_pixels=0.4,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=43.70,
        longitude=-79.38,
        zoom=9.7,
        pitch=0,
    )

    tooltip = {
        "html":
            "<b>Ward:</b> {Ward}<br/>"
            "<b>Subdivision:</b> {Sub}<br/>"
            "<b>% Voted:</b> {PctVoted}",
        "style": {
            "backgroundColor": "rgba(0, 0, 60, 0.7)",
            "color": "white",
            "font-size": "14px",
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10",
    )

    st.pydeck_chart(deck)

    # ------------------------------
    # Data Table (converted to %)
    # ------------------------------
    with st.expander("Show Data Table"):
        df_display = gdf_year.copy()
        df_display["PctVoted"] = df_display["PctVoted"] * 100

        st.dataframe(
            df_display[["Year", "Ward", "Sub", "PctVoted"]]
            .sort_values(["Ward", "Sub"]),
            use_container_width=True
        )


if __name__ == "__main__":
    main()