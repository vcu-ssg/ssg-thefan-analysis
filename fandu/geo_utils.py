"""
Geospatial Utilities for Fandu
"""
import os
import re

from pathlib import Path

import zipfile
import geopandas as gpd
import matplotlib.pyplot as plt

from datetime import datetime
from typing import Optional
from loguru import logger


def get_newest_path(path: Path, feature: str, ext: str = ".geojson") -> Optional[Path]:
    """
    Finds the newest file matching the pattern 'feature-YYYY-MM-DD*.ext' in the given path.
    Returns the absolute Path object, or None if no matching files are found.

    Parameters
    ----------
    path : Path
        Directory path to search in.
    feature : str
        Feature name prefix, e.g., 'Addresses' or 'Parcels'.
    ext : str, optional
        File extension to match (default='.geojson').

    Returns
    -------
    Optional[Path]
        Absolute Path of the newest feature file, or None if not found.
    """

    pattern = re.compile(
        rf"^{re.escape(feature)}-(\d{{4}}-\d{{2}}-\d{{2}}).*{re.escape(ext)}$",
        re.IGNORECASE
    )

    newest_file: Optional[Path] = None
    newest_date: Optional[datetime] = None

    for file in path.iterdir():  # iterdir() yields Path objects
        if not file.is_file():
            continue

        match = pattern.match(file.name)
        if match:
            try:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                if newest_date is None or file_date > newest_date:
                    newest_date = file_date
                    newest_file = file
            except ValueError:
                continue

    if newest_file:
        return newest_file.resolve()  # returns absolute Path
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


