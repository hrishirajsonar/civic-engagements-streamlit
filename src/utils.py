import re
from pathlib import Path

import pandas as pd
import geopandas as gpd
import numpy as np
import streamlit as st

# ----------------------------------------------------
# Helpers
# ----------------------------------------------------
def normalize_names(series: pd.Series) -> pd.Series:
    """Lowercase, strip whitespace, collapse spaces, drop NA safely."""
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )


def find_col_by_keywords(cols, keywords):
    """Return the first column name containing any of the keywords."""
    if cols is None:
        return None

    for c in cols:
        low = str(c).strip().lower()
        for kw in keywords:
            if kw.lower() in low:
                return c
    return None


def detect_join_key(gdf: gpd.GeoDataFrame, df: pd.DataFrame):
    """Detect a shared join key between shapefile + CSV."""
    possible = ["riding_id", "riding_name", "name"]

    # exact name match
    for key in possible:
        if key in gdf.columns and key in df.columns:
            return key

    # case-insensitive match
    gcols_lower = {c.lower(): c for c in gdf.columns}
    dcols_lower = {c.lower(): c for c in df.columns}

    for key in possible:
        if key in gcols_lower and key in dcols_lower:
            return (gcols_lower[key], dcols_lower[key])

    return None


def _safe_str_intlike(x):
    """Convert ID-like values safely to string without trailing .0."""
    if pd.isna(x):
        return ""

    if isinstance(x, (int, np.integer)):
        return str(int(x))

    try:
        s = str(x).strip()
        s = re.sub(r"\.0+$", "", s)
        return s
    except Exception:
        return str(x)

# ----------------------------------------------------
# Loaders (CLEANED)
# ----------------------------------------------------
@st.cache_data(ttl=3600)
def load_gpkg(path: str = "data/combined_toronto_ridings.gpkg"):
    """Load combined GPKG of ridings with defensive normalization."""
    gdf = gpd.read_file(path)

    # Ensure CRS
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        try:
            gdf = gdf.to_crs(epsg=4326)
        except Exception:
            print("Warning: CRS conversion failed; using original CRS.")

    # Normalize columns
    gdf.columns = gdf.columns.str.strip().str.lower()

    # Normalize year naming
    if "election_year" in gdf.columns and "year" not in gdf.columns:
        gdf = gdf.rename(columns={"election_year": "year"})

    # riding_num fallback reconstruction
    if "riding_num" not in gdf.columns:
        id_candidates = [
            "riding_num", "feduid", "fed_id", "fednum",
            "fed_num", "ed_id", "ed_num"
        ]
        id_col = next((c for c in id_candidates if c in gdf.columns), None)

        if id_col:
            gdf["riding_num"] = (
                gdf[id_col].astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
            )
        else:
            gdf["riding_num"] = None

    # riding_name mapping
    if "riding_name" not in gdf.columns:
        name_candidates = [
            "riding_name", "fedname", "enname", "fedename",
            "ed_namee", "ed_name_en", "ed_name_e", "ename"
        ]
        name_col = next((c for c in name_candidates if c in gdf.columns), None)
        gdf["riding_name"] = gdf[name_col] if name_col else None

    # Ensure year numeric
    if "year" in gdf.columns:
        gdf["year"] = pd.to_numeric(gdf["year"], errors="coerce").astype("Int64")

    # Composite geo_key
    def _safe_str(x):
        if pd.isna(x):
            return ""
        try:
            return str(int(x))
        except Exception:
            return re.sub(r"\.0+$", "", str(x)).strip()

    gdf["geo_key"] = gdf.apply(
        lambda r: f"{_safe_str(r.get('year', ''))}__{str(r.get('riding_num', '')).strip()}",
        axis=1,
    )

    return gdf


