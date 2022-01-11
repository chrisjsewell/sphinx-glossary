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


@pytest.mark.param_file(PATH.joinpath("docutils.txt"), fmt="dot")
def test_role(setup_docutils, file_params):
    """Test the parsing the role."""
    warning_stream = StringIO()
    string = publish_string(
        file_params.content,
        writer_name="pseudoxml",
        settings_overrides={
            "warning_stream": warning_stream,
            "output_encoding": "unicode",
        },
    )
    assert warning_stream.getvalue().strip() == ""
    file_params.assert_expected(string, rstrip_lines=True)
