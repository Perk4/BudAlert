"""
Joint Ecommerce platform scrapers package (underscore import alias).

This package keeps `joint-ecommerce/` as the source of truth and exposes
`joint_ecommerce` as a valid Python import path.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "JointEcommerceScraper",
    "AltaScraper",
    "scrape_alta",
    "StoopsScraper",
    "scrape_stoops",
]


def __getattr__(name: str) -> Any:
    if name == "JointEcommerceScraper":
        return import_module(".base_scraper", __name__).JointEcommerceScraper
    if name in {"AltaScraper", "scrape_alta"}:
        module = import_module(".alta", __name__)
        return getattr(module, name)
    if name in {"StoopsScraper", "scrape_stoops"}:
        module = import_module(".stoops", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
