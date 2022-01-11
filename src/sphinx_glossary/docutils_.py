"""Define docutils elements.

This module intentionally does not import anything from sphinx.

References:
- https://docutils.sourceforge.io/docs/howto/rst-directives.html
"""
import re
from string import Formatter
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from docutils import nodes
from docutils.parsers.rst.states import Inliner
from docutils.transforms import Transform
from docutils.utils import unescape

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class GlsRole:
    """The docutils `gls` role for referencing glossary entries.

    The text should be a comma separated list of terms (no whitespace),
    optionally followed by space then a format string.

    For example: `` :gls:`term1,term2,term3 format string` ``
    """

    name: str = "gls"
    """The role name to register."""

    def __call__(
        self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options: Optional[Dict] = None,
        content: Optional[List[str]] = None,
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Call the role.

        :param name: The role name actually used in the document.
        :param rawtext: A string containing the entire interpreted text input.
        :param text: The interpreted text content.
        :param lineno: The line number where rawtext appears in the input.
        :param inliner: The inliner instance that called us.
        :param options: A dictionary of directive options for customization
                        (from the "role" directive)
        :param content: A list of strings, the directive content for customization
                        (from the "role" directive).
        """
        text = unescape(text)
        # evaluate the text
        terms_format = text.split(" ", 1)
        # create a placeholder, for later substitution
        placeholder = nodes.inline(text, terms_format[0])
        placeholder[self.name] = True
        placeholder["keys"] = terms_format[0].split(",")
        placeholder["format"] = terms_format[1] if len(terms_format) > 1 else ""
        # TODO literal_eval?
        placeholder.source, placeholder.line = inliner.reporter.get_source_and_line(
            lineno
        )
        return [placeholder], []


class ReferenceResolver(Transform):
    """Docutils transform for resolving references."""

    default_priority = 100  # TODO check this

    @property
    def sphinx_env(self) -> Optional["BuildEnvironment"]:
        """Get the sphinx environment."""
        return self.document.settings.env

    def sanitize_key(self, key: str) -> str:
        """Sanitize the key.

        :param key: The key to sanitize.
        """
        return re.subn(r"[^a-zA-Z0-9_]", "_", str(key))[0]

    def create_warning(
        self, msg: str, base_node: nodes.Node, subtype: str
    ) -> nodes.system_message:
        """Create a warning node.

        :param msg: The message to use.
        """
        # TODO sphinx handle suppression
        wtype = "gls"
        msg = f"{msg} [{wtype}.{subtype}]"
        return self.document.reporter.error(msg, base_node=base_node)

    def apply(self, **kwargs):
        """Apply the transform."""
        # gather all glossary sources
        references = {}
        if self.sphinx_env:
            for key, data in (self.sphinx_env.config.gls_references or {}).items():
                assert isinstance(
                    data, dict
                ), f"gls_references values must be dict, got: {key!r}: {data!r}"
                key = self.sanitize_key(key)
                references[key] = {"source": "__global__", "data": data}

        # iterate through all the glossary references
        # in docutils v0.18 traverse is deprecated for findall
        iterator = getattr(self.document, "findall", self.document.traverse)
        for node in list(iterator(nodes.inline)):
            if GlsRole.name not in node.attributes:
                continue
            new_nodes = []
            for key in node["keys"]:
                if key not in references:
                    new_nodes.extend(
                        [self.create_warning(f"Unknown reference: {key}", node, "ref")]
                    )
                else:
                    new_nodes.extend(self.generate_nodes(key, node, references[key]))
            if new_nodes:
                node.replace_self(new_nodes)
            else:
                node.parent.remove(node)

    def generate_nodes(
        self, key: str, node: nodes.inline, data: dict
    ) -> List[nodes.Node]:
        """Generate nodes."""
        # TODO document reserved keys
        kwargs = {**data["data"], **{"key_": key, "source_": data["source"]}}
        format_string = node["format"] or "{key_}"  # TODO get default from config
        return RefFormatter(self.document, node).format(format_string, **kwargs)


class RefFormatter(Formatter):
    """Convert a format string to a list of docutils nodes.

    See: https://docs.python.org/3/library/string.html
    """

    def __init__(self, document: nodes.document, node: nodes.Node) -> None:
        """Initialize the formatter."""
        super().__init__()
        self.document = document
        self.node = node

    def format(self, format_string: str, **kwargs) -> List[nodes.Node]:
        """Format the format string.

        :param format_string: The format string to format.
        """
        result: List[nodes.Node] = []
        # TODO handle parse failure
        for literal_text, field_name, format_spec, conversion in self.parse(
            format_string
        ):
            # output the literal text
            if literal_text:
                result.append(nodes.Text(literal_text, literal_text))
            # if there's a field, output it
            if field_name is not None:
                if field_name in kwargs:
                    result.extend(
                        self.convert_field(kwargs[field_name], conversion, format_spec)
                    )
                else:
                    # TODO sphinx handle suppression
                    msg = f"Unknown field {field_name!r} [gls.format]"
                    result.append(
                        self.document.reporter.error(msg, base_node=self.node)
                    )

        return result

    def convert_field(
        self, value: Any, conversion: Optional[str], format_spec: Optional[str]
    ) -> List[nodes.Node]:
        """Convert a field, with an optional conversion and format_spec.

        For example `{key:=1!s}` will convert the value of key to a string and

        :param value: The value to convert.
        :param format_spec: The format specifier (character after :).
        :param conversion: The conversion to use (character after !).
        """
        if conversion == "s":
            text = str(value)
            return [nodes.Text(str(value), str(value))]
        elif conversion == "r":
            text = repr(value)
        else:
            text = str(value)
        return [nodes.Text(text, text)]

        # elif conversion == "a":
        #     return ascii(value)
        # elif conversion == "f":
        #     return float(value)
        # elif conversion == "i":
        #     return int(value)
        # elif conversion == "p":
        #     return pprint.pformat(value)
        # elif conversion == "c":
        #     return pprint.pformat(value, width=40)
        # else:
        #     raise ValueError(f"Unknown conversion {conversion!r}")
