# sphinx-glossary (IN-DEVELOPMENT!)

A sphinx extension for creating glossaries and bibliographies from external files.

All reference keys will be normalised to replace non-`[a-zA-Z0-9_]` with `_`.

Define references:

- In `conf.py`, with `gls_references` configuration variable
- In files with paths defined in `conf.py` as `gls_files` configuration variable
- Per document as `gls_references` document information variable
- Per document as `gls_files` document information variable

Reference a variable using the `gls` role.

Create a glossary with the `gls` directive.

## TODO

How to deduplicate entries? Referencing specific sources?

Per document glossaries, vs global glossaries?

Handle comma-delimited references
