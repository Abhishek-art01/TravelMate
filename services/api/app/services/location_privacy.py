from __future__ import annotations

import hashlib
import math


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in km)."""
    earth_radius_km = 6371.0

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c


def approximate_coordinates(
    lat: float,
    lon: float,
    precision_mode: str = "approximate",
    fuzz_radius_km: float = 5.0,
) -> tuple[float, float]:
    """
    Transform exact coordinates into privacy-safe approximate coordinates.
    Never exposes raw high-precision coordinates for non-exact sharing modes.
    Uses deterministic spatial hashing so coordinates do not jump erratically on repeated queries.
    """
    if precision_mode == "exact":
        return round(lat, 6), round(lon, 6)

    # Convert fuzz radius into rough degree grid (~111 km per degree of latitude)
    grid_deg = max(0.02, fuzz_radius_km / 111.0)

    # Snap to center of nearest grid cell
    grid_lat = round(lat / grid_deg) * grid_deg
    grid_lon = round(lon / grid_deg) * grid_deg

    # Deterministic pseudo-random offset within 35% of grid cell using SHA256 of grid cell
    seed = f"{round(grid_lat, 2)}:{round(grid_lon, 2)}".encode()
    digest = hashlib.sha256(seed).hexdigest()
    offset_lat = ((int(digest[:8], 16) / 0xFFFFFFFF) - 0.5) * (grid_deg * 0.5)
    offset_lon = ((int(digest[8:16], 16) / 0xFFFFFFFF) - 0.5) * (grid_deg * 0.5)

    approx_lat = round(grid_lat + offset_lat, 4)
    approx_lon = round(grid_lon + offset_lon, 4)

    # Clamp to geographical boundaries
    approx_lat = max(-90.0, min(90.0, approx_lat))
    approx_lon = max(-180.0, min(180.0, approx_lon))

    return approx_lat, approx_lon


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Calculate min_lat, max_lat, min_lon, max_lon bounding box for spatial search."""
    lat_delta = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    lon_delta = radius_km / (111.0 * max(0.01, abs(cos_lat)))

    min_lat = max(-90.0, lat - lat_delta)
    max_lat = min(90.0, lat + lat_delta)
    min_lon = max(-180.0, lon - lon_delta)
    max_lon = min(180.0, lon + lon_delta)

    return min_lat, max_lat, min_lon, max_lon
