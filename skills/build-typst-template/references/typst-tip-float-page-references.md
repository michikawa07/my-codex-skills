# Page References to Placed Figures

Read this when a figure moves to another page but its page reference, outline
entry, or link still points to the page where it was declared.

A figure's declaration location and the location of its displayed body can
differ. Correct figure numbers do not establish correct page references: the
figure counter and the page counter answer different questions.

## Reproduce the Difference

This standalone diagnostic reproduces the difference in Typst 0.14.2. The small
page and rectangle are probe inputs, not publication defaults.

```typst
#set page(width: 250pt, height: 300pt, margin: 20pt, numbering: "1")
#set text(size: 10pt)
#lorem(100)

#figure(
  [#metadata("drawn")<probe-body>#rect(width: 80%, height: 140pt)],
  kind: image,
  placement: bottom,
  caption: [A floating object.],
) <probe-figure>

Page reference: #ref(<probe-figure>, form: "page").
#context {
  let source = query(<probe-figure>).first().location()
  let drawn = query(<probe-body>).first().location()
  [Source sheet: #source.page(). Drawn sheet: #drawn.page().
  Drawn page number: #numbering(drawn.page-numbering(), ..counter(page).at(drawn)).]
}
```

In the tested output, the figure remained numbered 1, its declaration was on
sheet 1, and its body appeared on sheet 2. The native page reference printed 1.
For a project probe, keep its normal page/font settings and vary preceding prose
until the figure actually moves. Inspect the rendered pages beside the queries.

## Repair and Recheck

- Keep the original figure's identity, counter, label, and author syntax.
- If a correction is needed, associate that identity with a nonprinting location
  marker inside the displayed body or caption. A marker before the figure still
  measures its declaration. A caption-only marker needs a route for captionless
  figures. Avoid copying the public label onto a second semantic object.
- Resolve the page reference, figure/table outline page, and link destination
  from the corresponding displayed location. For a multi-page table, use its
  actual start location.
- `location.page()` is the physical sheet index. A printed page number must use
  the page counter and numbering at that location, including Roman front matter
  and page-counter resets. The diagnostic shows that distinction explicitly.
  If page numbering is `none`, apply the document's unnumbered-page policy
  instead of passing `none` as a numbering pattern.
- Repeat the move after inserting an earlier numbered figure. Verify the object
  number, displayed page number, outline page, and PDF link destination
  separately. The same incorrect location can make references and outlines
  agree with each other while both are wrong.

Use a correction only where the current compiler and route demonstrate the
failure. See the [location API](https://typst.app/docs/reference/introspection/location/)
and the [upstream floating-reference issue](https://github.com/typst/typst/issues/4359).
