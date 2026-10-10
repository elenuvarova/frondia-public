CITIES = {
    "paris": {
        "display_name": "Paris, France",
        "crs": 2154,                    # RGF93 / Lambert-93, metric (metres)
        "osm_place": "Paris, France",
        "admin_level": "8",
        "walk_radius_m": 500,           # planning threshold: 5-min walk ~80 m/min
        "candidate_min_dist_m": 300,    # min distance between two new assets
    },
    "antwerp": {
        "display_name": "Antwerpen, Belgium",
        "crs": 31370,                   # Belge 1972 / Belgian Lambert 72
        "osm_place": "Antwerp, Belgium",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
    "brussels": {
        "display_name": "Brussels-Capital Region, Belgium",
        "crs": 31370,                   # Belge 1972 / Belgian Lambert 72
        # Nominatim resolves "Brussels-Capital Region, Belgium" to a degenerate
        # polygon and "Brussels, Belgium" to the City of Brussels commune only
        # (34 km² instead of 162). This name returns all 19 communes.
        "osm_place": "Brussels-Capital Region",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
    # added 26 Sep 2026 for Frondia (map_project): the municipality of Ghent (NIS 44021)
    "ghent": {
        "display_name": "Gent, Belgium",
        "crs": 31370,                   # Belge 1972 / Belgian Lambert 72
        "osm_place": "Gent, Belgium",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
    # added 26 Sep 2026 for Frondia (map_project): the municipality of Liège (NIS 62063). Nominatim
    # returns the municipality itself: relation 1681788, 68.5 km² (Statbel's 184 sectors: 68.7 km²)
    "liege": {
        "display_name": "Liège, Belgium",
        "crs": 31370,                   # Belge 1972 / Belgian Lambert 72
        "osm_place": "Liège, Belgium",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
    # added 26 Sep 2026 for Frondia (map_project): the municipality of Charleroi (NIS 52011). Nominatim
    # returns the municipality itself: relation 2113725, 102.9 km² (Statbel's 291 sectors: 102.9 km²)
    "charleroi": {
        "display_name": "Charleroi, Belgium",
        "crs": 31370,                   # Belge 1972 / Belgian Lambert 72
        "osm_place": "Charleroi, Belgium",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
    "london": {
        "display_name": "London, United Kingdom",
        "crs": 27700,                   # OSGB36 / British National Grid
        "osm_place": "London, England",
        "admin_level": "8",
        "walk_radius_m": 500,
        "candidate_min_dist_m": 300,
    },
}

ASSETS = {
    "toilets": {
        "osm_tags": {"amenity": "toilets"},
        "demand_pois": {
            "leisure":          ["park"],
            "amenity":          ["school", "marketplace"],
            "public_transport": ["platform"],
            "railway":          ["station"],
        },
    },
    "benches": {
        "osm_tags": {"amenity": "bench"},
        "demand_pois": {
            "amenity":   ["pharmacy", "clinic", "hospital"],
            "leisure":   ["park"],
            "public_transport": ["platform"],
        },
    },
    "waste_bins": {
        "osm_tags": {"amenity": "waste_basket"},
        "demand_pois": {
            "leisure":          ["park"],
            "amenity":          ["marketplace", "restaurant", "fast_food"],
            "public_transport": ["platform"],
            "railway":          ["station"],
        },
    },
    "drinking_water": {
        "osm_tags": {"amenity": "drinking_water"},
        "demand_pois": {
            "leisure":          ["park", "sports_centre", "pitch"],
            "amenity":          ["school", "marketplace"],
            "public_transport": ["platform"],
        },
    },
    "fitness_stations": {
        "osm_tags": {"leisure": "fitness_station"},
        "demand_pois": {
            "leisure":   ["park"],
            "amenity":   ["hospital", "clinic", "pharmacy"],
        },
    },
    "bike_parking": {
        "osm_tags": {"amenity": "bicycle_parking"},
        "demand_pois": {
            "railway":          ["station"],
            "public_transport": ["platform"],
            "amenity":          ["school", "marketplace"],
            "leisure":          ["park"],
        },
    },
    "defibrillators": {
        "osm_tags": {"emergency": "defibrillator"},
        "demand_pois": {
            "amenity":          ["community_centre", "school", "marketplace"],
            "leisure":          ["sports_centre"],
            "railway":          ["station"],
            "public_transport": ["platform"],
        },
    },
    "dog_areas": {
        "osm_tags": {"leisure": "dog_park"},
        "demand_pois": {
            "leisure":   ["park"],
            "amenity":   ["veterinary"],
            "shop":      ["pet"],
        },
    },
    "playgrounds": {
        "osm_tags": {"leisure": "playground"},
        "demand_pois": {
            "amenity":   ["school", "kindergarten", "childcare", "community_centre"],
            "leisure":   ["park"],
        },
    },
    "shelters": {
        "osm_tags": {"amenity": "shelter"},
        "demand_pois": {
            "public_transport": ["platform"],
            "railway":          ["station"],
            "amenity":          ["marketplace", "school"],
        },
    },
    "recycling": {
        "osm_tags": {"amenity": "recycling"},
        "demand_pois": {
            "shop":      ["supermarket", "convenience"],
            "amenity":   ["marketplace", "school"],
            "leisure":   ["park"],
        },
    },
    "bicycle_repair": {
        "osm_tags": {"amenity": "bicycle_repair_station"},
        "demand_pois": {
            "railway":          ["station"],
            "public_transport": ["platform"],
            "amenity":          ["bicycle_parking", "school"],
            "shop":             ["bicycle"],
        },
    },
    "public_bookcases": {
        "osm_tags": {"amenity": "public_bookcase"},
        "demand_pois": {
            "amenity":   ["library", "school", "community_centre", "cafe"],
            "leisure":   ["park"],
        },
    },
    "picnic_tables": {
        "osm_tags": {"leisure": "picnic_table"},
        "demand_pois": {
            "leisure":   ["park", "garden", "nature_reserve"],
            "amenity":   ["school"],
        },
    },
}

# H3 resolution for analysis grid
H3_RES = 9          # edge ~201 m, area ~0.11 km² — good ~250m city grid feel

# Output dir (relative to repo root)
OUTPUT_BASE = "frontend/public/data"
