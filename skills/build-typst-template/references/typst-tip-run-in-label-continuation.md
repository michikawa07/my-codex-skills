# Run-in Labels with Aligned Continuation Lines

A **run-in label** begins on the same line as its paragraph body, such as a
`Keywords:` prefix or a caption number followed by text. Read this tip when the
first line is correct but wrapped continuation lines start at the wrong
horizontal position.

A horizontal space after the label changes only the first line. To give every
continuation line the same body edge, reserve a left inset for the whole
paragraph and return the label to the outer edge on the first line:

```typst
#let run-in-label(label, body, label-width) = block(
  inset: (left: label-width),
)[
  #set par(first-line-indent: 0pt)
  #h(-label-width)#box(width: label-width)[#align(left, label)]#body
]
```

Include the intended label-to-body gap in `label-width`. Derive a fixed width
only when source evidence reserves a fixed horizontal area. Otherwise, inside
the actual font, size, weight, and tracking settings, set `label-width` from the
unconstrained natural width of the styled label plus the gap measured from the
source; separately confirm that it fits the finite width supplied by the
parent. Use a separate block label when the label itself may wrap.

Confirm the first-line body edge, continuation-line body edge, final-line
formation, and following content with one-line and multiline bodies. Repeat the
check for each localized label whose width differs.

## Numbered Headings That Wrap

This also occurs when a heading show rule emits its number, `h(1em)`, and title
as one ordinary paragraph. A short title looks correct; a longer title's next
line returns to the number's left edge. A single-line chapter title does not
exercise a separately overridden section or subsection rule.

Use ordinary numbered headings through each affected rule, for example:

```typst
#set heading(numbering: "1.1")
= Methods

#heading(level: 2)[A long section heading describing the construction and
evaluation of a mathematical model and its relationship to measurements
collected in several operating conditions]

#heading(level: 3)[A long subsection heading describing the construction and
evaluation of a mathematical model and its relationship to measurements
collected in several operating conditions]
```

Lengthen the title until it actually wraps under the project settings. When the
publication requires hanging continuation, compare the first title word's left
edge with every continuation line's left edge, not with the number's edge.
Reserve a label column or paragraph inset for the whole heading, using the
source-required gap. Preserve its native heading identity, counter, label,
outline entry, and reference behavior when changing its visual rendering.

Check line pitch separately. Increasing the heading font size while retaining
body-text leading can produce the wrong pitch even after indentation is fixed.
Use the [local line-pitch measurement](typst-tip-line-pitch.md) with that heading
level's actual font and source-prescribed pitch. A TeX comparison exposed both
failures: continuation returned to the number's edge and pitch was about
21.05 PDF points instead of 23.31. These are observations, not reusable sizes.

Some publications intentionally use centered headings or another continuation
alignment. Apply the source's rule; wrapping by itself is not a failure, and a
critic without the source must not invent the required alignment or pitch.
