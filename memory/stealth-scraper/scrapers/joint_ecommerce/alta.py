"""
Underscore import alias for legacy `joint-ecommerce.alta`.
"""

from ._compat import load_legacy_submodule

_legacy_module = load_legacy_submodule("alta")

AltaScraper = _legacy_module.AltaScraper
scrape_alta = _legacy_module.scrape_alta

__all__ = ["AltaScraper", "scrape_alta"]
