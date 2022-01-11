"""A sphinx extension for creating glossaries and bibliographies from external files."""

__version__ = "0.1.0"


def setup(app):
    """Register the sphinx extension"""
    from .sphinx_ import setup_extension

    return setup_extension(app)
