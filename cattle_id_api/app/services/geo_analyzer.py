# Geospatial logic goes here

import osmnx as ox
from shapely.geometry import Point, Polygon
from shapely.errors import TopologicalError
import logging

logger = logging.getLogger(__name__)

class GeoAnalyzer:
    def __init__(self):
        # Configure osmnx to be useful for API responses
        ox.settings.use_cache = True
        ox.settings.log_console = False

    def create_polygon(self, coordinates):
        """
        Converts a list of [lat, lon] coordinates into a Shapely Polygon.
        Expects coordinates in format: [[lat, lon], [lat, lon], ...]
        """
        # Shapely expects (x, y) which corresponds to (longitude, latitude)
        # We need to swap them if your DB stores [lat, lon]
        swapped_coords = [(lon, lat) for lat, lon in coordinates]
        return Polygon(swapped_coords)

    def check_fence_status(self, cattle_lat, cattle_lon, polygon_obj):
        """
        Returns True if cattle is INSIDE the polygon, False if OUTSIDE.
        """
        point = Point(cattle_lon, cattle_lat) # Note order: Lon, Lat
        return polygon_obj.contains(point)

    def scan_for_features(self, polygon_obj):
        """
        Uses OSMnx to find features (houses, trees, water) INSIDE the polygon.
        """
        features_found = []
        
        # Define what OSM tags we are looking for
        # You can add more tags here based on what you want to detect
        tags = {
            'building': True,  # All buildings
            'natural': ['tree', 'water', 'wood'], # Trees and water
            'landuse': ['forest', 'residential', 'farmland'] # Areas
        }

        try:
            # 1. Fetch data from OpenStreetMap for this specific polygon area
            gdf = ox.features_from_polygon(polygon_obj, tags)

            # 2. Process the results
            if not gdf.empty:
                # We iterate through the results to format them for the API
                for index, row in gdf.iterrows():
                    
                    # Determine the type of object
                    obj_type = "unknown"
                    if 'building' in row and isinstance(row['building'], str):
                        obj_type = "building"
                    elif 'natural' in row and isinstance(row['natural'], str):
                        obj_type = row['natural'] # e.g., 'tree'
                    elif 'landuse' in row and isinstance(row['landuse'], str):
                        obj_type = row['landuse']

                    # Get location (centroid) of the feature
                    # geometry.centroid returns a Point(lon, lat)
                    centroid = row.geometry.centroid
                    
                    features_found.append({
                        "type": obj_type,
                        "location": {
                            "lat": centroid.y,
                            "lon": centroid.x
                        },
                        "name": row.get('name', 'Unnamed Object') # Get name if available
                    })
                    
        except Exception as e:
            # If OSM returns no data or fails, we just log it and return empty list
            # We don't want to crash the whole app just because OSM failed.
            logger.warning(f"OSM lookup failed or found nothing: {e}")

        return features_found

    def analyze(self, cattle_lat, cattle_lon, polygon_coords):
        """
        Main function to orchestrate the analysis.
        """
        try:
            # 1. Prepare Geometry
            user_polygon = self.create_polygon(polygon_coords)
            
            # 2. Check Fence (Is cattle safe?)
            is_inside = self.check_fence_status(cattle_lat, cattle_lon, user_polygon)
            
            # 3. Scan Area (What is around?)
            # We scan the area inside the polygon as requested
            nearby_objects = self.scan_for_features(user_polygon)

            return {
                "status": "success",
                "is_safe": is_inside,
                "cattle_location": {"lat": cattle_lat, "lon": cattle_lon},
                "detected_objects": nearby_objects
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"status": "error", "message": str(e)}

# Create a singleton instance
analyzer = GeoAnalyzer()