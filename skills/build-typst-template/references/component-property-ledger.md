# Document Element Router

[Router order](#document-element-router) · [Target list and measurements](#target-element-list-and-measurement-coverage) · [C/T vocabulary](#common-property-vocabulary)

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

## Target Element List and Measurement Coverage

The **target element list** records target-specific elements, occurrences, and
numeric checks before implementation; packet-specific rechecks are added when
their branch opens. The `inventory` block stores whether the initial list is
`open` or `complete`. A **branch path** is its unique router path, such as
`Frontmatter/Title`; an **occurrence** is one rendered instance of that branch
in the official document. Every code-formatted branch path named in the minimum
numeric table below is a **default branch**; `origin: discovered` means target inspection added it.
Start with every default branch, inspect the source structure and every rendered reference page,
then add discovered branches under their real parents. Store the list under
`inventory.target_elements`:

```yaml
- branch: "Frontmatter/Title"
  parent: "Frontmatter"
  origin: default # default | discovered
  official_presence: present # present | absent
  variation_required: false
  variation_requirement_reason: ""
  absence_evidence: []
  source_regions: []
  children: []
  official_occurrences:
    - occurrence: "page-1-title"
      reference_regions: []
      candidate_regions: []
      image_result: "" # match | mismatch | accepted_mismatch
      observed_after_last_change: false
  variation_cases:
    - case: "long-title"
      author_edit: ""
      expected_event: ""
      call_path: ""
      observed_event: ""
      result: "" # match | mismatch | accepted_mismatch
      observed_after_last_change: false
  required_rechecks:
    - check: "title wrapping and downstream flow"
      cases: ["page-1-title", "long-title"]
  numeric_selection: required # required | none
  numeric_none_reason: ""
  required_numeric:
    - relation: ""
      case: "page-1-title"
      sample_roles: [ordinary] # ordinary | longest | wrapped | split | boundary
      endpoints_and_coordinates: ""
      expected_relation: "match reference"
      reference_value: ""
      candidate_value: ""
      unit: ""
      result: "" # match | mismatch | accepted_mismatch
      observed_after_last_change: false
```

`source_regions` names the source file and stable structural locations that
establish the branch. For each occurrence, `reference_regions` names its one or
more page/column rectangles in the official rendering, while `candidate_regions`
names the corresponding rectangles in the latest generated PDF. `image_result` is `match` only when that
comparison has no visible difference. Use `accepted_mismatch` only for the exact
difference covered by a user decision, and `mismatch` for every other visible
difference; these outcomes are mutually exclusive. For each numeric
relation, `endpoints_and_coordinates` names the two measured edges or centers,
axis, coordinate origin, and positive direction. Each record covers exactly one
`case`, identified by an occurrence or variation-case label; `sample_roles` says
why that case was selected. `ordinary` is an unsplit, unwrapped case away from a
page/column boundary; the other role names mean the longest relevant content, a
wrapped case, one occurrence split across regions, or a case at that boundary.
One case may satisfy multiple roles. The two values
and unit contain the actual official and latest-candidate measurements.
`expected_relation` is `match reference` for an official case. For a variation
without an official value, set `reference_value` to reasoned `not_applicable`,
put the numeric condition required by source evidence in `expected_relation`, and
judge `candidate_value` against it. Its `result` uses the same three outcomes as
`image_result`. `observed_after_last_change` is true only after observing the
latest PDF compiled after the most recent edit that can affect that result.
For a variation, `expected_event` also names relations expected not to change,
while `observed_event` includes downstream behavior; its `result` uses the same
three outcomes. A recheck result uses them as well.
Below, **current** means recorded from that latest PDF with
`observed_after_last_change: true`. The **container rectangle** is an element's
outer layout rectangle inside its parent; the **content rectangle** is the area
inside its padding or insets that is available to its direct content. A
**signed gap** is the destination-edge coordinate minus the source-edge
coordinate along the recorded positive direction; a negative value is overlap.

For any branch absent from the official rendering, inspect every available
structural source and every rendered reference page in `absence_evidence`; mark
an unavailable evidence kind with its reason. Leave official occurrences and
official numeric records empty. `variation_required` separately records an
author-facing branch that must be implemented and closed even when absent from
the official instance. For an absent branch, `variation_requirement_reason`
records the source evidence for choosing true or false. A default branch with
`official_presence: absent` and `variation_required: false` needs no active
implementation branch. When it is true, list the activating author edit and
expected visible/structural event in `variation_cases`; mark every ancestor as
present or variation-required. Select a numeric variation record only when
source evidence supplies `expected_relation`; otherwise record
`numeric_selection: none` and its reason. `variation_required: false` never
waives the activating variation required later for a present branch.

Set `inventory.status: complete` only after every default has one presence
result, every absent branch has completed `absence_evidence` and a nonempty
`variation_requirement_reason`, every discovered
branch and official occurrence is listed, every present branch has at least one
official occurrence, and every present or
variation-required branch has its variation cases, required direct children,
and every applicable minimum relation and sample case from the table below selected.
`numeric_selection: none` always needs `numeric_none_reason`;
`required` needs every applicable record, not merely one. At this stage a record
is selected when `relation`, `case`, `sample_roles`,
`endpoints_and_coordinates`, `expected_relation`, and `unit` are filled;
candidate fields, `result`, and `observed_after_last_change` remain empty/false
until implementation and the latest compile. Only then create the first active
branch. Expand `Heading level N` into one branch path for each level found.
When a branch becomes active, read its packet and, before editing that branch,
add every relation named by the packet's `Recheck` clause and the cases that
exercise it to `required_rechecks`. Add any newly required variation case to the
same target element entry.

Each official occurrence receives a same-scale image comparison in its parent
context, including the immediately following element when one exists; for the
last occurrence, include the relevant parent or page/column bottom boundary.
One comparison region may cover several occurrences, but every covered
occurrence names that region and result. Select numeric relations before tuning
the branch. Use numbers for invisible boundaries, ambiguous whitespace,
repeated drift, and object geometry; check semantic identity, order, counters,
labels, links, and field content structurally. Use these minimum relations:

| Branch path | Minimum numeric relations |
| --- | --- |
| `Document` | None. |
| `Document/Page` | Paper width/height and the four edges of the rectangle available to Body for each source-established first/odd/even/title/body page form. |
| `Document/Page/Header`, `Document/Page/Footer` | Container rectangle; signed gap from its edge nearest Body to the corresponding Body edge; visible rule thickness when present. |
| `Frontmatter` | Container top/bottom and signed gap from its bottom edge to the first Body child's top edge. |
| `Frontmatter/Title`, `Frontmatter/Subtitle`, `Frontmatter/Authors`, `Frontmatter/Affiliations`, `Frontmatter/Abstract`, `Frontmatter/Keywords` | Content rectangle width/height and signed gap to the next present sibling; baseline interval when multiline; gap between the preceding and following present siblings when an optional sibling is omitted. |
| `Frontmatter/Authors/Presenter mark` | Signed horizontal and vertical offsets from its evidenced attachment point on the author name. |
| `Body` | Container rectangle edges; signed gap from its top edge to its first child's top edge; signed gap from its final child's bottom edge to the Body bottom edge. |
| `Body/Columns` | Column edges and gutters for each distinct column count and column/page-span combination established by source evidence. |
| `Body/Columns/Paragraphs` | First-line indent, baseline interval, and inter-paragraph gap. |
| `Body/Columns/Heading level N` | Signed before/after gaps, number-to-title gap, and multiline baseline interval for each level. |
| `Lists` | Left inset, nesting increment, and before/after gaps once per distinct numeric inset/spacing rule. |
| `Lists/Items` | Marker-to-body gap, continuation indent, and inter-item gap once per distinct numeric item-layout rule. |
| `Equations` | Width/height of the smallest rectangle containing all visible formula glyphs and rules for every official formula; when numbered, signed gap from the formula edge to the number on its source-evidenced side and signed formula-center-to-number-center vertical offset. |
| `Equations/Equation references` | None unless source evidence raises or lowers the inline reference. |
| `Figures` | Container rectangle and before/after gaps for each distinct placement and column/page-span combination established by source evidence. |
| `Figures/Images` | Intrinsic and displayed width/height; crop edges when cropping is present. |
| `Figures/Captions` | Image-to-caption gap, caption content rectangle, and multiline baseline interval. |
| `Figures/Figure references` | None unless source evidence raises or lowers the inline reference. |
| `Tables` | Container rectangle, each column boundary in one representative row, and one measurement per distinct numeric stroke-thickness rule. |
| `Tables/Rows` | One row height per distinct numeric row-height rule, using applicable header, ordinary, multiline, or math cases as samples. |
| `Tables/Rows/Cells` | Representative edge insets and applicable horizontal/vertical center or baseline offset once per distinct numeric inset/alignment rule. |
| `Tables/Table captions` | Table-to-caption gap, caption content rectangle, and multiline baseline interval. |
| `Tables/Table references` | None unless source evidence raises or lowers the inline reference. |
| `Citations` | Baseline offset only when source evidence raises or lowers a citation. |
| `References` | Heading-to-first-entry gap, bibliography edges, signed gap from the final entry's bottom edge to the Body bottom edge, and column boundaries when distinct from Body. |
| `References/Bibliography entries` | Label-to-body gap, hanging indent, wrapped baseline interval, and inter-entry gap. |

For a shared numeric rule, select the fewest cases that collectively include one
ordinary example and at least one example for each applicable longest, wrapped,
split, or page/column-boundary role. Measure every official equation.
Repeat in a variation only the relations its predicted event can change. Avoid
per-glyph, per-line, per-row, and per-cell measurements when a shared rule plus
all-occurrence image inspection covers them.

After an edit to a branch, ancestor, or shared rule, clear every affected
`official` observation and `rechecks` entry in the complete records held by `active` or `open_parents`,
candidate region/value/result in the target element list, and variation
`call_path`/`observed_event`/`result`; set `last_change_recompiled: false` on every affected open record and each affected
record in the target element list and `rechecks` to `observed_after_last_change: false`. Invalidate dependent closures and fill
these fields again only after the latest compile. Preserve a prior user decision
as source evidence, but do not treat its accepted mismatch as current until that
exact difference is observed again. The closure's `rechecks` records one keyed
observation for every `required_rechecks[].check` and case; it does not duplicate
image or numeric values.

A branch may close only when all applicable conditions below hold:

- its target entry has nonempty `source_regions`; after the latest compile,
  every applicable `active.official` container, direct-child,
  internal-formation, and downstream observation records `match` or
  `accepted_mismatch`, or records `not_applicable: <reason>` when inapplicable;
- each present branch has at least one official occurrence; every occurrence
  has nonempty reference/candidate regions, current `match` or
  `accepted_mismatch`, and no `mismatch`;
- `numeric_selection: none` has its reason, or every selected numeric record has
  applicable reference/candidate values, current `match` or
  `accepted_mismatch`, and no `mismatch`; reasoned `not_applicable` is a value
  only in the variation case defined above;
- every variation case has a call path, observed event, and current `match` or
  `accepted_mismatch`, with no `mismatch`;
- every required packet recheck and listed case has a keyed, current `match` or
  `accepted_mismatch`, with no `mismatch`; a composite also has a current observation of its direct
  children's order and placement and the following flow;
- every required child branch has a valid closure; every
  `accepted_mismatch` has the exact corresponding user decision; and the
  branch has no unresolved mismatch.

A newly found occurrence is added to its existing branch entry and reopens that
branch; only a newly found element with a different shared rule creates a new
branch path.

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
