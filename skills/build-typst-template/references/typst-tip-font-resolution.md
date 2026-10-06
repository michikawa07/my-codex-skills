# Reusing the Same Typst Font Environment

Check required faces in the user's actual Typst workflow first; if missing,
search elsewhere for the same faces before considering substitutes.
Before copying/installing fonts or changing font settings, identify the files or
settings, destination, and effect; obtain any authorization not already granted.

Use that workflow's font settings for discovery, official usage, variations, and
final checks. For an established CLI workflow, for example:

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
paths and font-source options. Keep text and math font assignments separate
when the source does.

Verify the normal preview/export routes in scope, including any required reload,
and record evidence in the existing font record. Keep the font gate open until
those checks pass; a build in another environment does not establish completion.

The exact-face requirement, substitution decision, and PDF comparison are
defined in `SKILL.md`.
