import streamlit as st
import folium
import numpy as np
from streamlit_folium import st_folium
import branca.colormap as cm

from src.utils import load_gpkg, load_federal_csv, prepare_map_df

# Page Layout
st.set_page_config(page_title="Federal Voter Participation Map", layout="wide")
st.title("Toronto Federal Election - Voter Participation Map")

# Load Data
gdf_all = load_gpkg("data/combined_toronto_ridings.gpkg")
df_fed = load_federal_csv("data/federal_combined.csv")

years = sorted(df_fed["year"].dropna().unique())

# ------------------------------------------------------
# Year Selector (TOP — like provincial)
# ------------------------------------------------------
year = st.selectbox("Select Election Year", years, index=len(years)-1)

# ------------------------------------------------------
# Prepare Federal Map Data
# ------------------------------------------------------
merged = prepare_map_df(gdf_all, df_fed, year)

if merged is None or len(merged) == 0:
    st.error("No Toronto federal districts found for this election year.")
    st.stop()

# Standard participation column
value_col = "voter_participation_pct"

merged[value_col] = merged[value_col].astype(float)

# ------------------------------------------------------
# TOP METRICS — SAME STYLE AS PROVINCIAL
# ------------------------------------------------------
max_idx = merged[value_col].idxmax()
min_idx = merged[value_col].idxmin()

max_row = merged.loc[max_idx]
min_row = merged.loc[min_idx]

max_name = max_row["riding_name"]
min_name = min_row["riding_name"]

max_turnout = max_row[value_col] / 100
min_turnout = min_row[value_col] / 100
avg_turnout = merged[value_col].mean() / 100

c3, c1, c2 = st.columns(3)

with c3:
    st.markdown("### Average Turnout")
    st.markdown(f"<h2 style='margin-top:-10px'>{avg_turnout:.2%}</h2>", unsafe_allow_html=True)

with c1:
    st.markdown("### Highest Turnout")
    st.markdown(f"**{max_name}**")
    st.markdown(f"<h2 style='margin-top:-10px'>{max_turnout:.2%}</h2>", unsafe_allow_html=True)

with c2:
    st.markdown("### Lowest Turnout")
    st.markdown(f"**{min_name}**")
    st.markdown(f"<h2 style='margin-top:-10px'>{min_turnout:.2%}</h2>", unsafe_allow_html=True)

# ------------------------------------------------------
# BLUE COLOR GRADIENT (same as provincial)
# ------------------------------------------------------
vmin = merged[value_col].min()
vmax = merged[value_col].max()

colormap = cm.LinearColormap(
    ["#deebf7", "#9ecae1", "#3182bd"],
    vmin=vmin,
    vmax=vmax
)
colormap.caption = "Voter Participation (%)"

# ------------------------------------------------------
# Create Map
# ------------------------------------------------------
m = folium.Map(location=[43.7, -79.4], zoom_start=10)

def style_function(feature):
    val = feature["properties"].get(value_col)
    if val is None or np.isnan(val):
        return {"fillColor": "#cccccc", "color": "black", "weight": 0.5, "fillOpacity": 0.4}
    
    return {
        "fillColor": colormap(val),
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.85,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["riding_name", value_col],
    aliases=["District:", "Turnout (%):"],
    localize=True,
    sticky=True,
    labels=True
)

folium.GeoJson(
    merged,
    style_function=style_function,
    tooltip=tooltip
).add_to(m)

colormap.add_to(m)

# ------------------------------------------------------
# Render Map
# ------------------------------------------------------
st_folium(m, height=650, width=900)

# ------------------------------------------------------
# Underlying Data (hidden in an expander)
# ------------------------------------------------------
#with st.expander("Show underlying data"):
    #st.dataframe(merged.drop(columns="geometry"))
