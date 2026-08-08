# Document Element Router

Use this router to open the packet for the branch currently being completed.
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

Keep a scratch cursor containing the active branch, active direct child,
established parent contract, and remaining packet `Recheck` relations. Apply
the Element Completion Loop in `SKILL.md` to that branch and advance the cursor
from the observations that close it.

Open a later packet when its required parent context and upstream flow are
stable enough to interpret it. Reopen the earliest governing packet when later
evidence changes a coordinate system, inherited rule, available width, flow
policy, counter, or other upstream contract. Add an unknown element under its
real parent and route it by the contract it depends on. This index supplies the
default coverage and dependencies.

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
repeated instances, and visual measurements; then choose the semantic owner,
target, confidence, author syntax, and implementation. For an element marked
`[C,T]`, record its parent placement, direct-child placement, and internal text
formation separately. Its branch packet supplies the current closure context.
