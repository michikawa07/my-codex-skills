# Table Breaks, Caption Attachment, and Rule Padding

Read this when changing table length separates its caption, or changing the
structure of an otherwise equivalent table changes its spacing.

## Splitting the Table Does Not Keep Its Caption Attached

A native `table` inside `figure` can split in Typst 0.14.2. An in-flow figure
(`placement: none`) and a breakable block allow the following diagnostic to
continue across pages:

```typst
#set page(width: 180pt, height: 200pt, margin: 20pt)
#show figure.where(kind: table): set block(breakable: true)
#figure(
  table(columns: 2,
    table.header([Row], [Value]),
    ..range(40).map(i => ([Row #i], [Value #i])).flatten(),
  ),
  placement: none,
  caption: [A table that continues across pages.],
)
```

In the tested 0.14.2 output, all 40 rows appeared once across five pages, with
repeated headers, but the bottom caption occupied a sixth page alone. This is a
reproducer of missing attachment, not a complete layout repair. Page counts can
change with the font environment.

For a top caption, add preceding prose until the caption alone fits at the
bottom of a page but the first table rows do not. Observe the caption, header,
and first data row. For a bottom caption, observe the final row and caption.

Keep a top caption with the following table start and a bottom caption with the
preceding table end. If a custom caption rule adds a block or alignment wrapper,
check attachment at that actual wrapper boundary. A sticky block follows the
next block in its flow; it does not provide backward attachment for a bottom
caption. Keeping the entire long table unbreakable loses the requested page
continuation.

After a repair, verify native figure/table/caption structure, all row identifiers,
header repetition, caption/reference numbers, and following prose. Retain a
short table near a page boundary as well as the multi-page table: native
association and correct numbering can survive a visually orphaned caption.
See [figure behavior](https://typst.app/docs/reference/model/figure/)
and [block stickiness](https://typst.app/docs/reference/layout/block/#parameters-sticky).

## Equivalent Short Tables Must Retain Their Rule Spacing

A TeX-derived template applied rule padding only when the first top-level child
was `table.hline`. Moving that same line inside `table.header` bypassed the
padding, although the native table and all cells remained present. The measured
header-to-first-row spacing changed from about 19.03 to 13.55 PDF points. Those
values describe the observed failure; they are not template defaults.

Insert this ordinary figure through the template's public author route. Compile
once with `--input rule-position=outside` and once with
`--input rule-position=inside`:

```typst
#let inside = sys.inputs.at("rule-position", default: "outside") == "inside"
#let header = if inside {
  (table.header(
    table.hline(stroke: 0.8pt), [Condition], [Value],
    table.hline(stroke: 0.5pt),
  ),)
} else {
  (table.hline(stroke: 0.8pt), table.header([Condition], [Value]),
    table.hline(stroke: 0.5pt))
}
#figure(
  table(columns: 2, stroke: none,
    ..header, [One], [1], [Two], [2], table.hline(stroke: 0.8pt),
  ),
  placement: none,
  caption: [Identical data and rules.],
)
```

Both native-control outputs have the same short-table geometry. Use a one-page
table for this comparison: placing rules inside a repeated header can
intentionally change which rules recur on later pages.

For the template outputs, compare column edges, row pitch, rule thickness, and
rule-to-cell clearance in the table's local coordinates. Also try equivalent
explicit cell coordinates. Trace conditional fallbacks that bypass publication
rules; a valid native table alone does not establish equivalent formatting.

Derive padding from the resolved rule/cell relationships, including header and
footer groups and spans, while retaining the native structure. Do not add empty
semantic rows to hold rule gaps. A later continuation check must inspect the
clearance below a repeated header: the first body row there has a different
source row index from the first body row on the initial page.
