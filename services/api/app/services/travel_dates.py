from __future__ import annotations

from datetime import date


def is_date_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
    """
    Check if two date intervals [start1, end1] and [start2, end2] overlap.
    Boundary conditions: if end1 == start2 or start1 == end2, they overlap.
    Interval condition: start1 <= end2 AND start2 <= end1.
    """
    if start1 > end1:
        raise ValueError(f"Invalid interval: start1 ({start1}) is after end1 ({end1})")
    if start2 > end2:
        raise ValueError(f"Invalid interval: start2 ({start2}) is after end2 ({end2})")

    return start1 <= end2 and start2 <= end1


def validate_date_range(start_date: date, end_date: date, max_days: int = 365) -> None:
    """Validate that start_date <= end_date and does not exceed max_days."""
    if start_date > end_date:
        raise ValueError("Trip start_date must be on or before end_date")
    duration = (end_date - start_date).days
    if duration > max_days:
        raise ValueError(f"Trip duration cannot exceed {max_days} days (provided: {duration} days)")
