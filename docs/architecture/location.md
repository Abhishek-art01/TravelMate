# Location & Geospatial Architecture

TravelMate uses PostgreSQL with PostGIS as its authoritative geospatial foundation for destination catalogs, proximity queries, traveler itineraries, and location-aware discovery.

```text
PostgreSQL + PostGIS (geography(Point, 4326))
                     │
                     ▼
             GeographyPointType
       (SQLAlchemy @compiles hook)
         │                       │
         ▼ (Postgres)            ▼ (SQLite Fallback)
geography(Point, 4326)      VARCHAR(64) + Haversine
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
              LocationService
     ├── Destination Resolution & Search
     ├── Alias Normalization (e.g. Bombay -> Mumbai)
     ├── Geospatial Proximity Queries (ST_DWithin / Haversine)
     └── Privacy-Aware User Location Snapping
```

---

## 1. PostGIS Foundation & Portability

### Database Layer
- Authoritative coordinates use the WGS 84 spatial reference system (`SRID 4326`) with PostGIS `geography(Point, 4326)`.
- Using `geography` rather than planar `geometry` guarantees spherical distance calculations in meters across Earth coordinates without planar distortion.
- Spatial indexing uses PostGIS GiST index:
  ```sql
  CREATE INDEX idx_destinations_geom_gist ON destinations USING gist (geom);
  ```

### Cross-Dialect Portability (`GeographyPointType`)
To allow fast, zero-dependency in-memory SQLite testing alongside production PostGIS, TravelMate implements a dialect-aware SQLAlchemy type:

```python
class GeographyPointType(TypeDecorator):
    impl = UserDefinedType

@compiles(GeographyPointType, "postgresql")
def compile_geography_point_pg(type_, compiler, **kw):
    return "geography(Point, 4326)"

@compiles(GeographyPointType)
def compile_geography_point_default(type_, compiler, **kw):
    return "VARCHAR(64)"
```

When running in SQLite, coordinates are persisted as `"lon,lat"` strings and distance calculations automatically fall back to the in-memory spherical Haversine formula, ensuring complete testability without external database dependencies.

---

## 2. Destination Catalog & Hierarchy

Destinations represent standardized travel locations to which trips, itineraries, and companion matching are pinned:

### Hierarchy
```text
Country (e.g. Japan, ISO code JPN)
   └── Region / State (e.g. Kansai)
         └── City (e.g. Kyoto)
               └── Destination (e.g. Kyoto Cultural District, slug: kyoto)
```

### Destination Entity
- `id`: Stable UUID primary key.
- `name`: Official display name.
- `slug`: URL-safe, unique alphanumeric slug.
- `country`: Full country name.
- `country_code`: Standard ISO 3166-1 alpha-2 / alpha-3 code.
- `region`: Administrative region or state.
- `city`: Optional city/municipality name.
- `latitude` & `longitude`: Authoritative floating-point coordinates.
- `geom`: PostGIS geography point.
- `timezone`: IANA timezone identifier (e.g. `Asia/Tokyo`).
- `category`: Destination category (`city`, `beach`, `mountain`, `cultural`, `adventure`, `nature`, `general`).
- `status`: Lifecycle publication status (`active`, `draft`, `archived`).

---

## 3. Alias Normalization Subsystem

Travelers search for destinations using historical names, colloquial variants, airport codes, or alternate romanizations:

- `DestinationAlias` stores normalized lowercase alias records:
  - `alias`: Unique index on `(destination_id, alias)`.
  - Example: Destination `Mumbai` has aliases `["bombay", "bambai"]`.
  - Example: Destination `Bengaluru` has aliases `["bangalore", "blr"]`.
- Search resolution performs case-insensitive prefix and exact matching against destination names, cities, regions, countries, and alias tables.

---

## 4. Proximity Queries

Proximity search allows finding destinations within a specified radius $R$ of given coordinates $(lat, lon)$:

- **PostGIS Query Engine**:
  ```sql
  SELECT id, name, ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_meters
  FROM destinations
  WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_meters)
  ORDER BY distance_meters ASC
  LIMIT :limit;
  ```
- **Fallback Engine**:
  Computes great-circle distance via Haversine formula:
  $$d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
  Filters destinations where $d \le R$ and orders by calculated distance.

---

## 5. Location Privacy Integration

User location is strictly decoupled from exact destination locations:
- Destinations store exact center coordinates.
- Traveler locations pass through the `LocationPrivacyService` transformation pipeline before being discoverable or queryable by other users.
