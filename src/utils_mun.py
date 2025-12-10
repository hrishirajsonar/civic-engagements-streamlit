# src/utils_mun.py

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Tuple, Dict, Any

import geopandas as gpd
import pandas as pd


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
# Adjust this if your layout is different
BASE_DIR = Path(__file__).resolve().parent.parent
MUN_DATA_DIR = BASE_DIR / "data" / "municipal"

DEFAULT_GPKG_PATH = MUN_DATA_DIR / "combined_toronto_municipal.gpkg"
DEFAULT_GPKG_LAYER = "municipal_subdivisions"
DEFAULT_TURNOUT_CSV = MUN_DATA_DIR / "municipal_combined.csv"


# -------------------------------------------------------------------
# Loaders
# -------------------------------------------------------------------
def load_municipal_geometries(
    path: str | Path = DEFAULT_GPKG_PATH,
    layer: str = DEFAULT_GPKG_LAYER,
) -> gpd.GeoDataFrame:
    """
    Load combined municipal geometries for Toronto.

    Expected schema:
      - Year (int)
      - Ward (int)
      - Sub (int)
      - geometry (Polygon/MultiPolygon)
    """
    gdf = gpd.read_file(path, layer=layer)

    # Normalize dtypes
    for col in ["Year", "Ward", "Sub"]:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

    gdf = gdf.dropna(subset=["Year", "Ward", "Sub"])
    gdf["Year"] = gdf["Year"].astype(int)
    gdf["Ward"] = gdf["Ward"].astype(int)
    gdf["Sub"] = gdf["Sub"].astype(int)

    # Make sure CRS is WGS84 for web mapping
    if gdf.crs is not None and gdf.crs.to_string().upper() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)

    return gdf


def load_municipal_turnout(
    path: str | Path = DEFAULT_TURNOUT_CSV,
) -> pd.DataFrame:
    """
    Load municipal voter turnout CSV.

    Expected schema (after cleaning script):
      - Year
      - Ward
      - Sub
      - PctVoted
    """
    df = pd.read_csv(path)

    # Normalize dtypes
    for col in ["Year", "Ward", "Sub"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Year", "Ward", "Sub"])
    df["Year"] = df["Year"].astype(int)
    df["Ward"] = df["Ward"].astype(int)
    df["Sub"] = df["Sub"].astype(int)

    if "PctVoted" in df.columns:
        df["PctVoted"] = pd.to_numeric(df["PctVoted"], errors="coerce")

    return df


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def get_available_years(
    turnout_df: Optional[pd.DataFrame] = None,
    gdf: Optional[gpd.GeoDataFrame] = None,
) -> list[int]:
    """
    Get sorted list of municipal election years present in the data.
    Priority: turnout_df → gdf.
    """
    if turnout_df is not None and "Year" in turnout_df.columns:
        years = sorted(turnout_df["Year"].dropna().astype(int).unique())
    elif gdf is not None and "Year" in gdf.columns:
        years = sorted(gdf["Year"].dropna().astype(int).unique())
    else:
        years = []

    return list(years)


def prepare_municipal_year_gdf(
    year: int,
    geom_gdf: gpd.GeoDataFrame,
    turnout_df: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """
    For a given year, join geometry with turnout.

    Returns a GeoDataFrame with:
      - Year, Ward, Sub
      - PctVoted
      - geometry
    """
    # Filter by year
    g_year = geom_gdf[geom_gdf["Year"] == int(year)].copy()
    t_year = turnout_df[turnout_df["Year"] == int(year)].copy()

    # Make sure keys are aligned
    for col in ["Ward", "Sub"]:
        g_year[col] = pd.to_numeric(g_year[col], errors="coerce")
        t_year[col] = pd.to_numeric(t_year[col], errors="coerce")

    g_year = g_year.dropna(subset=["Ward", "Sub"])
    t_year = t_year.dropna(subset=["Ward", "Sub"])

    g_year["Ward"] = g_year["Ward"].astype(int)
    g_year["Sub"] = g_year["Sub"].astype(int)
    t_year["Ward"] = t_year["Ward"].astype(int)
    t_year["Sub"] = t_year["Sub"].astype(int)

    merged = g_year.merge(
        t_year[["Year", "Ward", "Sub", "PctVoted"]],
        on=["Year", "Ward", "Sub"],
        how="left",
        validate="1:1",
    )

    return merged


def compute_turnout_summary(df_year: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute basic turnout summary for a year.
    """
    if "PctVoted" not in df_year.columns or df_year["PctVoted"].dropna().empty:
        return {
            "n": len(df_year),
            "mean": None,
            "min": None,
            "max": None,
        }

    series = df_year["PctVoted"].dropna()
    return {
        "n": int(len(series)),
        "mean": float(series.mean()),
        "min": float(series.min()),
        "max": float(series.max()),
    }