@st.cache_data(ttl=3600)
def load_federal_csv(path: str = "data/federal_combined.csv"):
    """Load and normalize federal CSV with fuzzy header matching."""
    try:
        df = pd.read_csv(path, dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, encoding="latin1")

    raw_cols = list(df.columns)
    col_map = {}

    # Detect important columns
    c = find_col_by_keywords(raw_cols, ["year"])
    if c: col_map[c] = "year"

    c = find_col_by_keywords(raw_cols, ["province", "prov"])
    if c: col_map[c] = "province"

    c = find_col_by_keywords(
        raw_cols,
        ["electoral district name", "riding", "circonscription", "district"]
    )
    if c: col_map[c] = "riding_name"

    c = find_col_by_keywords(
        raw_cols,
        ["electoral district number", "num", "numero", "number"]
    )
    if c: col_map[c] = "riding_num"

    # Population / electors
    c = find_col_by_keywords(raw_cols, ["population"])
    if c: col_map[c] = "population"

    c = find_col_by_keywords(raw_cols, ["electors", "électeurs"])
    if c: col_map[c] = "electors"

    # Turnout
    c = find_col_by_keywords(raw_cols, ["voter turnout", "participation"])
    if c: col_map[c] = "voter_participation_pct"

    # Winner
    c = find_col_by_keywords(raw_cols, ["elected candidate"])
    if c: col_map[c] = "elected_candidate"

    # Apply mapping
    df = df.rename(columns=col_map)

    # Clean riding_name
    if "riding_name" in df.columns:
        df["riding_name"] = normalize_names(df["riding_name"])

    # Clean riding_num
    if "riding_num" in df.columns:
        df["riding_num"] = (
            df["riding_num"].astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
        )
    else:
        # emergency fallback
        if "riding_name" in df.columns:
            df["riding_num"] = normalize_names(df["riding_name"]).str.replace(r"\s+", "_", regex=True)
        else:
            print("Warning: No riding_num or riding_name found in CSV; joins may fail.")

    # Ensure year numeric
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Clean voter participation numeric
    if "voter_participation_pct" in df.columns:
        df["voter_participation_pct"] = (
            df["voter_participation_pct"]
            .astype(str)
            .str.replace("%", "")
            .str.replace(",", ".")
            .str.extract(r"([0-9]+(?:\.[0-9]+)?)")[0]
        )
        df["voter_participation_pct"] = pd.to_numeric(
            df["voter_participation_pct"], errors="coerce"
        )

    # Composite geo_key
    df["riding_num"] = df["riding_num"].replace({"nan": None, "None": None, "none": None})
    df["geo_key"] = df.apply(
        lambda r: f"{_safe_str_intlike(r.get('year', ''))}__{str(r.get('riding_num', '')).strip()}",
        axis=1,
    )

    return df

