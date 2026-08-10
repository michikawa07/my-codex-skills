# Document Element Router

Use `router`, `packet`, `branch`, and `closure entry` exactly as defined in
`SKILL.md`. Open the packet for the active branch.
The target remains a reusable authoring system: the template owns publication
policy, authors use semantic fields and standard Typst content, the official
instance matches, and justified content changes remain coherent.

First inspect the source structure and rendered pages. Establish a parent
enough to define its children's coordinate and flow context, then complete its
children in reading order. Open one packet at a time:

1. [Document and page](ledger-document-page.md)
2. [Frontmatter](ledger-frontmatter.md)
3. [Body flow](ledger-body-flow.md)
4. [Lists](ledger-lists.md)
5. [Equations](ledger-equations.md)
6. [Figures](ledger-figures.md)
7. [Tables](ledger-tables.md)
8. [Citations and references](ledger-citations-references.md)

Use the `router-cursor.yaml` schema in `SKILL.md`; it records the active branch,
active direct child, observed parent coordinate/width/inheritance/flow, and
remaining packet `Recheck` relations. Advance only from a closure entry.

Open a later packet only when every observation named by its `Requires` section
is present in valid closure entries. When later evidence changes a coordinate
system, inherited rule, available width, flow policy, or counter, reopen the
first affected branch as defined in `SKILL.md`. Add an unknown element under its
real parent and place it after every element whose recorded output it requires.

## Common Property Vocabulary

Apply **C** to every container in two separate observations:

1. its placement and extent within the parent: width and height policy (fixed,
   intrinsic, fill-parent, measured, min/max), and horizontal/vertical position;
2. its direct children's placement within that box: padding or insets on every
   edge, internal alignment and spacing, columns, gutters, flow, overflow,
   keep/break, and page behavior.

Apply **T** to text formation inside its established content box: font family,
face, and fallback; size; weight and style; glyph horizontal scale or character
width; tracking and word spacing; color and baseline position; internal
horizontal/vertical alignment; line pitch; wrapping and explicit breaks; first,
continuation, final, hanging, left, and right line edges and indents; space before
and after; keep-with-next, keep-lines, widow/orphan, and page-break behavior.

For each applicable prompt, first inspect normative or structural values,
repeated instances, and visual measurements; then choose one of the four owner categories in `SKILL.md`,
target, confidence, author syntax, and implementation. For an element marked
`[C,T]`, record its parent placement, direct-child placement, and internal text
formation separately. Its packet and closure entry supply the current evidence.
