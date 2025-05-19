"""
Geospatial Utilities for Fandu
"""
import os
import re

import zipfile
import geopandas as gpd
import matplotlib.pyplot as plt

from datetime import datetime
from typing import Optional


def get_newest_feature_file(path: str, feature: str) -> Optional[str]:
    """
    Finds the newest .geojson file matching the pattern 'feature-YYYY-MM-DD*.geojson' in the given path.
    Returns the absolute file path, or None if no matching files are found.

    Parameters:
        path (str): Relative directory path to search in.
        feature (str): Feature name prefix, e.g., 'Addresses' or 'Parcels'.

    Returns:
        Optional[str]: Absolute file path of the newest feature file, or None.
    """
    pattern = re.compile(rf"^{re.escape(feature)}-(\d{{4}}-\d{{2}}-\d{{2}}).*\.geojson$", re.IGNORECASE)

    newest_file = None
    newest_date = None

    for filename in os.listdir(path):
        match = pattern.match(filename)
        if match:
            try:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                if newest_date is None or file_date > newest_date:
                    newest_date = file_date
                    newest_file = filename
            except ValueError:
                continue

    if newest_file:
        return os.path.abspath(os.path.join(path, newest_file))
    return None

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

def rva_geohub_url( feature ):
    """ API URL for RVA geohub"""
    return f"https://services1.arcgis.com/k3vhq11XkBNeeOfM/arcgis/rest/services/{feature}/FeatureServer/0/query?where=1=1&outFields=*&f=geojson"


