import geopandas as gpd

gdf = gpd.read_file(
    r"E:\bdat2\project\fed\federal_electoral_districts_boundaries\combined_toronto_ridings.gpkg", 
    layer="toronto_ridings_all_years"
)

print(gdf[gdf['year']==2006].head())
print(gdf.columns)