# Document Element Router

[Router order](#document-element-router) · [Target list and measurements](#target-element-list-and-measurement-coverage) · [C/T vocabulary](#common-property-vocabulary)

Use `router`, `packet`, `branch`, and `closure entry` exactly as defined in
`SKILL.md`. Open the packet for the active branch.
The target remains a reusable authoring system: the template owns publication
policy, authors use semantic fields and standard Typst content, the official
instance matches, and justified content changes remain coherent.

First inspect the source structure and rendered pages. Establish a parent
enough to define its children's coordinate and flow context, then complete its
children in reading order. Open one packet at a time. In every packet, each
semicolon-separated relation following a branch name is a required packet
starter property; split it further when the source or Typst implementation
controls its parts independently. The eight numbered entries are also the eight **critic groups**
defined in `SKILL.md`:

1. [Document and page](ledger-document-page.md)
2. [Frontmatter](ledger-frontmatter.md)
3. [Body flow](ledger-body-flow.md)
4. [Lists](ledger-lists.md)
5. [Equations](ledger-equations.md)
6. [Figures](ledger-figures.md)
7. [Tables](ledger-tables.md)
8. [Citations and references](ledger-citations-references.md)

Assign every target element to exactly one of these groups with `critic_group`; assign the root `Document` branch the
literal value `final_only`. Default branch paths use this mapping:

| `critic_group` | Assigned branch paths |
| --- | --- |
| `Document and page` | `Document/Page`, `Document/Page/Header`, and `Document/Page/Footer` |
| `Frontmatter` | `Frontmatter` and all its descendants |
| `Body flow` | `Body`, `Body/Columns`, `Body/Columns/Paragraphs`, and every `Body/Columns/Heading level N` branch |
| `Lists` | `Lists` and `Lists/Items` |
| `Equations` | `Equations` and `Equations/Equation references` |
| `Figures` | `Figures`, `Figures/Images`, `Figures/Captions`, and `Figures/Figure references` |
| `Tables` | `Tables`, `Tables/Rows`, `Tables/Rows/Cells`, `Tables/Table captions`, and `Tables/Table references` |
| `Citations and references` | `Citations`, `References`, and `References/Bibliography entries` |

Assign a discovered branch to the numbered packet that owns its rule. A critic group completes only when it has at
least one present or variation-required branch and every such branch assigned to it has a valid closure. Closing two
children of one group still completes no more than one group. Reopening any assigned branch makes the group incomplete
until that branch closes again. `final_only` is checked by the unconditional final critic and never contributes to the
intermediate critic trigger.

Use the compact `router-cursor.yaml` schema in `SKILL.md`. It points to the
target element file, font record, active branch record, waiting parent records,
closed branch records, and suspended branch records. Read detailed evidence
from the pointed-to file only when that branch, inventory, or font gate is active,
or when the file supplies a prerequisite or direct-parent relation for the active
branch. After a branch closes, read its record again only for one of those
prerequisite or direct-parent relations, invalidation or reopening, or the final
audit. Advance only from a closure entry.

Open a later packet only when every item named by its `Requires` section has a
current Prerequisites row. That row cites either a valid prerequisite record or the
direct target, font, structural-source, asset, bibliography, or rendered-page
evidence that satisfies the requirement. When later evidence changes a coordinate
system, inherited rule, available width, flow policy, or counter, reopen the
first affected branch as defined in `SKILL.md`. Add an unknown element under its
real parent and place it after every element whose recorded output it requires.

## Target Element List and Measurement Coverage

The **target element list** records target-specific elements, occurrences, and
numeric checks before implementation; packet-specific rechecks are added when
their branch opens. The cursor stores whether the initial list is `open` or
`complete`. A **branch path** is its unique router path, such as
`Frontmatter/Title`; an **occurrence** is one rendered instance of that branch
in the official document. Every code-formatted branch path named in the minimum
numeric table below is a **default branch**; `origin: discovered` means target inspection added it.
Start with every default branch, inspect the source structure and every rendered reference page,
then add discovered branches under their real parents. Store the list in
`<scratch>/target-elements.md`. Use one section per branch with these fields and
tables:

```markdown
## Frontmatter/Title

| Field | Value |
| --- | --- |
| Parent | Frontmatter |
| Critic group | Frontmatter |
| Origin | default |
| Official presence | present |
| Variation required | false |
| Variation requirement reason | ... |
| Absence evidence | ... |
| Source regions | ... |
| Direct children | ... |
| Branch record | <scratch>/branch-records/frontmatter-title.md |

### Official occurrences
| Occurrence | Reference regions |
| --- | --- |

### Variation cases
| Case | Author edit | Expected event and unchanged relations |
| --- | --- | --- |

### Required rechecks
| Check | Cases |
| --- | --- |

### Numeric relations
| Relation | Case | Sample roles | Endpoints and coordinates | Expected relation | Reference value | Unit | Method | Maximum allowed difference | Rule evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Use `present` or `absent` for official presence and `default` or `discovered`
for origin.
Write `Numeric selection: none — <reason>` instead of the numeric table when no
numeric relation is selected. The branch-record path is created when the branch
first becomes active; write `pending until active` in that field during inventory,
then replace it with the exact path when the record is created.

`Source regions` names the source file and stable structural locations that
establish the branch. For each occurrence, `Reference regions` names its one or
more page/column rectangles in the official rendering. The corresponding
candidate regions and current comparison result belong in the branch record.
Use `accepted_mismatch` only for the exact difference covered by a user decision,
and `mismatch` for every other visible difference; these outcomes are mutually
exclusive. For each numeric
relation, `Endpoints and coordinates` names the two measured edges or centers,
axis, coordinate origin, and positive direction. Each record covers exactly one
`Case`, identified by an occurrence or variation-case label; `Sample roles` says
why that case was selected. `ordinary` is an unsplit, unwrapped case away from a
page/column boundary; the other role names mean the longest relevant content, a
wrapped case, one occurrence split across regions, or a case at that boundary.
One case may satisfy multiple roles. The target element file stores the reference
value and unit; the branch record stores the latest candidate value and result.
In expressions, `reference_value` means the `Reference value` column and
`candidate_value` means the `Candidate value` column. `Expected relation` is
`candidate_value == reference_value after conversion to unit` for an official exact case. For a variation
without an official value, set `Reference value` to reasoned `not_applicable`,
put the numeric condition required by source evidence in `Expected relation`, and
judge `Candidate value` against it. Its result uses `match`, `mismatch`, or
`accepted_mismatch`. `Observed after last change` is true only after observing the
latest PDF compiled after the most recent edit that can affect that result.
The numeric-plan columns make that judgment reproducible. Before measuring the candidate, write `Expected relation` as
the true-or-false expression that will decide the result and record `Method`. For `exact`, compare values produced by the
same measurement command in `unit` with `candidate_value == reference_value`. Use `explicit_tolerance` only when the
governing source states a tolerance or the user changes the required relation before candidate measurement; put the same
maximum absolute difference in `Expected relation` and `Maximum allowed difference`, and record its evidence in
`Rule evidence`. Use `predicate` only for a variation without a reference value. Set `Reference value` to
`not_applicable`; name each candidate measurement in `Endpoints and coordinates`; store `Candidate value` as a keyed map
using those names; write the source-backed inequality or non-overlap expression in `Expected relation`; and record its
evidence in `Rule evidence`. After measurement, put the substituted expression,
exact command, and unedited standard output in the block named by `Calculation
evidence ID` rather than a prose verdict. `Result: match` is valid only when that
output is true and `Observed after last change` is true. False output requires `mismatch`; a user-approved deviation from the source-required value or relation remains
`accepted_mismatch`, not `match`.
For a variation, `Expected event and unchanged relations` names relations expected not to change,
while `Observed event and unchanged relations` includes downstream behavior; its result uses the same
three outcomes. A recheck result uses them as well.
Below, **current** means recorded from that latest PDF with
`Observed after last change: true`. The **container rectangle** is an element's
outer layout rectangle inside its parent; the **content rectangle** is the area
inside its padding or insets that is available to its direct content. A
**signed gap** is the destination-edge coordinate minus the source-edge
coordinate along the recorded positive direction; a negative value is overlap.

For any branch absent from the official rendering, inspect every available
structural source and every rendered reference page in `Absence evidence`; mark
an unavailable evidence kind with its reason. Leave official occurrences and
official numeric records empty. `Variation required` separately records an
author-facing branch that must be implemented and closed even when absent from
the official instance. For an absent branch, `Variation requirement reason`
records the source evidence for choosing true or false. A default branch with
`Official presence: absent` and `Variation required: false` needs no active
implementation branch. When it is true, list the activating author edit and
expected visible/structural event in `Variation cases`; mark every ancestor as
present or variation-required. Select a numeric variation record only when
source evidence supplies `Expected relation`; otherwise record
`Numeric selection: none` and its reason. `Variation required: false` never
waives the activating variation required later for a present branch.

Set `inventory.status: complete` only after every default has one presence
result, every absent branch has completed `Absence evidence` and a nonempty
`Variation requirement reason`, every target element has a valid `Critic group`, every discovered
branch and official occurrence is listed, every present branch has at least one
official occurrence, and every present or
variation-required branch has its variation cases, required direct children,
and every applicable minimum relation and sample case from the table below selected.
`Numeric selection: none` always needs its reason;
when the Numeric relations table is used, it must contain every applicable
record, not merely one. At this stage a plan
is selected when `Relation`, `Case`, `Sample roles`, `Endpoints and coordinates`, `Expected relation`, `Unit`, and
`Method` are filled. Before candidate measurement, `explicit_tolerance` also requires
`Maximum allowed difference` and `Rule evidence`, while `predicate` requires `Rule evidence`.
Only then create the first active
branch. Expand `Heading level N` into one branch path for each level found.
When a branch becomes active, read its packet and, before editing that branch,
add every relation named by the packet's `Recheck` clause and the cases that
exercise it to `Required rechecks`. Add any newly required variation case to the
same target element entry.

## Branch Records and Required Properties

Create one Markdown file for each active branch under
`<scratch>/branch-records/`. The file is the branch's working and closure record;
the cursor contains only its path. Use these sections:

```markdown
# Frontmatter/Authors

| Field | Value |
| --- | --- |
| Parent | Frontmatter |
| Packet | references/ledger-frontmatter.md |
| Critic group | Frontmatter |
| Target entry | target-elements.md#frontmatterauthors |
| Status | open |
| Last change recompiled | false |

## Author route and official content
| Document role and boundary | Document-role owner | Author syntax and call path | Official content and source | Official-content owner | Relations expected not to change | Observed after last change |
| --- | --- | --- | --- | --- | --- | --- |

## Prerequisites
| Requirement | Evidence or prerequisite record and current observation | Observed after last change |
| --- | --- | --- |

## Property discovery
| Required inspection | Locations inspected | Properties added or `none: <reason>` | Complete |
| --- | --- | --- | --- |

## Required properties
| Property | Added from | Source evidence and required relation | Requirement basis | Owner | Typst file and control | Official observation and evidence ID | Variation observation or reason not applicable, and evidence ID | Result | Observed after last change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Official occurrence results
| Occurrence | Candidate regions | Comparison observation and evidence ID | Result | Observed after last change |
| --- | --- | --- | --- | --- |

## Variation results
| Case | Call path | Observed event, unchanged relations, and evidence ID | Result | Observed after last change |
| --- | --- | --- | --- | --- |

## Numeric results
| Relation and case | Candidate value | Calculation evidence ID | Result | Observed after last change |
| --- | --- | --- | --- | --- |

## Rechecks
| Check and case | Observation and evidence ID | Result | Observed after last change |
| --- | --- | --- | --- |

## Child closures
| Child branch | Record file |
| --- | --- |

## Unresolved mismatches
| Item | Observation and evidence ID |
| --- | --- |

## Accepted mismatches
| Item | Exact user decision | Current observation and evidence ID |
| --- | --- | --- |

## Evidence
### E-001
Command and unedited output:
~~~text
...
~~~
```

An evidence ID is a unique `E-<number>` label inside that branch record. Put a
short observation and the ID in the table cell. In that ID's fenced Evidence
block, put the exact command and unedited output, or the inspected file path and
the direct visual observation when no command produced the observation. For a
numeric calculation, the block also contains the substituted `Expected relation`
expression. Do not place raw multiline output or unescaped pipe characters
inside a table cell.

`Requirement basis` is exactly one of: `direct_source` when the cited structural
source states the required relation; `rendered_inference` when the relation is
inferred from rendered evidence because no structural source states it; or
`user_decision` when an explicit user choice determines the required relation.

`Status` is `open`, `closed`, or `invalidated`. An `invalidated` record never
satisfies a closure and must not appear in `active`, `open_parents`, `closures`,
or `suspended`; create a new branch record when that branch is rebuilt after a
full inventory/font reset.

`Added from` lists one or more of `common C starter`, `common T starter`,
`packet starter`, or `discovered`. One row satisfies every listed starter when
they require the same relation. Before editing the branch, add the common
starter rows selected by its `[C]` and `[T]` markers and every branch-specific
starter named in its packet. Add one Property discovery row for each numbered
inspection below. Then perform all four inspections and add one
`discovered` row for each semantic or layout relation not already represented.
A relation is already represented only when one existing row names the same
affected elements, the same predicate or measured endpoints, the same required
outcome, and the same source rule:

1. a source rule applied directly to the branch or inherited from an ancestor;
2. a source container or construct that sets direct-child order, grouping,
   alignment, spacing, wrapping, or breaks;
3. each official occurrence's content identity and order; counters, labels, and
   links; placement and extent in its parent; direct-child
   arrangement, internal text or structured-content formation, relation to its
   preceding and following siblings, and effect on later flow;
4. each selected author variation's predicted changed relations and predicted
   unchanged relations.

For each Property discovery row, name every inspected file location or rendered
region, the property rows it produced, and `Complete: yes`; use
`none: <reason>` only when that inspection produced no additional relation.
The `Source evidence and required relation` cell names the source location or
reference region and states the relation to reproduce. The `Typst file and
control` cell names the exact file and setting, rule, or function that implements
it. A common starter that has no corresponding relation in the source or target
structure may use `not_applicable: <structural reason>` in its required-relation,
Typst-control, official, variation, and Result cells. Its official and variation
cells still cite a same-file evidence ID. A packet starter may do so
only when the target entry and cited source evidence establish that the named
relation is absent. Set `Observed after last change` to `true` after confirming
that absence. Such a row satisfies closure. For any other property that the
selected variation cannot affect, record the reason in the variation cell.
That cell still cites a same-file evidence ID.
Finish this property list before tuning the branch. If a
later comparison reveals a missing property, add it and keep or reopen the branch.

Each official occurrence receives a same-scale image comparison in its parent
context, including the immediately following element when one exists; for the
last occurrence, include the relevant parent or page/column bottom boundary.
One comparison region may cover several occurrences, but every covered
occurrence has its own result row in the active branch record. Select numeric relations before tuning
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

After an edit to a branch, ancestor, or shared rule, remove each affected closure
pointer and apply all of these changes to every affected branch record before
compiling:

1. set `Status` to `open` and `Last change recompiled` to `false`;
2. set the Author route and official content row's `Observed after last change`
   value to `false`, and clear its
   call path when author syntax or a template route changed;
3. set each Prerequisites row's `Observed after last change` value to `false`
   whenever its cited evidence or cited prerequisite relation is no longer
   current or satisfying;
4. set Property discovery inspections 3 and 4 to `Complete: no` after any edit that
   can change rendering, and also set inspections 1 and 2 to incomplete when the
   structural source or an inherited ancestor rule changed;
5. clear every affected required property's Typst control when that control
   changed, and always clear its official observation, variation observation,
   Result, and `Observed after last change` value;
6. clear affected Official occurrence, Variation, Numeric, and Recheck result
   rows, and remove a Child closures row when that child was invalidated;
7. preserve an accepted-mismatch user decision, but clear its current
   observation until that exact difference is observed again.

Fill the cleared fields only from the latest compile. The branch record's
Rechecks section has one row for every check and case planned in the target
element file; it does not duplicate image or numeric values.

If `Expected relation`, `Method`, `Maximum allowed difference`, or `Rule evidence` changes after
candidate measurement, clear that numeric result row's `Candidate value`, `Calculation evidence ID`, `Result`, and
`Observed after last change`, then measure it again after the next compile.

A branch may close only when all applicable conditions below hold:

- its Author route and official content row has no empty cell and is current;
  every item named by the packet's `Requires` section has a current Prerequisites
  row that names either a valid prerequisite record or direct evidence and the
  corresponding observation; a direct-evidence observation must establish the
  prerequisite and have no unresolved contradiction; its target entry has
  nonempty source regions; every required common and packet
  starter branch property has a row; all four Property discovery rows name inspected
  locations, properties added or a concrete reason for none, and `Complete: yes`;
  and every applicable property row names source evidence, its required relation,
  Requirement basis, owner, and exact Typst file/control; a `not_applicable` row instead satisfies
  the explicit structural-absence rule above;
- after the latest compile, every property row for a present branch has a current
  official observation; for an official-absent but variation-required branch,
  the official cell instead cites that branch's absence evidence and a same-file
  evidence ID as `not_applicable`; every property row has a current variation observation or a
  justified reason that the selected variation cannot affect it, and its observed
  comparison is `match`, `accepted_mismatch`, or the permitted
  `not_applicable`; no property row remains
  `mismatch` or unobserved;
- each present branch has at least one official occurrence; every occurrence
  has nonempty reference regions in the target file and candidate regions in the
  branch record, current `match` or
  `accepted_mismatch`, and no `mismatch`;
- `Numeric selection: none` has its reason, or every selected numeric plan and result row has applicable reference and candidate values,
  a `Method` and concrete `Expected relation` recorded before candidate measurement, `Rule evidence` when required, and current calculation output; `match`
  requires true output and `Observed after last change: true`, while false output is permitted only with `accepted_mismatch` and
  its exact user decision; no record may remain `mismatch`; reasoned `not_applicable` is a value
  only in the variation case defined above;
- every variation case has a call path, observed event and unchanged relations, and current `match` or
  `accepted_mismatch`, with no `mismatch`;
- every required packet recheck and listed case has a keyed, current `match` or
  `accepted_mismatch`, with no `mismatch`; a composite also has a current observation of its direct
  children's order and placement and the following flow;
- `Last change recompiled` is `true`; every required child branch has a valid closure; every
  `accepted_mismatch` has the exact corresponding user decision; and the
  Unresolved mismatches section is empty;
- every cell in a branch-record column whose heading contains `evidence ID` is
  nonempty and resolves to one same-file Evidence block; any evidence ID cited
  in another column resolves the same way. That block contains a nonempty command
  or inspected file path and its unedited output or direct visual observation; a
  Numeric row's block also contains the substituted `Expected relation`
  expression.

A newly found occurrence is added to its existing branch entry and reopens that
branch; only a newly found element with a different shared rule creates a new
branch path.

## Common Property Vocabulary

The `[C]` and `[T]` markers in a packet select required starter rows for the
branch record. They are a minimum, not a claim that no other property exists.

For every `[C]` branch, start with these rows:

| Starter layout property | Relation to identify |
| --- | --- |
| Parent placement and extent | Width policy, height policy, and horizontal and vertical position inside the parent. |
| Edge insets | Content offsets from all four container edges. |
| Direct-child order and grouping | Which children share a row, column, line, or source construct that prevents an internal break, and their reading order. |
| Direct-child layout | Stack, inline flow, grid, columns, or another source construct; include column widths and gutters when present. |
| Direct-child alignment and spacing | Horizontal and vertical alignment plus the gaps between children or groups. |
| Overflow and document flow | Wrapping, clipping, growth, keep/break, and page or column behavior. |

For every `[T]` branch, start with these rows:

| Starter layout property | Relation to identify |
| --- | --- |
| Font selection | Font role and resolved face from the completed font record, including fallback when the source defines one. |
| Text style | Size, weight, style, color, horizontal scale, tracking, and word spacing that the source applies to this branch. |
| Baseline placement | Vertical placement of glyphs or inline objects relative to the line. |
| Line alignment | Left, center, right, or justified formation inside the content box. |
| Line formation | Line pitch, wrapping, hyphenation, and source-required explicit breaks. |
| Line edges and indents | First, continuation, final, hanging, left, and right line edges or indents that occur. |
| Text-block spacing and breaks | Space before and after; keep-with-next, keep-lines, widow/orphan, and page or column breaks. |

For each row, inspect structural values, inherited values, repeated instances,
and the rendered relation; then record its Requirement basis, owner, target relation, Typst control,
official observation, and relevant variation observation. Use a separate row
when the source or Typst implementation controls parts of one starter property
independently. For an inapplicable row, record the concrete structural reason.
For an element marked `[C,T]`, keep container placement, direct-child placement,
and internal text formation as separate rows. Add every target-specific relation
found by the discovered-property inspection above; the starter tables do not
limit that inspection.
