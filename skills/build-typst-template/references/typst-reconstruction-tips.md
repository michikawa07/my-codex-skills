# Typst Reconstruction Tips

Read only the section matching the active implementation problem. Keep a tip
here when it resolves a concrete Typst decision, supplements a gap left by the
Skill and ordinary official documentation, is supported by a versioned minimal
probe or two unrelated projects, and generalizes without a target-specific
value or policy. Keep one-project hypotheses in the run notes.

## Test natural width before wrapped extent

Use this when one publication form applies to a single-line object and another
form applies after wrapping, such as centered versus hanging captions.

Inside the actual local `layout`, compose and style the exact compact candidate.
Use unconstrained `measure(candidate).width` to decide whether that candidate
fits on one line. Use `measure(candidate, width: size.width)` only to inspect
the extent after it has been allowed to wrap:

```typst
#layout(size => {
  let natural = measure(candidate).width
  if natural <= size.width {
    render-single-line(candidate)
  } else {
    render-wrapped(candidate, size.width)
  }
})
```

A constrained measurement normally fits its constraint, so use the
unconstrained natural width for this distinction. Source evidence must still
establish that the publication actually uses both forms.

## Use a combined accent for a combined mark

Use this when a source equation contains a multi-mark accent such as a second
time derivative. In Typst 0.14.2, nested `$ dot(dot(x)) $` places two single-dot
accents vertically, whereas `$ dot.double(x) $` produces the intended
horizontal double dot. Use the semantic combined accent, then verify the mark
count and placement in a focused high-resolution render in addition to
successful equation compilation.

## Bound reference shorthand beside CJK prose

Use this when `@label` or `@key` is followed immediately by Japanese or other
Unicode identifier characters. Typst 0.14.2 can consume that following prose as
part of the label. Keep the ordinary shorthand where punctuation or whitespace
ends it; use the explicit standard form at an ambiguous lexical boundary:

```typst
@fig:overview。
#ref(<fig:overview>)では次を示す。
#cite(<source-key>)によれば、
```

This remains the standard Typst reference/citation route. Keep localized
wording and caption supplements in their respective template policies. After
template styling, extract equation, figure, and table references separately
because their target kinds and punctuation can differ.

Re-probe the matching minimal case after an engine upgrade.

## Materialize injected indented prose as a paragraph

Use this when a template injects a content value into an isolated text block
and the publication requires a first-line indent. In a Typst 0.14.2 minimal
probe, a local `set par(first-line-indent: ...)` left the injected first line at
the block edge even with `all: true`. Materializing the content as an explicit
paragraph established the intended relation:

```typst
#par(first-line-indent: (amount: 1em, all: true))[
  #injected-prose
]
```

Keep the evidenced indent and paragraph properties at their semantic owner.
Confirm the first and continuation line edges in the integrated render; source
presence of the setting is not the observed result. Re-probe this case after an
engine upgrade.
