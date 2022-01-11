# sphinx-glossary

A sphinx extension for creating glossaries and bibliographies from external files.

## Example

In your ``conf.py`` file, add the following:

```python
gls_references = {
    "key1": {"name": "me", "value": 1.2345, "description": "something *nested*"}
}
```

Then you can reference the key data in your documents using the `gls` role:

```md
This is the description of `key1`: {gls}`key1 {name}, {value:.2f}, {description!p}`
```

This is the description of `key1`: {gls}`key1 {name}, {value:.2f}, {description!p}`

## Variable formatting

Variable formatting follows the [Python format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax), with some additional conversion flags.

The following conversion flags (after `!`) are available:

| Type | Meaning |
| ---- | ------- |
|      | `str()` format. This is the default type. |
| `r`  | `repr()` format. |
| `f`  | `float()` format. |
| `i`  | `int()` format. |
| `a`  | `ascii()` format. |
| `p`  | Parsed format. This format performs an inline nested parse on the string |
| `e`  | Emphasis format. Wrap the string in an *emphasis* marker |
| `s`  | Strong format. Wrap the string in a **strong** marker |
| `u`  | Upper format. Wrap the string in an superscript marker |
| `l`  | Lower format. Wrap the string in an subscript marker |
