# Tables

**Requires** — Established body/column insertion context, page flow, inherited
typography, and the semantic structure of the official table content.

**Owns** — Table width allocation, row/cell geometry, strokes, captions,
numbering, labels, and table-reference rendering.

**Emits** — A standard table route whose dimensions derive from content,
available width, and evidenced publication policy.

**Recheck** — Header/body boundaries, natural row heights, multiline and math
cells, vertical stroke continuity, repeated headers, references in prose,
caption attachment, and following flow.

Process one direct child at a time after establishing Tables: Rows, Table
captions, then Table references. Open Cells as Rows children. Close
the reference route against the already observed caption supplement and
counter, then close the table after child composition preserves widths,
strokes, numbering, caption attachment, and downstream flow.

- **Tables [C]** — semantic kind; total width; column count and width
  policy; grid/stroke sides, thickness, style and color; header repetition;
  counter/reset, label/reference semantics; caption position; page/column
  span and break behavior.
  - **Rows [C]** — header/body/footer role; natural/min/fixed height;
    separators; keep/split/repeat behavior; zebra/background styling.
    - **Cells [C,T]** — column/row span; content kind; width/height policy;
      padding; horizontal/vertical alignment; wrapping and overflow;
      background; per-edge strokes.
  - **Table captions [C,T]** — position; kind/prefix, counter and number format;
    separator/punctuation; single/multiline alignment; shared width; distance
    to table and following flow.
  - **Table references [T]** — actual author syntax; localized prose
    prefix and number format; spacing and link target; distinction from
    the caption supplement; observed inline result.

Use contextual measurement when local available space governs the result.
Separate semantic structure, content-derived dimensions, and publication
strokes so a repair explains both official and varied tables.
