# Lists

**Requires** — Established body/column width, paragraph rules, inherited
typography, and page/column flow.

**Owns** — List semantics, hierarchy, markers/counters, item attachment, and
continuation across pages or columns.

**Emits** — A standard Typst list route whose nesting, continuation, and item
flow remain coherent under justified content changes.

**Recheck** — Ordered, unordered, and description forms evidenced by the
source; nested and continued lists; split items; sibling paragraphs; and
following flow.

Route Lists first, then open Items as its one direct child. Close Items across
short, multiline, and split content before closing the list composition.

- **Lists [C,T]** — ordered/unordered/description semantics; nesting;
  marker or counter style, prefix/suffix, alignment, marker-body gap,
  counter reset/continuation, page flow.
  - **Items [C,T]** — marker attachment; item indentation and spacing;
    paragraph children; keep/break and split behavior.

Trace each claimed author syntax to its expected semantic output and observed
rendered output. Confirm the same author API carries the list through page and
column flow.
