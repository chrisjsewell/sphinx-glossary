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

    @property
    def document(self) -> nodes.document:
        """Get the sphinx environment."""
        return self.inliner.document

    @property
    def sphinx_env(self) -> Optional["BuildEnvironment"]:
        """Get the sphinx environment."""
        try:
            return self.document.settings.env
        except AttributeError:
            return None

    def get_source_info(self) -> Tuple[str, int]:
        return self.inliner.reporter.get_source_and_line(self.lineno)  # type: ignore

    def set_source_info(self, node: nodes.Node) -> None:
        node.source, node.line = self.get_source_info()

    def create_warning(
        self, text: str, subtype: str
    ) -> Tuple[nodes.problematic, nodes.system_message]:
        """Create a warning node.

        :param msg: The message to use.
        """
        # TODO handle sphinx warning suppression
        wtype = "gls"
        msg = self.inliner.reporter.error(
            f"{text} [{wtype}.{subtype}]", line=self.lineno
        )
        prb = self.inliner.problematic(self.rawtext, self.rawtext, msg)
        return prb, msg

    @staticmethod
    def sanitize_key(key: str) -> str:
        """Sanitize the key.

        :param key: The key to sanitize.
        """
        return re.subn(r"[^a-zA-Z0-9_]", "_", str(key))[0]

    def get_references(self) -> Dict[str, Dict[str, Any]]:
        """Gather all glossary sources"""
        # TODO cache, we want to get from config/top-matter, directly/via file
        references: Dict[str, Dict[str, Any]] = {}
        if self.sphinx_env:
            global_references = self.sphinx_env.config.gls_references
        else:
            global_references = getattr(self.document.settings, "gls_references", {})

        for key, data in (global_references or {}).items():
            assert isinstance(
                data, dict
            ), f"gls_references values must be dict, got: {key!r}: {data!r}"
            key = self.sanitize_key(key)
            references[key] = {"source": "__config__", "data": data}

        return references

    def generate_nodes(
        self, key: str, format_string: str, data: dict
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Generate nodes."""
        # TODO document reserved keys
        kwargs = {**data["data"], **{"key_": key, "source_": data["source"]}}
        return GlsFormatter(self).format(format_string, **kwargs)

    def nested_parse(
        self, text: str
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Parse text."""
        # TODO this is not yet directly supported in myst-parser (will be in v0.17)
        if hasattr(self.inliner, "_renderer"):
            renderer = self.inliner._renderer
            container = nodes.Element()
            with renderer.current_node_context(container):
                tokens = renderer.md.parseInline(text, renderer.md_env)
                for token in tokens:
                    if token.map:
                        token.map = [
                            token.map[0] + self.lineno,
                            token.map[1] + self.lineno,
                        ]
                renderer._render_tokens(tokens)

            return container.children, []

        # we are actually just parsing back to the inliner what it gave us
        return self.inliner.parse(text, self.lineno, self.inliner, self.inliner.parent)

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
        # set variables
        self.rawtext = rawtext
        self.lineno = lineno
        self.inliner = inliner

        # evaluate the text
        text = unescape(text)
        terms_format = text.split(" ", 1)
        keys = terms_format[0].split(",")
        fmt_string = (
            terms_format[1] if len(terms_format) > 1 else "{key_}"
        )  # TODO get default from config
        # TODO literal_eval (to remove '' or "")?

        references = self.get_references()

        new_nodes = []
        messages = []
        for key in keys:
            key = self.sanitize_key(key)
            if key not in references:
                prb, msg = self.create_warning(
                    f"{key!r} key not found in glossary", "not_found"
                )
                new_nodes.append(prb)
                messages.append(msg)
            else:
                inline = nodes.inline(
                    key, gls_key=key, gls_source=references[key]["source"]
                )
                result, msgs = self.generate_nodes(key, fmt_string, references[key])
                inline.extend(result)
                new_nodes.append(inline)
                messages.extend(msgs)

        for node in new_nodes:
            self.set_source_info(node)
            for child in node.children:
                self.set_source_info(child)

        return new_nodes, messages


class GlsFormatter(Formatter):
    """Convert a format string to a list of docutils nodes.

    See: https://docs.python.org/3/library/string.html
    """

    def __init__(self, role: GlsRole, warn_missing: bool = True) -> None:
        """Initialize the formatter."""
        super().__init__()
        self.warn_missing = warn_missing
        self.role = role

    def format(
        self, format_string: str, **kwargs
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Format the format string.

        :param format_string: The format string to format.
        """
        result: List[nodes.Node] = []
        messages: List[nodes.system_message] = []
        try:
            for literal_text, field_name, format_spec, conversion in self.parse(
                format_string
            ):
                # output the literal text
                if literal_text:
                    result.append(nodes.Text(literal_text, literal_text))
                # if there's a field, output it
                if field_name is not None:
                    if field_name in kwargs:
                        output, msgs = self.convert_field(
                            kwargs[field_name], conversion, format_spec
                        )
                        result.extend(output)
                        messages.extend(msgs)
                    elif self.warn_missing:
                        prb, msg = self.role.create_warning(
                            f"Unknown format field {field_name!r}", "format"
                        )
                        result.append(prb)
                        messages.append(msg)
        except Exception as exc:
            prb, msg = self.role.create_warning(
                f"Error while parsing format string: {exc}", "format"
            )
            result.append(prb)
            messages.append(msg)

        return result, messages

    def convert_field(
        self, value: Any, conversion: Optional[str], format_spec: Optional[str]
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Convert a field, with an optional conversion and format_spec.

        For example `{key:=1!s}` will convert the value of key to a string and

        :param value: The value to convert.
        :param format_spec: The format specifier (character after :).
        :param conversion: The conversion to use (character after !).
        """
        # standard conversions
        obj = _UNSET
        if conversion is None:
            obj = value
        elif conversion == "s":
            obj = str(value)
        elif conversion == "r":
            obj = repr(value)
        elif conversion == "f":
            obj = float(value)
        elif conversion == "i":
            obj = int(value)
        elif conversion == "a":
            obj = ascii(value)
        if obj is not _UNSET:
            text = format(obj, format_spec)
            return [nodes.Text(text, text)], []

        # special docutils conversions
        if conversion == "p":
            return self.role.nested_parse(str(value))
        if conversion == "s":
            node = nodes.strong()
            node.append(nodes.Text(str(value), str(value)))
            return [node], []
        if conversion == "e":
            node = nodes.emphasis()
            node.append(nodes.Text(str(value), str(value)))
            return [node], []
        if conversion == "u":
            node = nodes.superscript()
            node.append(nodes.Text(str(value), str(value)))
            return [node], []
        if conversion == "l":
            node = nodes.subscript()
            node.append(nodes.Text(str(value), str(value)))
            return [node], []

        prb, msg = self.role.create_warning(
            f"Unknown conversion format {conversion!r}", "format"
        )
        return [prb], [msg]


class _UNSET:
    """A sentinel value for unset values."""
