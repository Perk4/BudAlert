"""
Underscore import alias for legacy `joint-ecommerce.base_scraper`.
"""

from ._compat import load_legacy_submodule

_legacy_module = load_legacy_submodule("base_scraper")

JointEcommerceScraper = _legacy_module.JointEcommerceScraper

__all__ = ["JointEcommerceScraper"]
