"""Run tests against docutils parsing."""
from io import StringIO
from pathlib import Path

from docutils.core import publish_string
from docutils.parsers.rst import roles
import pytest

from sphinx_glossary.docutils_ import GlsRole


@pytest.fixture()
def setup_docutils():
    """Temporarily register the docutils components."""
    roles.register_local_role(GlsRole.name, GlsRole())
    yield
    roles._roles.pop(GlsRole.name, None)


PATH = Path(__file__).parent / "fixtures"


@pytest.mark.param_file(PATH.joinpath("docutils_gls_role.txt"), fmt="dot")
def test_role_rst(setup_docutils, file_params):
    """Test the parsing the role with the RSTParser."""
    warning_stream = StringIO()
    string = publish_string(
        file_params.content,
        parser_name="restructuredtext",
        writer_name="pseudoxml",
        settings_overrides={
            "warning_stream": warning_stream,
            "output_encoding": "unicode",
            "gls_references": {
                "term1": {"name": "a", "value": 1.2345},
                "term2": {"name": "b", "value": 1.2345},
                "term3": {"name": "c", "value": 1.2345},
            },
        },
    )
    warnings = warning_stream.getvalue().strip()
    if warnings:
        warnings += "\n"
    file_params.assert_expected(warnings + string, rstrip_lines=True)
