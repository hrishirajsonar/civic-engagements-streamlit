import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
from src.utils_pro import get_provincial_map

# ------------------------------
# Page Title
# ------------------------------
st.title("Toronto Provincial Election - Voter Participation Map")


# ------------------------------
# Year Selector
# ------------------------------
year = st.selectbox("Select Election Year", [2018, 2022], index=1)


# ------------------------------
# Load Toronto-Only Map Data
# ------------------------------
gdf = get_provincial_map(year)

if gdf is None or len(gdf) == 0:
    st.error("No Toronto provincial districts found for this election year.")
    st.stop()

# Clean turnout column
turnout_col = "VoterTurnoutPercentageOfList"
gdf[turnout_col] = gdf[turnout_col].astype(float)


# ------------------------------
# Data Cards: Highest, Lowest, Average Turnout
# ------------------------------
max_idx = gdf[turnout_col].astype(float).idxmax()
min_idx = gdf[turnout_col].astype(float).idxmin()

max_row = gdf.loc[max_idx]
min_row = gdf.loc[min_idx]

max_name = max_row["ENGLISH_NA"]
min_name = min_row["ENGLISH_NA"]

max_turnout = max_row[turnout_col]
min_turnout = min_row[turnout_col]
avg_turnout = gdf[turnout_col].mean()

c3, c1, c2 = st.columns(3)

with c3:
    st.markdown("### Average Turnout")
    # st.markdown("<br>", unsafe_allow_html=True)  # spacing for alignment
    st.markdown(f"<h2 style='margin-top:-10px'>{avg_turnout:.2%}</h2>", unsafe_allow_html=True)

with c1:
    st.markdown("### Highest Turnout")
    st.markdown(f"**{max_name}**")
    st.markdown(f"<h2 style='margin-top:-10px'>{max_turnout:.2%}</h2>", unsafe_allow_html=True)

with c2:
    st.markdown("### Lowest Turnout")
    st.markdown(f"**{min_name}**")
    st.markdown(f"<h2 style='margin-top:-10px'>{min_turnout:.2%}</h2>", unsafe_allow_html=True)



# ------------------------------
# Create Toronto Map
# ------------------------------
m = folium.Map(location=[43.7, -79.4], zoom_start=10)


# ------------------------------
# Color Ramp (Blue Gradient)
# ------------------------------
colormap = cm.LinearColormap(
    ["#deebf7", "#9ecae1", "#3182bd"],
    vmin=min_turnout,
    vmax=max_turnout
)
colormap.caption = "Voter Turnout (%)"
colormap.add_to(m)

# assign color to each riding
gdf["color"] = gdf[turnout_col].apply(colormap)


# ------------------------------
# Hover Tooltip
# ------------------------------
tooltip = folium.GeoJsonTooltip(
    fields=["ENGLISH_NA", "VoterTurnoutPercentageOfList"],
    aliases=["District:", "Turnout:"],
    localize=True,
    sticky=True,
    labels=True
)


# ------------------------------
# Polygon Layer with Tooltip
# ------------------------------
folium.GeoJson(
    gdf,
    tooltip=tooltip,
    style_function=lambda feature: {
        "fillColor": feature["properties"]["color"],
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.85,
    }
).add_to(m)


# ------------------------------
# Render Map in Streamlit
# ------------------------------
st_folium(m, height=650, width=900)
