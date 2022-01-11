"""The sphinx extension setup."""
from typing import Any, Dict, Sequence

from sphinx.application import Sphinx

from . import __version__
from .docutils_ import GlsRole, ReferenceResolver


def setup_extension(app: Sphinx) -> None:
    """Setup the sphinx extension"""
    # TODO validate the configuration
    app.add_config_value("gls_default_format", "{key_}", "env", types=str)
    app.add_config_value("gls_references", {}, "env", types=Dict[str, Dict[str, Any]])
    app.add_config_value("gls_files", (), "env", types=Sequence[str])
    app.add_role(GlsRole.name, GlsRole())
    app.add_transform(ReferenceResolver)

    return {"version": __version__}
