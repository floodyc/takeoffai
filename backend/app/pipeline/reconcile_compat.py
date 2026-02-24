"""Compatibility shim: convert agentic SheetResult to ReconciliationReport for XLSX output.

The output.py module from aecai-lt-counter expects a ReconciliationReport.
This bridges the gap until output.py is rewritten for the new data model.
"""

from dataclasses import dataclass


@dataclass
class ReconciliationReport:
    """Minimal compat struct for output.py."""
    final_counts: dict[str, int]
    total: int
    pass1_counts: dict[str, int]
    pass1_total: int
    boundary_additions: list
    boundary_removals: list
    warnings: list[str]


def to_compat_report(sheet) -> ReconciliationReport:
    """Convert a SheetResult ORM object to ReconciliationReport."""
    return ReconciliationReport(
        final_counts=sheet.final_counts or {},
        total=sheet.total or 0,
        pass1_counts=sheet.final_counts or {},  # No separate pass1 in agentic pipeline
        pass1_total=sheet.total or 0,
        boundary_additions=[],
        boundary_removals=[],
        warnings=sheet.pattern_warnings or [],
    )
