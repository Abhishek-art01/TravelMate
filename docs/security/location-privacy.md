# Location Privacy & Security Specification

TravelMate enforces strict location privacy controls to protect travelers against stalking, unauthorized location profiling, and physical safety risks.

```text
GPS / Browser Geolocation
           │
           ▼
TravelMate API (/api/v1/me/location)
           │
           ▼
LocationPrivacyService
           ├── Consent & Purpose Validation
           ├── Coordinate Snapping (Grid Snapping ~5km)
           └── Privacy Transformation
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
Internal Storage        Public Discovery API
(exact coords encrypted) (snapped approx coords only)
```

---

## 1. Core Principles

1. **Server-Side Enforcement**:
   - Location precision transformation is strictly enforced in the backend (`app.services.location_privacy`). Frontend clients are never trusted to obfuscate or truncate coordinates.
2. **Never Expose Exact Coordinates by Default**:
   - Public APIs (`/api/v1/trips`, `/api/v1/destinations`) return only destination center coordinates or obfuscated user centroids. Raw GPS coordinates are never returned across user boundaries.
3. **Domain Separation**:
   - **Public Catalog Data** (Destinations, Cities, Landmarks) is public geospatial data.
   - **Personal Location Data** (User current location, proximity) is sensitive personal data governed by GDPR and DPDP Act regulations.

---

## 2. Server-Side Coordinate Approximation Algorithm

### Defense Against Averaging & Trilateration
A common security flaw in privacy systems is adding Gaussian random noise (jitter) to coordinates: an attacker who queries the API multiple times over minutes can compute the arithmetic mean of the noisy coordinates and recover the exact location.

To permanently neutralize averaging attacks, TravelMate utilizes **deterministic grid snapping**:

```python
def approximate_coordinates(
    lat: float,
    lon: float,
    precision_km: float = 5.0,
) -> tuple[float, float]:
    """
    Snap coordinates to a deterministic spatial grid centroid.
    Ensures that multiple requests from the same vicinity snap
    to the identical centroid, preventing noise-averaging attacks.
    """
    lat_deg_per_km = 1.0 / 111.32
    lon_deg_per_km = 1.0 / (111.32 * max(0.01, math.cos(math.radians(lat))))

    grid_lat = precision_km * lat_deg_per_km
    grid_lon = precision_km * lon_deg_per_km

    approx_lat = round(lat / grid_lat) * grid_lat
    approx_lon = round(lon / grid_lon) * grid_lon
    return (round(approx_lat, 4), round(approx_lon, 4))
```

### Properties of Grid Snapping:
- **Spatial Resolution**: Snaps coordinates to approximately $5\text{ km} \times 5\text{ km}$ spatial buckets.
- **Repeatability**: A user staying in the same hotel or cafe will consistently project to the same centroid.
- **K-Anonymity**: Any user within the same $25\text{ km}^2$ cell shares the identical coordinate representation.

---

## 3. User Location Sharing Modes

TravelMate provides three user-controlled sharing levels via `sharing_mode`:

| Sharing Mode | Internal Storage | Discoverable By Other Users | Use Cases |
| :--- | :--- | :--- | :--- |
| `private` (Default) | Stored only for personal trip planning | No coordinates or presence exposed | Default mode, maximum privacy |
| `approximate` | Stored internally, transformed on output | Only snapped centroid (~5km) visible | Future companion discovery in city |
| `explicit_share` | Explicit consent required | Only authorized companions during active trip | Co-travelers on joint itinerary |

---

## 4. Anti-IDOR & Endpoint Security

### Direct Object Reference Protection
- Location endpoints are strictly user-centric:
  - `GET /api/v1/me/location`: Reads only the authenticated `current_user.id`.
  - `PUT /api/v1/me/location`: Updates only the authenticated `current_user.id`.
  - `DELETE /api/v1/me/location`: Purges records for the authenticated `current_user.id`.
- There are no public `/api/v1/users/{id}/location` endpoints.
- Unauthenticated requests are rejected with `401 Unauthorized`.
- Non-admin requests attempting to query internal user location tables are rejected with `403 Forbidden`.

---

## 5. Threat Model & Countermeasures

| Threat Vector | Risk Level | Architectural Countermeasure |
| :--- | :--- | :--- |
| **GPS Trail Profiling** | Critical | Continuous tracking is disabled. TravelMate stores at most one record per user (latest location); historical paths are not saved. |
| **Noise Averaging** | High | Deterministic grid snapping replaces random jitter, preventing mathematical reconstruction of coordinates. |
| **Trip Stalking** | High | Trips allow `private` visibility; public discovery feeds show date ranges and destination summaries, never real-time location. |
| **Frontend Tampering** | Medium | All proximity and bounding box calculations are computed server-side in PostGIS. |
