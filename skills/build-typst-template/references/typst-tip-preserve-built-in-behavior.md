# Preserve Typst's Built-in Behavior

Read this tip before a wrapper, helper function, or manual rendering route
replaces or encloses a standard Typst document element.

In this tip:

- a **standard element** is ordinary Typst author syntax such as `heading`,
  `list`, `enum`, `math.equation`, `figure`, `table`, `cite`, or `ref`;
- **built-in behavior** is behavior supplied by that element, including natural
  size, wrapping, page or column breaking, counters, labels, links, nesting,
  headers repeated by `table.header(repeat: true)`, and displacement of
  following content;
- a **custom route** is a wrapper, helper, fixed box, `stack`, `grid`, `place`,
  `move`, or manually rendered replacement that changes how the standard
  element reaches the page.
- an **indivisible wrapper** keeps all of its contents on one page or column.

## Decide Before Customizing

Before adding a custom route:

1. write the ordinary standard-element syntax for the author action;
2. list every applicable built-in behavior, including behavior activated only
   by realistic author changes rather than the official fixture;
3. identify the exact source requirement that the standard route does not
   reproduce;
4. prefer `set` and `show` rules that retain the standard element;
5. if a custom route remains necessary, list each built-in behavior it can
   change;
6. use the smallest author-input variations needed to exercise each behavior
   the custom route can change.

Do not remove a built-in behavior merely because the official sample does not
activate it. A fixed publication rule may change appearance; it does not imply
that ordinary author changes should lose counters, links, wrapping, or natural
flow.

## Causal Guide

| Element or relation | Custom route that can cause the failure | Built-in behavior at risk | Typical failure under an author change | Preferred starting point |
|---|---|---|---|---|
| Frontmatter | Fixed-height block, one indivisible `stack`, or absolute placement | Content-dependent height, page breaking, movement of following content | A longer title, author block, abstract, or keyword list overlaps a sibling or footer | Emit children in normal document order; keep only source-required indivisible children together |
| Table | Keep a table that must span pages inside an indivisible wrapper or floating placement | Page breaking and headers requested through `table.header(repeat: true)` | A long table moves as a whole, leaves a large blank area, or crosses the footer | In Typst 0.14.2, an in-flow `figure(table(...), placement: none)` with `show figure.where(kind: table): set block(breakable: true)` can split. Preserve the native figure/table route and check caption attachment separately; see [table flow and rule spacing](typst-tip-table-flow-and-rules.md) |
| Table row or cell | Force a sample-derived row height | Natural row height and multiline formation | Wrapped text or math crosses a rule or another row | Use natural or minimum height unless the source establishes a fixed height |
| Numbered equation | Measure in unbounded width or force one sample-derived row height | Layout in the width supplied by the actual parent and natural equation height | A long formula reaches the number; a tall fraction overlaps neighboring content | Establish the number width and gap, then form the equation in the remaining finite width |
| List | Draw markers and numbers as ordinary text | Counter progression, nesting, item attachment, and page continuation | Inserted or deleted items keep old numbers; nested or split items detach from markers | Keep `enum`, `list`, or `terms` and style their existing structure |
| Figure | Correct layout with positioned `place`, visual-only `move`, or author-side spacing | Space reserved before following content and figure-caption attachment | The image moves without moving its caption or following prose | Keep one standard `figure` element; express publication spacing and caption policy in template rules |
| Caption | Render prefix, number, and body as unrelated text | Figure counter, label target, link, and caption attachment | Insertion changes the figure number but not the visible caption or prose reference | Style the standard caption and its counter-derived number |
| Reference | Type references directly, or use only a floating object's declaration location | Target counter, link, renumbering, and displayed page | Insertion leaves stale numbers; moving a float leaves its page reference or link on the declaration page | Keep `@label` or `ref`; verify object numbering and [displayed-page references](typst-tip-float-page-references.md) separately |
| Citation | Type `(1)` or `[1]` directly | Citation ordering, clustering, bibliography relation, and link | Reordering sources leaves stale numbers or bibliography order | Keep `cite` and let CSL plus template policy render it |
| Column flow | Use a fixed grid as a replacement for flowing columns | Reading order and continuation from one column or page to the next | Longer prose does not continue through the intended columns | Use the source-supported column flow; use a grid only when the source defines independent cells |
| Repeated group | Fix a helper or grid to the number of items in the sample | Content-dependent item count and collapse | One item leaves an empty slot; an added item overlaps or disappears | Derive layout from the collection length, or validate a source-required fixed count explicitly |

The preferred starting points retain Typst behavior while the target rule is
being inferred. They do not override structural or normative source evidence.

## Select the Variation from the Risk

Use the causal guide to choose a focused variation. For example:

- after a custom equation row changes available width or height, use one long
  equation and one tall equation;
- after list marker rendering changes, insert and delete an item, nest one
  item, and make one item cross a page or column;
- after a table wrapper changes page flow, use enough ordinary author-supplied
  rows to cross a
  page and observe requested header repetition and the first paragraph or
  heading after the table;
- after an optional frontmatter route changes, omit that field and lengthen a
  present field until following content moves or a page boundary is crossed;
- after changing a group whose layout assumes a fixed item count, render one,
  two, three, and four items and remove one item from the middle.

These are minimum checks for the built-in behaviors changed by the custom
route. Add another observation when a rendered mismatch presents a different
plausible cause, and state which implementation decision that observation will
change. Use this selection for the focused variation; still perform the active
element packet's other rechecks and the required full-document comparisons.
