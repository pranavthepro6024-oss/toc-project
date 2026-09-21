"""Declarative vendor protocol adapters."""

from afco.adapters.conformance import ConformanceReport, check_conformance, validate_adapter
from afco.adapters.loader import AdapterLoadError, load_adapter, load_adapter_text, load_adapter_with_report

__all__ = [
    "AdapterLoadError",
    "ConformanceReport",
    "check_conformance",
    "validate_adapter",
    "load_adapter",
    "load_adapter_text",
    "load_adapter_with_report",
]