# ----------------------------------------------------
# Data preparation (CLEAN)
# ----------------------------------------------------
def prepare_map_df(
    gdf_all: gpd.GeoDataFrame,
    df_fed: pd.DataFrame,
    year: int,
    join_key_hint=None,
    simplify_tol=0.00008,
):
    """Prepare a clean GeoDataFrame for mapping."""
    # Normalize year naming
    if "election_year" in gdf_all.columns and "year" not in gdf_all.columns:
        gdf_all = gdf_all.rename(columns={"election_year": "year"})

    if "year" not in gdf_all.columns:
        raise ValueError("GPKG missing 'year' column.")

    # Filter by year
    view_gdf = gdf_all[gdf_all["year"] == int(year)].copy()
    if view_gdf.empty:
        return view_gdf

    # --------------------------------------------
    # Preferred join: geo_key
    # --------------------------------------------
    if "geo_key" in view_gdf.columns and "geo_key" in df_fed.columns:
        view_gdf = view_gdf[view_gdf["geo_key"].astype(str).str.len() > 0].copy()

        if not view_gdf.empty:
            df_year = df_fed[df_fed["year"] == int(year)].copy()

            # dissolve duplicates
            if view_gdf["geo_key"].duplicated(keep=False).any():
                try:
                    tmp = view_gdf[["geo_key", "geometry", "year"]].copy()
                    view_gdf = (
                        gpd.GeoDataFrame(tmp, geometry="geometry", crs=view_gdf.crs)
                        .dissolve(by="geo_key", as_index=False)
                    )
                except Exception:
                    grouped = []
                    for key_val, grp in view_gdf.groupby("geo_key"):
                        geom = grp.unary_union
                        row = grp.iloc[0].to_dict()
                        row["geometry"] = geom
                        row["geo_key"] = key_val
                        grouped.append(row)
                    view_gdf = gpd.GeoDataFrame(grouped, crs=gdf_all.crs)

            merged = view_gdf.merge(df_year, on="geo_key", how="left")

            # simplify
            try:
                merged["geometry"] = merged["geometry"].simplify(
                    tolerance=simplify_tol, preserve_topology=True
                )
            except Exception:
                pass

            return merged

    # --------------------------------------------
    # Fallback join: riding_id / riding_num / riding_name
    # --------------------------------------------
    preferred_keys = []
    if join_key_hint:
        preferred_keys.append(join_key_hint)

    preferred_keys.extend(["riding_id", "riding_name", "riding_num", "name"])

    detected_join = None
    for key in preferred_keys:
        if key in view_gdf.columns and key in df_fed.columns:
            detected_join = key
            break

    if detected_join is None:
        detected = detect_join_key(view_gdf, df_fed)
        if isinstance(detected, tuple):
            gkey, dkey = detected
            detected_join = gkey
            if dkey in df_fed.columns and gkey != dkey:
                df_fed = df_fed.rename(columns={dkey: gkey})
        else:
            detected_join = detected

    if detected_join is None:
        raise ValueError("No valid join key found.")

    join_key = detected_join

    # Normalize join keys
    if "name" in join_key.lower():
        view_gdf[join_key] = normalize_names(view_gdf[join_key].astype(str))
        df_fed[join_key] = normalize_names(df_fed[join_key].astype(str))
    else:
        view_gdf[join_key] = view_gdf[join_key].astype(str).str.strip()
        df_fed[join_key] = df_fed[join_key].astype(str).str.strip()

    # Drop missing join keys
    missing_mask = (
        view_gdf[join_key].isna()
        | (view_gdf[join_key].astype(str).str.len() == 0)
        | (view_gdf[join_key].astype(str).str.lower() == "none")
    )
    view_gdf = view_gdf.loc[~missing_mask].copy()
    if view_gdf.empty:
        return view_gdf

    # Remove duplicate polygons
    if view_gdf[join_key].duplicated(keep=False).any():
        try:
            cols = [join_key, "geometry"]
            if "year" in view_gdf.columns:
                cols.append("year")

            tmp = view_gdf[cols].copy()
            view_gdf = (
                gpd.GeoDataFrame(tmp, geometry="geometry", crs=view_gdf.crs)
                .dissolve(by=join_key, as_index=False)
            )

            if "year" not in view_gdf.columns:
                view_gdf["year"] = int(year)

        except Exception:
            grouped = []
            for key_val, grp in view_gdf.groupby(join_key):
                geom = grp.unary_union
                row = grp.iloc[0].to_dict()
                row["geometry"] = geom
                row[join_key] = key_val
                grouped.append(row)
            view_gdf = gpd.GeoDataFrame(grouped, crs=gdf_all.crs)

    # Filter CSV
    df_year = df_fed[df_fed["year"] == int(year)].copy()

    # Merge
    merged = view_gdf.merge(df_year, on=join_key, how="left")
    if merged is None or merged.empty:
        return merged

    # --------------------------------------------
    # Compute delta turnout (prev election)
    # --------------------------------------------
    if "voter_participation_pct" in df_fed.columns:
        if "riding_id" in df_fed.columns:
            df_sorted = df_fed.sort_values(["riding_id", "year"])
            df_sorted["prev_participation"] = df_sorted.groupby("riding_id")[
                "voter_participation_pct"
            ].shift(1)

            prev = df_sorted[df_sorted["year"] == int(year)][
                ["riding_id", "prev_participation"]
            ]

            if "riding_id" in merged.columns:
                merged = merged.merge(prev, on="riding_id", how="left")
                merged["delta_pct"] = (
                    merged["voter_participation_pct"]
                    - merged["prev_participation"]
                )
        else:
            # fallback: by name
            df_sorted = df_fed.sort_values(["riding_name", "year"])
            df_sorted["prev_participation"] = df_sorted.groupby("riding_name")[
                "voter_participation_pct"
            ].shift(1)

            prev = df_sorted[df_sorted["year"] == int(year)][
                ["riding_name", "prev_participation"]
            ]

            if "riding_name" in merged.columns:
                merged = merged.merge(prev, on="riding_name", how="left")
                merged["delta_pct"] = (
                    merged["voter_participation_pct"]
                    - merged["prev_participation"]
                )

    # simplify
    try:
        merged["geometry"] = merged["geometry"].simplify(
            tolerance=simplify_tol, preserve_topology=True
        )
    except Exception:
        pass

    return merged