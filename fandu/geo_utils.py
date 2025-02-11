"""
Geospatial Utilities for Fandu
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import zipfile
import os

def load_shapefile_from_zip(zip_path="../data/neighborhoods-shp.zip" ):
    """Extracts, loads a shapefile from a ZIP archive."""
    extract_dir = "shapefile_temp"
    os.makedirs(extract_dir, exist_ok=True)

    # Extract the ZIP file
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    # Locate the .shp file
    shp_file = None
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".shp"):
                shp_file = os.path.join(root, file)
                break

    if not shp_file:
        raise FileNotFoundError("No shapefile (.shp) found in the ZIP archive.")

    # Load shapefile
    gdf = gpd.read_file(shp_file)
    return gdf

