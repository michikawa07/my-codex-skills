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
