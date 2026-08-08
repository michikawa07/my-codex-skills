# Font Resolution Through the Final Compile Route

Use the same font directories for discovery, calibration, every variation, and
the accepted final compile:

```sh
typst fonts --font-path <font-dir>
typst compile --font-path <font-dir> input.typ output.pdf
```

`--font-path` adds a search directory to the active system and embedded font
sources. Record the full command and environment. Use `--ignore-system-fonts`
when the target requires resolution from the named directories, and
`--ignore-embedded-fonts` when the target evidence also excludes Typst's
embedded faces.

Resolve body text and math as separate rendering routes. Apply the evidenced
math face at the equation route when needed, for example with
`show math.equation: set text(font: "...")`. Inspect the embedded PDF faces and
focused glyphs before calibrating wrapping or spacing.
