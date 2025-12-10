import geopandas as gpd
import pandas as pd
import os
from pathlib import Path

# Step 1: Define the root directory containing your year folders
root_dir = Path('E:/bdat2/project/fed/federal_electoral_districts_boundaries/') 
# Step 2: List to hold individual GeoDataFrames
gdfs = []

# Step 3: Loop over each year folder
for year_folder in root_dir.iterdir():
    if year_folder.is_dir():
        # Extract year from folder name (assume it's the folder name, e.g., '2000')
        try:
            election_year = int(year_folder.name)
        except ValueError:
            print(f"Skipping folder '{year_folder.name}' - not a valid year.")
            continue
        
        # Find the .shp file in the folder
        shp_file = list(year_folder.glob('*.shp'))
        if not shp_file:
            print(f"No .shp file found in '{year_folder.name}'.")
            continue
        shp_path = shp_file[0]  # Take the first (and only) .shp
        
        # Read the shapefile into a GeoDataFrame
        gdf = gpd.read_file(shp_path)
        
        # Add the election_year column
        #gdf['election_year'] = election_year
        gdf['year'] = election_year
        
        # Reproject to a common CRS (choose one)
        common_crs = 'EPSG:3347'  # Matches your Lambert_Conformal_Conic
        # common_crs = 'EPSG:4326'  # Alternative: For web maps (uncomment if needed)
        gdf = gdf.to_crs(common_crs)
        print(f"Reprojected {election_year} to: {gdf.crs}")  # Confirm
        
        gdfs.append(gdf)
        print(f"Loaded {len(gdf)} features for {election_year} from {shp_path.name}")

# Step 4: Stack (concatenate) all GeoDataFrames into one
if gdfs:
    combined_gdf = pd.concat(gdfs, ignore_index=True)
    
    # Optional: Sort by year for consistency
    combined_gdf = combined_gdf.sort_values('year').reset_index(drop=True)
    
    # Display basic info
    print(f"\nCombined GeoDataFrame shape: {combined_gdf.shape}")
    print(f"Columns: {list(combined_gdf.columns)}")
    print(f"CRS: {combined_gdf.crs}")
    print(f"Years covered: {sorted(combined_gdf['year'].unique())}")
    
    # Save the combined file (optional)
    # combined_gdf.to_file('/path/to/combined_toronto_ridings.shp')
    
    # Now you can work with combined_gdf (e.g., plot, filter by year)
    # Export to GeoPackage (recommended over .shp)
    output_path = 'E:/bdat2/project/fed/federal_electoral_districts_boundaries/combined_toronto_ridings.gpkg'
    combined_gdf.to_file(output_path, layer='toronto_ridings_all_years', driver='GPKG')

    print(f"Exported to GeoPackage: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")  # Optional: Check size
else:
    print("No valid GeoDataFrames to combine.")

