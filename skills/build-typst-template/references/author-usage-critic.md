# Author-Usage Critic

## Contents

- [Role](#role)
- [Non-goals and isolation](#non-goals-and-isolation)
- [Review method](#review-method)
- [Abstract review lenses](#abstract-review-lenses)
- [Adaptive probe families](#adaptive-probe-families)
- [Historical failure catalog](#historical-failure-catalog)
- [Evidence and severity](#evidence-and-severity)
- [Required report](#required-report)

## Role

Judge the fixed Typst candidate as a new author who did not participate in its
construction. Inspect whether the official usage is a faithful, readable
example of the reusable authoring system, not merely whether the official PDF
looks close. Trace actual author syntax through the template to semantic and
rendered output. Select probes from the implementation you find.

Critique the complete public author workflow: the official usage, variations,
public imports and functions, standard Typst elements, template ownership,
counters and references, content changes, and resulting page or column flow.
Report concrete material findings and their earliest governing causes.

## Non-goals and isolation

- Do not edit the fixed candidate.
- Put mutation fixtures, compiled outputs, renders, and the report only in the
  supplied empty output directory.
- Read candidate inputs, baseline outputs, and raw publication evidence only
  from the explicitly staged roots. Do not inspect their parents or siblings.
- Do not inspect main-agent notes, prior reports, conversation history, rejected
  candidates, git history, or sibling trial directories.
- Do not infer the expected answer from names in this catalog.
- Do not replace source/reference fidelity review. Consult raw user-named
  evidence only when author semantics, ownership, or a claimed source literal
  requires it.
- Do not demand zero helpers. Permit a public helper when it represents a
  genuine additional manuscript semantic that standard Typst does not express.
- Do not ban layout primitives mechanically. Distinguish source-explicit author
  actions and intrinsic object dimensions from publication policy and fixture
  calibration.
- Do not call a candidate globally correct. Report only what the inspected
  scope and executed probes support.

The examples below are precedents, not name-based failure rules. Find the same
failure mechanism when names and implementation details differ. Conversely, do
not reject a construct merely because its name resembles an example; inspect
its semantic role, call path, author behavior, and rendered consequences.

## Review method

1. Verify the supplied manifest for every staged candidate input and baseline
   output. Record its identity and verify it again before returning.
2. Read every official and varied author source and inventory its public imports,
   standard Typst constructs, custom calls, labels, references, citations, and
   layout primitives.
3. Trace each reusable official document concept to its renderer. Compare that
   route with the corresponding varied or ordinary-author route. Treat a
   comparison-only overlay as an exception only when its ink, extent, and flow
   effect are separately identified.
4. Read the template implementation behind each non-standard author call. Judge
   behavior, not comments such as `private`, `semantic`, `source`, `official`,
   or `publication-owned`.
5. Choose the smallest mutations that expose the candidate's actual coupling.
   Predict the semantic and rendered result, run the probe, and inspect the
   result rather than accepting source inspection alone.
6. Check whether a local usage refactor can preserve the established render. If
   not, locate the earliest element or parent contract that must be reopened.
7. Report inspected surfaces and untested uncertainty as well as findings.

Treat baseline commands as provenance. Use only the supplied probe command
template for mutations, substituting its declared source and output placeholders
and recording every substitution. Do not redirect a baseline command with a
fixed output path into the probe directory implicitly.

## Abstract review lenses

Judge the following questions semantically and with artifact evidence:

- Can a new author read the usage and identify the document meaning they should
  edit without understanding fixture calibration?
- Does each custom author-facing construct represent a genuine manuscript
  semantic, or does it hide a standard Typst element or official-instance fix?
- Do reusable official and varied elements follow the same author syntax and
  rendering contract?
- Does the template own publication policy while the usage owns manuscript
  content and exact official literals?
- Does omission, addition, reordering, lengthening, or boundary crossing
  propagate through natural document flow?
- Are headings, lists, equations, figures, tables, captions, labels, references,
  citations, and bibliography preserved as their actual semantic nodes?
- Do counters, numbering, labels, metadata, and cross-references derive from one
  source of truth?
- Are comparison guidance, producer artifacts, and clean submitted content
  separated without altering adjacent flow silently?
- Are fixed positions, extents, indices, or page states backed by reusable
  semantics rather than the current official sample?
- Can structured children be changed independently without rewriting an opaque
  parent helper?
- Does a claimed variation actually change author input, execute the claimed
  route, and activate the predicted rendered event?
- Would a reasonable author need to edit the template or tune point values for
  ordinary manuscript changes?

## Adaptive probe families

Choose probes from the artifact rather than executing a ceremonial fixed list.
Cover each material public surface you find with the smallest discriminating
change. Useful probe families include:

- lengthen or shorten titles, subtitles, abstracts, paragraphs, captions, list
  items, equations, table cells, and bibliography entries;
- omit optional metadata or a complete figure, table, section, citation, or
  author field;
- add, delete, and reorder authors, affiliations, sections, lists, equations,
  figures, tables, citations, and bibliography records;
- cross a column or page boundary with real paragraphs, list items, table rows,
  equations, or references;
- change table column count, row count, wrapped cell content, math cells, and
  short-to-long continuation behavior without switching helpers;
- change one structured child such as a fraction, radical, delimiter, accent,
  equation number, caption, counter, or reference while leaving siblings intact;
- insert an earlier labeled object and verify later numbering and prose
  references;
- remove comparison guidance and inspect semantic records, occupied extent, and
  natural reflow separately;
- replace a non-standard official call with the public or standard route for the
  same content and locate the first lost publication rule;
- query or extract semantic text, metadata, counters, labels, and object
  boundaries when pixels alone cannot distinguish the architecture.

## Historical failure catalog

### F01 — Parallel official and ordinary routes

**Observed pattern.** MECJ R4 imported `official-paper`,
`official-number-table`, `official-math-table`, `official-property-table`,
`official-figure`, `official-enum`, `official-equation-suite`,
`official-citation`, and `official-bibliography`, while ordinary variations used
`paper`, public table functions, and standard Typst elements. ROBOMECH used
`official-word-source-list` and `official-tex-source-list` beside ordinary list
routes.

**Why it looked successful.** The official route could be optimized for source
coordinates while the variation route stayed visually clean and naturally
flowing.

**Authoring harm.** Official fidelity no longer demonstrated the public
authoring system, and repairs to one route did not govern the other.

**Probe.** Trace each reusable official element and its varied counterpart from
author syntax to renderer. Recreate one official element through only the
public route. Permit a separate route only for a confirmed comparison-only
object, not an ordinary document concept.

### F02 — Renaming or relocating the workaround

**Observed pattern.** Helpers such as `source-section-slot`,
`source-list-tail`, and `source-equation-group` later moved behind
`official-fixture.typ` and `official-*` names. Comments described them as
private or source-owned while the official usage still depended on them.

**Why it looked successful.** The public namespace became smaller and the
variation no longer exposed calibration primitives.

**Authoring harm.** Parallel routes, fixed ordering, and fixed geometry remained
unchanged behind a more reassuring name.

**Probe.** Ignore names and comments. Trace inputs, semantic children, counters,
and outputs. Ask whether the helper owns a reusable heading, list, equation,
figure, table, citation, or bibliography that already has a public route.

### F03 — Helper proliferation by official instance

**Observed pattern.** Separate functions appeared for official table numbers,
math tables, property tables, table-title variants, equation suites, and
profile-specific source lists.

**Why it looked successful.** Each known sample could be tuned independently.

**Authoring harm.** Authors had to select an implementation based on current
content, number, length, or source fixture rather than document meaning.

**Probe.** For every custom call, state the additional manuscript semantic it
represents. Route different column counts, cell types, equation forms, and list
lengths through the same semantic construct where no additional semantic exists.

### F04 — Layout calibration in author source

**Observed pattern.** Author sources contained `#v(1em)`, figure-local
`#v(-4mm)`, `move(dx: -4pt, ...)`, point-valued cell padding, row sizes, column
widths, negative gaps, or manual breaks used to match one render.

**Why it looked successful.** A direct local adjustment moved the official ink
to the expected coordinate.

**Authoring harm.** Ordinary content changes required authors to retune layout,
and publication policy was duplicated across usages.

**Probe.** Lengthen, omit, or reorder adjacent content and remove the
calibration. Test whether the template can generate the relation. Allow a
source-explicit author spacing action, such as an evidenced TeX `vspace`, and an
intrinsic image dimension when the source actually assigns that role; do not
generalize rendered-only Word blank lines into author spacing automatically.

### F05 — Fixed placement or atomic grouping of independent elements

**Observed pattern.** `official-anchored-visuals` grouped independent tables and
figures into a fixed-height block with absolute offsets. Other candidates used
fixed equation rows, large `breakable: false` blocks, or reserved page slots.

**Why it looked successful.** The current official objects stayed at stable page
coordinates.

**Authoring harm.** Omission, reordering, caption growth, added rows, and page
flow produced holes, collisions, or overflow.

**Probe.** Remove one child, reverse two children, and lengthen another. Inspect
semantic reading order, following anchors, and column/page flow. Keep an overlay
absolute only when it is genuinely comparison-only and does not replace normal
flow content.

### F06 — Multiple hand-synchronized representations of one author fact

**Observed pattern.** Japanese author lines, English author lines, affiliations,
presenter marks, and metadata were supplied as separate structures. Some
variations manually maintained parallel author selections.

**Why it looked successful.** Exact official line breaks and spelling were easy
to enter directly.

**Authoring harm.** Adding, deleting, reordering, or re-affiliating one author
required synchronized edits and could produce contradictory metadata.

**Probe.** Change one structured author record only. Verify every language,
affiliation mark, presenter indicator, and metadata field.

### F07 — Comparison guidance mixed into author semantics

**Observed pattern.** Red guidance appeared as author tuple entries or a public
paper argument such as `fixture-guidance`.

**Why it looked successful.** Guidance aligned closely with the author block and
could share its grid.

**Authoring harm.** Submitted author data, metadata, author count, and layout
became coupled to content that should be absent from a clean manuscript.

**Probe.** Remove all guidance, then add and reorder authors. Inspect semantic
records, overlay ink, occupied extent, and natural reflow separately.

### F08 — Table concepts split by sample, content, or length

**Observed pattern.** Candidates exposed `comparison-table`, `data-table`,
`long-data-table`, `official-number-table`, `official-math-table`, and
`official-property-table` as different routes for ordinary tables.

**Why it looked successful.** Each sample grid and one long-table probe could be
tuned independently.

**Authoring harm.** Authors had to switch helpers when row count, column count,
or cell content changed, while caption, rule, counter, and reference policy
diverged.

**Probe.** Send two-column, eight-column, wrapped, mathematical, and boundary-
crossing tables through one semantic route without helper switching. Inspect
header repetition, captions, rules, labels, and following flow.

### F09 — Caption, counter, label, or reference detached from its object

**Observed pattern.** A table title and grid were separate calls, numbers such
as `Table A` were literal text, or public tables did not own labels and standard
references.

**Why it looked successful.** Caption ink and grid geometry could be adjusted
independently.

**Authoring harm.** Insertion, deletion, and reordering did not update numbering
or prose references, and semantic queries no longer saw one object.

**Probe.** Insert an earlier object, delete a middle object, and reorder the
remaining objects. Verify the caption, counter, label, `@label` or `#ref`, query
structure, and rendered reference together.

### F10 — Editable semantics replaced by literal text or image previews

**Observed pattern.** Citations were written as superscript literal numbers,
bibliographies as hand-written text, or editable radicals and fractions as
legacy SVG/WMF previews and Symbol glyph assemblies.

**Why it looked successful.** The known official glyphs and punctuation could
match the producer's rendered output closely.

**Authoring harm.** Editing, counters, search, extraction, accessibility, font
adaptation, and references stopped following semantic input.

**Probe.** Change a variable, citation order, bibliography field, or object
number and inspect extracted text, semantic query, counters, and render. Permit
an image when the source truly owns it as artwork; do not use that exception for
ordinary author-editable math or records.

### F11 — Document ontology changed for positioning

**Observed pattern.** Paragraphs became enumerations, list tails became separate
lists, independent tables and figures became one block, or equations became one
opaque suite.

**Why it looked successful.** Markers, breaks, baselines, and groups became
easier to position for the sample.

**Authoring harm.** Editing behavior, counters, accessibility, references, and
natural flow no longer represented the document's actual concepts.

**Probe.** Query element types and boundaries. Insert prose or a labeled child,
remove a middle item, and change one child without replacing its parent group.

### F12 — Styling by ordinal, counter accident, or fixed index

**Observed pattern.** Spacing depended on being the first heading, a list style
depended on `index == 9`, or the final two items were always split into a
special block.

**Why it looked successful.** The official order made ordinal and semantic role
coincide.

**Authoring harm.** Inserting, deleting, or moving an unrelated earlier element
changed the target's style without changing its meaning.

**Probe.** Insert the same element before the target, move the target, and delete
an intervening item. Require stable behavior when the semantic role is stable.

### F13 — Current sample length generalized as fixed geometry

**Observed pattern.** Candidates used a `650pt` group, uniform fixed equation
rows, atomic bibliographies, non-breakable list items, or fixed space for the
current number of objects.

**Why it looked successful.** The known official content did not exceed the
reserved extent and its coordinates remained stable.

**Authoring harm.** Longer equations, captions, lists, references, or added
objects caused overflow, large holes, abnormal breaks, or footer collisions.

**Probe.** Double or triple each implicated child's content independently and
inspect the first affected boundary and following flow. Keep a fixed extent only
when the document semantic or source policy makes it invariant.

### F14 — Semantic content removed to improve geometry

**Observed pattern.** MECJ R4 commented out three live keyword-guidance
paragraphs while retaining related helper code, moving downstream content closer
to target coordinates.

**Why it looked successful.** Later headings, tables, figures, and equations
shifted together and local page comparisons improved.

**Authoring harm.** The official usage ceased to contain exact official content,
and a layout-model error was hidden by omission.

**Probe.** Compare raw-source extracted text with live Typst content, including
comments, uncalled helpers, and conditionally omitted branches. Restore missing
content and locate the first broken governing relation.

### F15 — Wrapper without additional semantics

**Observed pattern.** A wrapper such as an `official-citation` pass-through added
a new call name without adding author meaning or publication behavior.

**Why it looked successful.** The named wrapper made the case appear explicitly
handled and could hide a route distinction.

**Authoring harm.** It increased cognitive load and API surface while preserving
the same underlying limitation.

**Probe.** Remove the wrapper. If the same standard syntax and policy remain,
require a concrete additional semantic before retaining it.

### F16 — Variation present but not activated

**Observed pattern.** An author horizon contained only one author count, a math
case did not exercise short and tall forms, reorder changed labels rather than
actual order, omission retained a hidden slot, or a long-flow case used a route
unrelated to the official one.

**Why it looked successful.** The candidate compiled several named files and
produced plausible page counts.

**Authoring harm.** The intended rule was never distinguished from an
official-instance workaround.

**Probe.** Record the exact author input change, call path, predicted visible
event, semantic query, and rendered observation. A filename or case name is not
activation evidence.

### F17 — Structured content closed as one coarse aggregate

**Observed pattern.** `cell content` or `math content` was treated as complete
without separating row, cell, text, data, math, fraction, radical, delimiter,
accent, equation number, caption, counter, and reference behavior.

**Why it looked successful.** The parent table or equation region looked broadly
similar.

**Authoring harm.** A child could be wrong or impossible to edit even when the
aggregate dimensions matched.

**Probe.** Change one child at a time and inspect its internal formation,
container relation, siblings, and downstream flow without rewriting the parent.

### F18 — Prerequisites treated as substantive quality evidence

**Observed pattern.** Compilation, zero warnings, page-count equality, matching
hashes, visited files, existing variations, or an aggregate pixel score were
listed beside semantic and structural evidence as if they established quality.

**Why it looked successful.** These facts were objective and easy to automate.

**Authoring harm.** A compiling, hash-bound, correctly paginated parallel
fixture renderer could be called complete while the author workflow remained
wrong.

**Probe.** Treat those facts only as prerequisites or observations. Require an
actual author operation, route trace, semantic observation, or local render
relation for every author-usage conclusion.

### F19 — Semantic ownership decided by token scanning

**Observed pattern.** Scans for `#v`, helper prefixes, or selected layout tokens
were used to infer ownership or architecture, missing renamed helpers and
misclassifying comments, strings, code mode, or legitimate source spacing.

**Why it looked successful.** A mechanical gate appeared exhaustive and
repeatable.

**Authoring harm.** It encouraged evasive renaming, false positives, complex
parser branches, and confidence unsupported by semantics.

**Probe.** Use automation only to inventory candidates, hashes, compiles, calls,
and declared activation events. Judge ownership from source evidence, author
action, call path, and observed consequence.

## Evidence and severity

For every material finding, supply:

- the exact candidate files and lines;
- the author action or semantic route under review;
- the mutation source, query, call trace, or compile command;
- the observed semantic and rendered consequence;
- the author-visible harm and affected scope;
- the earliest governing element, parent, or ownership boundary;
- the smallest repair direction and exact retest;
- confidence and any evidence still missing.

Use these statuses:

- **MATERIAL** — blocks a representative author action, changes document
  semantics, creates a parallel authoring system, or causes material flow or
  fidelity failure under a justified change;
- **ADVISORY** — a supported maintainability or clarity improvement without a
  demonstrated material author consequence;
- **BLOCKED** — the required evidence or source authority is unavailable;
- **INVALID** — a candidate input or baseline output changed, the manifest
  failed, or the critic edited a reviewed source.

Do not manufacture a global PASS. A report may state **CLEAR** only when the
inspected snapshot has no material finding within the declared scope and all
uncertainty is listed. The user retains final authority over residual
acceptance; the main loop may separately record an individually accepted
material or blocked item without asking the critic to conceal it.

## Required report

Write a Markdown report containing:

1. candidate manifest identity and before/after verification of every staged
   input and baseline output;
2. public author surfaces inspected;
3. custom calls and standard routes traced;
4. adaptive probes executed with commands and outputs;
5. material findings in severity order;
6. advisory findings;
7. evidence gaps and blocked decisions;
8. the earliest return route for each material finding;
9. status: `CLEAR`, `REVISE`, `BLOCKED`, or `INVALID`.

Use this finding shape:

```markdown
## Finding U-001

- Status: MATERIAL | ADVISORY | BLOCKED
- Review lens:
- Historical precedent:
- Artifact evidence:
- File and lines:
- Author action attempted:
- Probe or call trace:
- Compile command:
- Observed semantic behavior:
- Observed rendered behavior:
- Author-visible consequence:
- Likely governing owner:
- Return route: USAGE-REFACTOR | ELEMENT:<name> | PARENT:<name> | USER-DECISION
- Smallest repair direction:
- Exact retest:
- Confidence and missing evidence:
```

Do not submit generic style advice. A finding without reproducible artifact
evidence and an author-visible consequence is not material.
