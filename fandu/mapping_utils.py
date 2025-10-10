"""


"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import mapping
from typing import Tuple, Optional

def get_boundary_map(
    boundary_path: Path,
    boundary_name: Optional[str] = None,
    show_boundary: bool = True
) -> tuple[folium.Map, folium.FeatureGroup, gpd.GeoDataFrame]:
    """
    Load and validate a boundary GeoJSON file, optionally filter it by name,
    and return both a Folium map and the filtered GeoDataFrame.

    Parameters
    ----------
    boundary_path : Path
        Path to a .geojson boundary file.
    boundary_name : str, optional
        If provided, filters the GeoDataFrame where a column 'name' or
        'Name' matches this value.
    show_boundary : bool, optional
        If True, overlay the boundary geometry on the map (default=True).

    Returns
    -------
    Tuple[folium.Map, gpd.GeoDataFrame]
        The Folium map centered on the boundary and the boundary GeoDataFrame.
    """

    # --- Validate path ---
    if boundary_path.suffix.lower() != ".geojson":
        raise ValueError(f"Expected .geojson file, got {boundary_path.suffix}")

    if not boundary_path.is_file():
        raise FileNotFoundError(f"File not found: {boundary_path}")

    # --- Load and project ---
    boundaries: gpd.GeoDataFrame = gpd.read_file(boundary_path)
    border_shape: gpd.GeoDataFrame = boundaries.to_crs(epsg=4326)

    # --- Optional filtering by name ---
    if boundary_name is not None:
        # Try to find a likely column to match on
        name_cols = [c for c in border_shape.columns if c.lower() in {"name", "boundary", "label"}]
        if not name_cols:
            raise ValueError(
                f"Cannot filter by name: no column like 'name' or 'boundary' found in {boundary_path.name}"
            )
        name_col = name_cols[0]
        border_shape = border_shape[border_shape[name_col].astype(str) == str(boundary_name)]
        if border_shape.empty:
            raise ValueError(f"No features found in '{boundary_path.name}' where {name_col} == '{boundary_name}'")

    # --- Sanitize columns for Folium (timestamps → strings) ---
    border_shape = border_shape.copy()
    for col in border_shape.columns:
        if pd.api.types.is_datetime64_any_dtype(border_shape[col]):
            border_shape[col] = border_shape[col].astype(str)

    # --- Compute bounds & center ---
    minx, miny, maxx, maxy = border_shape.total_bounds
    bounds: list[list[float]] = [[miny, minx], [maxy, maxx]]
    center: list[float] = [(miny + maxy) / 2, (minx + maxx) / 2]

    # --- Build Folium map ---
    m: folium.Map = folium.Map(location=center, zoom_start=15, tiles="cartodbpositron")
    m.fit_bounds(bounds)

    non_geom_cols = [c for c in border_shape.columns if c != border_shape.geometry.name]
    tooltip_field = non_geom_cols[0] if non_geom_cols else None

    boundary_layer = folium.FeatureGroup(
        name=f"Boundary: {boundary_name or boundary_path.stem}",
        show=show_boundary  # or False if you want it unchecked by default
    )

    folium.GeoJson(
        border_shape,
        name=f"Boundary: {boundary_name or boundary_path.stem}",
        tooltip=tooltip_field,
        style_function=lambda feature: {
            "color": "black",     # border color
            "weight": 2,          # line thickness
            "fill": False,        # no fill
            "fillColor": "none",
            "opacity": 1.0,
        },
        highlight_function=lambda feature: {
            "weight": 4,
            "color": "gray",
        },
    ).add_to( boundary_layer )

    boundary_layer.add_to( m )
    
    return m, boundary_layer, border_shape
