# utils_pro.py

import pandas as pd
import geopandas as gpd
from pathlib import Path
from .utils import normalize_names

# helper function to normalize district names
def normalize_one(x: str) -> str:
    if not isinstance(x, str):
        return ""
    return (
        x.strip()
         .lower()
         .replace("  ", " ")
         .replace("—", "-")
         .replace("–", "-")
    )

# ------------------------
# Load Data
# ------------------------

CSV_PATH = Path("data/provincial/provincial_combined.csv")
SHP_PATH = Path("data/provincial/ELECTORAL_DISTRICT.shp")  # adjust your path

prov_all = pd.read_csv(CSV_PATH)
gdf_prov = gpd.read_file(SHP_PATH)

# ------------------------
# Dash Cleaning Function
# ------------------------

def clean_dashes(x):
    if isinstance(x, str):
        return (
            x.replace("â€”","—")
             .replace("â€“","–")
             .replace("--","—")
             .strip()
        )
    return x

# Clean CSV district names
for col in ["ElectoralDistrictNameEnglish", "ElectoralDistrictNameFrench"]:
    prov_all[col] = prov_all[col].apply(clean_dashes)

# ------------------------
# Official Toronto Districts (normalized)
# ------------------------

toronto_districts = [
    "beaches-east york", "davenport", "don valley east", "don valley west",
    "don valley north", "eglinton-lawrence", "etobicoke centre",
    "etobicoke north", "etobicoke-lakeshore", "humber river-black creek",
    "parkdale-high park", "scarborough centre", "scarborough-agincourt",
    "scarborough-guildwood", "scarborough north", "scarborough-rouge park",
    "scarborough southwest", "spadina-fort york", "toronto-st. paul's",
    "toronto centre", "toronto-danforth", "university-rosedale",
    "willowdale", "york centre", "york south-weston"
]

toronto_districts = [normalize_one(x) for x in toronto_districts]

# ------------------------
# Main Function
# ------------------------

def get_provincial_map(year: int):

    # Filter election data
    df = prov_all[prov_all["year"] == year].copy()
    df["ElectoralDistrictNumber"] = pd.to_numeric(df["ElectoralDistrictNumber"], errors="coerce")

    # Clean & normalize shapefile
    gdf = gdf_prov.copy()
    gdf["ED_ID"] = pd.to_numeric(gdf["ED_ID"], errors="coerce")

    # Normalize district names in shapefile
    gdf["name_clean"] = gdf["ENGLISH_NA"].apply(normalize_one)

    # Toronto-only filter (exact matching)
    gdf = gdf[gdf["name_clean"].isin(toronto_districts)]

    # Merge the shapefile + CSV
    merged = gdf.merge(
        df,
        left_on="ED_ID",
        right_on="ElectoralDistrictNumber",
        how="left"
    )

    return merged
