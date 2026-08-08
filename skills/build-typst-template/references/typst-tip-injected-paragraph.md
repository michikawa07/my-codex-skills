# Materialize Injected Indented Prose

Use this when a template injects content into an isolated text block and the
publication requires a first-line indent. In a Typst 0.14.2 minimal probe, a
local `set par(first-line-indent: ...)` left the injected first line at the block
edge even with `all: true`. Materializing the content as a paragraph established
the intended relation:

```typst
#par(first-line-indent: (amount: 1em, all: true))[
  #injected-prose
]
```

Keep the indent and paragraph properties at their semantic owner. Confirm the
first and continuation line edges in the integrated render, and re-probe after
an engine upgrade.
