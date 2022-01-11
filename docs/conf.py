"""The sphinx configuration file."""
from sphinx_glossary import __version__

project = "sphinx-glossary"
author = "Chris Sewell"
copyright = "2021, Chris Sewell"
version = release = __version__

extensions = ["myst_parser", "sphinx_glossary"]
html_theme = "furo"
html_title = "sphinx-glossary"

gls_references = {
    "key1": {"name": "me", "value": 1.2345, "description": "something *nested*"}
}
