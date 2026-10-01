from __future__ import annotations

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UserDefinedType


class GeographyPointType(UserDefinedType):
    """PostgreSQL PostGIS geography(Point, 4326) with SQLite VARCHAR fallback."""

    cache_ok = True


@compiles(GeographyPointType, "postgresql")
def compile_geography_point_pg(type_, compiler, **kw):
    return "geography(Point, 4326)"


@compiles(GeographyPointType)
def compile_geography_point_default(type_, compiler, **kw):
    return "VARCHAR(64)"
