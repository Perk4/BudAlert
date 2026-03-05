"""
Underscore import alias for legacy `joint-ecommerce.stoops`.
"""

from ._compat import load_legacy_submodule

_legacy_module = load_legacy_submodule("stoops")

StoopsScraper = _legacy_module.StoopsScraper
scrape_stoops = _legacy_module.scrape_stoops

__all__ = ["StoopsScraper", "scrape_stoops"]
