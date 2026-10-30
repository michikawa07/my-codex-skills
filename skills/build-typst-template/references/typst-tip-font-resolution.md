# Diagnosing CLI Font Discovery

For font-discovery diagnosis in an established CLI workflow:

```sh
typst fonts --variants --font-path <font-dir>
typst compile --font-path <font-dir> input.typ output.pdf
```

`--font-path` adds a directory that Typst recursively searches for fonts,
alongside enabled system and embedded font sources. Pass
`--ignore-system-fonts` and/or `--ignore-embedded-fonts` consistently to
discovery and compilation when excluding those sources.

A font file found on disk or reported by `fc-match` is not necessarily loadable
by Typst; `typst fonts` reports what Typst recognizes with the selected font
paths and font-source options.

The exact-face requirement, substitution decision, and PDF comparison are
defined in `SKILL.md`.
