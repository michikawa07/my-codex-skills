---
name: build-typst-template
description: Build, reconstruct, or harden a reusable Typst document template from project-specific DOCX, PDF, TeX/LaTeX, or Typst evidence. Use when Codex must infer an author-facing API and layout rules from supplied publication sources, reproduce a reference document across its pages, or diagnose and repair template drift through structural and visual inspection.
---

# Build Typst Template

Reconstruct the document system evidenced by the project. Let Codex judge the
document semantics, relevant parameters, public API, Typst implementation,
visual differences, repairs, and readiness. Use automation to expose mechanical
facts that make those judgments faster.

## North Star

Port the publication format as an authoring system for a new author. The Typst
template owns the source layout machinery and publication policy; its user
supplies ordinary semantic document content through a small justified API and
standard Typst elements. The system must reproduce the official instance and
remain coherent when realistic titles,
authors, paragraphs, lists, equations, figures, tables, citations, references,
and page flow change. The deliverable combines faithful reproduction of the
official sample with reusable behavior under those author changes.

Use every inspection, compile, crop, difference, fixture, and element loop to
improve this document-level authoring system. Track progress by the author
workflow, template-owned rule, and document-wide behavior secured by each local
decision. Keep layout knowledge in the template and semantic manuscript content
in the author source.

## Bound the Evidence

Define evidence as every user-named file plus every regular file recursively
contained in a user-named directory. Calibrate from that closed set. Expand the
set when the user names an additional parent, sibling, prior output, or symlink
target.

Inventory that set before editing. Render each reference and make a shallow
all-page pass recording pagination, page roles, and top-level hierarchy.
Complete detailed inspection as corresponding semantic elements become active;
by finish, inspect every named source and every page of each reference. When
sources disagree about a reusable rule, identify the exact conflict and ask the
user which source governs. Treat metadata, extracted text, XML properties,
bboxes, and pixels as observations interpreted beside the structural source and
rendered document.

For a layered source stack, trace each rule to its role. A base class supplies
inherited defaults, a publication style or package defines publication
overrides, an author template exposes the intended author workflow and official
content, and compiled output shows realized geometry and pagination. Treat the
structural definitions as primary evidence for semantics and rule ownership,
and the render as primary evidence for their realized effects.
When the structural source that owns a target rule states a direct value,
implement that value exactly. When the realized render suggests a different
value, surface the conflict and governing sources, and preserve the stated rule
until the governing source is resolved.

Promote a choice to a template default, public API, or document semantic when
the closed evidence or explicit user direction assigns it that reusable role.
Let structural publication rules and exact official content and formatting
govern the intended target. When portability, a generic convention, or
implementation convenience suggests an alternative, treat it as a reported
constraint or candidate user decision while preserving the evidenced target.

Before implementation, assign each observed item to exactly one owner:

- **author semantic** — content a new author is expected to supply or vary;
- **publication policy** — reusable behavior owned privately by the template;
- **official-fixture literal** — sample content specific to reproduction of the
  official instance; or
- **comparison-only exclusion** — non-public guidance or producer artifact that
  the user confirms is absent from authored/submitted output.

Let the public API contain the author-semantic set and the template internals
contain publication policy. Keep official-fixture literals in `usage.typ`.
Record every comparison-only exclusion and its exact masked region or object,
while keeping adjacent publication content visible in the comparison. Base any
reclassification on new source evidence or an explicit user decision.

For each exclusion, distinguish its visible ink or object, occupied layout
extent, and effect on surrounding and downstream flow. When editable source is
available and the excluded item participated in flow, create a clean reference
render with that item removed and compare the resulting natural reflow. For an
overlay, mask exactly its ink or object. Retain excluded space when separate
evidence assigns that space to publication policy.

## Core Workflow

For generated run artifacts, use one authoring root and one system-temporary
scratch root. The authoring root contains the current `template.typ`, official
`usage.typ`, consolidated `variation.typ`, required dependencies and assets,
their current PDFs, and one `critic-findings.md` file containing the latest
completed critic-to-builder findings; it remains visible throughout repair. The
scratch root
contains inspector and comparator output, probe copies, focused sources, logs,
and rejected or intermediate builds. Reuse that scratch root during the run,
creating a new or empty subdirectory there only when a tool requires one. At
completion, copy only decisive probe or comparison artifacts that support the
verified result or an individually user-accepted exception into one `evidence/`
directory in the authoring root. These two roots contain the complete generated
workspace. Use critic findings exclusively as internal repair input and keep the
task active until closure.
Maintain `<scratch>/router-cursor.yaml` with the exact record and transitions in
step 9.

1. **Collect mechanical evidence.** Inventory files, formats, page
   geometry, embedded fonts, and images; render editable sources with their
   established application or compiler to expose appearance and pagination.
2. **Map the top level.** Read
   [the element router](references/component-property-ledger.md) once. From the
   shallow pass, identify the wrapper, page roles, major containers, reading
   order, repeated regions, and author-editable slots. For each step, load the
   packet linked by the router for the single active branch; its detailed
   prompts become current when their parent context exists.
3. **Build and compile the skeleton.** Rank a named target-adjacent working
   Typst template or document above the bundled
   [`template.typ` + `usage.typ`](assets/scaffold/) starting pair as architecture
   evidence, and use the highest-ranked available structure. Copy that pair into
   the authoring root before adapting it. The bundled pair provides one public
   wrapper with a positional body and one private
   `_render_body(body) = body` hook. Replace that hook from target evidence when
   the body needs a different flow such as `columns(...)`. Keep page, column
   count, gutter, break, and flow policy private in the template; treat them as
   private body-container parameters owned by the template.
   Derive the target's semantic API, publication policy, content-dependent
   rules, and calibration, including fixed offsets, from the target structural
   and rendered evidence. Expose observed author slots and preserve their
   free-form content while keeping publication rules private. Start with the
   template, an official `usage.typ`, and one representative `variation.typ`.
   Populate the variation early with the ordinary authoring horizon so that
   architectural mistakes surface, while leaving each future element open until
   its own branch is examined. Reuse and extend these sources as the analytical
   focus changes. Select mutually exclusive document states from the same
   variation source through an input case. Use a temporary focused source under
   the scratch root to distinguish a causal ambiguity left unresolved by the
   consolidated manuscript, then carry any lasting diagnostic case into the
   consolidated variation rather than persisting a separate focused source.
   Establish page setup, major containers, and rough natural
   flow, then compile and immediately render the official instance plus the
   smallest public-API change in the consolidated variation that activates and
   distinguishes the current skeleton contract. This first pair precedes
   repeated geometry tuning and supplies early architectural feedback.
4. **Complete elements in dependency order.** Keep one hierarchy branch active.
   Open its packet after its `Requires` context exists and close it through its
   `Emits` and `Recheck` relations. Within a composite packet, keep one direct
   child active at a time and complete the children in reading order. Apply the
   Element Completion Loop to establish each active element's exact official
   content, semantic API, and first meaningful variation before geometry tuning.
   Keep that branch current until its router-cursor closure record contains the
   official, activating-variation, and packet `Recheck` observations required by
   step 9 below. Advance through every element on every reference page only from
   such a record. Reopen the earliest governing branch when a later observation
   invalidates one of its recorded relations.
5. **Deepen uncertain rules.** The element loop renders its first official and
   varied instances before geometry tuning. When that pair leaves competing
   inferences, temporarily isolate the minimal content or flow needed to
   distinguish them, then carry the rule selected by the observed difference and
   its activating case back to the primary documents.
6. **Compare hierarchically.** Run the all-page comparison, then use the
   [visual comparison playbook](references/validation-playbook.md) to inspect
   semantic regions, internal formation, downstream flow, and the last page.
7. **Repair causally.** For a mismatch recorded by step 9, state the reusable rule
   and signed change predicted to remove it. Test that prediction, then record
   the new parent, child, internal-formation, and downstream observations it can
   affect.
8. **Critique and refactor the author usage.** Each time step 9 closes an element
   and advances the router cursor, trigger the Author-Usage Critic Loop on the
   complete current authoring system. Let the critic inspect the whole current
   usage and implementation rather than a builder-selected branch. Start the next
   element branch while that critic runs. Route each returned finding to its
   earliest governing usage, element, parent, or user decision and retest it.

Request a user decision when source authority, intended semantics, edit scope,
or residual acceptance depends on it.

After a context compaction or resumed run, restore the North Star, router
cursor, active packet, and roughly the five most recent causal observations
before editing or judging completion. Resume the open branch at the first
closure field lacking a post-last-change observation or containing an
unaccepted mismatch. Advance only from the step 9 closure entry.

Record elapsed time as secondary evidence. First obtain complete step 9 closure
records, reusable author behavior, a final critic `CLEAR`, and a final builder
audit with no unaccepted mismatch. Profile that path afterward and shorten it
toward a roughly 30-minute workflow while preserving the same result and
observations.

## Element Completion Loop

Apply this loop to the active branch selected by the router. Attach each rule to
its semantic owner and close the branch through its packet relations.

Connect each active branch to the complete authoring system. Before changing it,
identify the author action or publication invariant it must support and the
upstream and downstream contracts it touches. After changing it, record its
local formation and its effect on those named upstream and downstream relations.
Treat pixel scores, elapsed time, compiled fixtures, and visited elements only
as auxiliary observations.

Treat each element as a semantic layout contract within its parent context.
Recover its purpose, author-facing boundary, invariant behavior under justified
content and flow changes, and ownership of governing rules. Use the current
branch packet to enumerate the relations to inspect. For every implemented rule,
identify its source evidence, Typst control, official observation, activating
author change, and observed varied result. A packet supplies the current
branch's questions while the router preserves the whole capability horizon.

The parent container establishes the child's coordinate system, available
width, inherited rules, and flow context. Interpret and tune child parameters
inside that established context. Typography is structural too: font face,
size, tracking, and line pitch change wrapping and element extent, which moves
downstream content. Therefore establish parents before children, close composite
parents after their children, and work earlier flow elements before later ones.

Complete the following observations for one active element before moving to the
next. Revisit an earlier element when later evidence invalidates its record:

1. **Parent context.** Establish the coordinate system, available width,
   inherited rules, flow context, sibling relationships, and downstream effects
   supplied by the established parent and earlier elements.
2. **Meaning, ownership, and author route.** State the element's semantic
   purpose, boundary, invariants, and one of the four owners above. For a
   standard document element, first write the ordinary Typst author syntax:
   headings, lists, equations, figures, tables, labels/references, citations,
   or bibliography as applicable. Put publication behavior in template
   `set`/`show` rules. Introduce a public helper when the source contains a
   genuine additional manuscript semantic beyond the standard route, and record
   that semantic and the standard route tested. Select the
   smallest author-controlled content or flow change that can distinguish its
   generative rule from an official-instance workaround. Include any
   project-specific element found in the source hierarchy.
   For prose references, exercise the ordinary standard reference route,
   normally `@label` and explicitly `#ref(<label>)` where a lexical boundary
   requires it. Let template-owned reference styling derive the target-kind
   prefix, punctuation, and numbering form; keep this distinct from caption
   supplements and verify equation, figure, and table prose separately.
3. **Official content.** Establish exact correspondence for the active element's
   wording, symbols, equations, assets, citations, order, and deliberate breaks.
4. **Activated variation.** Change one legitimate author input to distinguish
   the inferred rule. Before rendering, predict the visible event, the relations
   that change, and the relations that remain invariant. Increase or alter the
   semantic input and rerender the same case until that event appears. Observe
   it directly through multiple title baselines, sentinels crossing a page or
   column, table-row identifiers around a boundary and its repeated header, or
   the next normal anchor after optional-field omission. Record how the result
   affects the parent, neighbors, and downstream flow.
5. **Owned parameter bundle.** List the governing controls inferred from
   structural and rendered evidence. Assign each rule to the element whose
   semantics it governs, covering applicable typography, alignment, width/wrap,
   spacing, breaks, numbering, strokes, padding, markers, and asset treatment.
   When a source names a geometric relation, record its definition and
   endpoints, then map it to the Typst control that governs the same relation.
   Verify that relation at two repeated instances, or record the unique
   element's actual endpoints. Use those endpoints as the calibration target.
   Resolve evidenced font faces through the final compile environment and
   compare the source-backed candidates before recording a fallback cause. Load
   the Typst tips for consistent font paths and separate text/math routes.
6. **Generative implementation.** Express one contract for the official and
   varied instances with the selected ordinary Typst syntax, template-owned
   `set`/`show` rules, and natural flow. Use contextual measurement when local
   available space governs the result. Place reusable constants at their
   semantic owner and keep sample content semantic.
7. **Official local confirmation.** Compare the active official element against
   its source through exact text and symbols, math form, glyphs/fonts,
   widths/heights, padding, strokes/borders, and its relations to parent,
   neighbors, and following flow. Compare three relations separately: the
   element container's placement and extent within its parent; direct-child box
   placement, insets, alignment, spacing, and flow inside that container; and
   each child's internal formation. For prose, observe first, continuation, and
   final line edges, alignment, wrapping, line pitch, and indents. For structured
   children, observe shared edges, row/cell alignment, padding, wrapping, rules,
   and boundaries. Record a match or the exact mismatch for every applicable
   relation; a missing observation or unaccepted mismatch leaves the branch
   active.
8. **Varied route confirmation.** Record the author input changed, its actual
   call path, the predicted visible event and invariants, the observed semantic
   or rendered event, and downstream behavior.
9. **Branch closure and transition.** After the last branch edit, rerender the
   official case and its activating variation through the public author workflow.
   Update `<scratch>/router-cursor.yaml` in this shape:

```yaml
active:
  branch: ""
  packet: ""
  status: open
  last_change_recompiled: false
  official:
    source_regions: []
    output_regions: []
    container: ""
    direct_children: ""
    internal_formation: ""
    downstream: ""
  variation:
    author_edit: ""
    predicted_event: ""
    call_path: ""
    observed_event: ""
  rechecks: []
  child_closures: []
  unresolved_mismatches: []
  accepted_mismatches: []
closures: []
suspended: []
critic:
  state: idle
  refresh_pending: false
  unresolved_findings: []
```

   Every observation names both locations and the visible, extracted, or measured
   relation. Use `not_applicable: <reason>` only where justified; each accepted
   mismatch records the exact item and user decision. Apply these transitions:

| Guard or event | Required transition |
| --- | --- |
| A required field is empty, `last_change_recompiled` is false, or `unresolved_mismatches` is nonempty | Keep `active.status: open`; continue this branch. |
| Every required string and region list is populated, `last_change_recompiled` is true, `rechecks` records each packet relation, and `unresolved_mismatches` is empty | For a composite, also require every direct child in `child_closures` and a composition result in `rechecks`; set `active.status: closed`, append it to `closures`, create the next open `active` record in dependency/reading order, and trigger the critic. |
| A later observation contradicts a closure | Move the earliest governing entry from `closures` to `active`, set it open, and record the interrupted branch in `suspended`. |
| Source authority or acceptance is missing | Keep the branch open and request the user's decision. |

   Compilation, warnings, page count, visited files, and aggregate pixel
   scores cannot populate the relation fields. Resume a suspended branch at its
   first empty or contradicted field after the reopened branch closes again.

Request the user's decision when source authority or acceptance leaves a closure
field unresolved. Classify a difference as renderer-origin only after recording
matching content, semantics, font/glyph choice, formation, and layout relation.

For every claimed author route, trace author syntax to its expected output or
policy and its observed extracted or rendered output. Do this for standard
Typst routes as well as wrapper fields, including references and bibliography
entries.

## Author-Usage Critic Loop

Every branch closure triggers a review. Compile the official usage and all
current accepted variations from the live dependency set first. Start a fresh
maximum-reasoning subagent without conversation history. Pass the current
authoring sources, dependencies, assets, matching PDFs, a system-temporary
`TEMP_CRITIC_REPORT_PATH`, and
[`author-usage-critic.md`](references/author-usage-critic.md). Withhold the
builder diagnosis, intended answer, prior reports, notes, and rejected outputs.

| Critic state and event | Required transition |
| --- | --- |
| `idle` + branch closure | Set `loading`; start one fresh whole-artifact critic. |
| `loading` + `INPUTS_LOADED` | Set `running`; begin the next element and continue all-page fidelity work. |
| `loading` or `running` + another closure | Set `refresh_pending: true`; keep one critic. |
| `running` + completed report | Publish it atomically as `critic-findings.md`, set `idle`, and process its findings. |
| `idle` + pending refresh at the next transition | Clear `refresh_pending`; start a fresh review. |
| No fresh subagent slot | Preserve builder state, consult the user immediately, and await the decision. |

For each returned mechanism, retest the current live version. Close an
already-fixed finding only from that retest. Route a surviving finding to its
earliest governing usage, element, parent, or user decision. For an upstream or
whole-system finding, put the current `active` record in `suspended` and reopen
the governing branch; resume the suspended record after it recloses. Apply a
local finding after the current edit compiles or is reverted and before closure.

Use this handoff with the current paths:

```text
Act as a fresh, independent critic of the generated Typst authoring system.
Read CRITIC_GUIDE completely. Read every CURRENT_SOURCE_FILE and inspect every
page of every CURRENT_OUTPUT_PDF, then send INPUTS_LOADED. Keep them read-only.
Use system-temporary copies for adaptive probes. Review the whole supplied
authoring system using only these inputs. Write the guide's bounded report to
TEMP_CRITIC_REPORT_PATH and return its path and status.
```

Maintain an accumulated finding ledger in scratch and use a new fresh critic for
each review; intermediate `CLEAR` is repair input. After all closure entries are
valid and earlier findings resolved, process any active report, clear pending,
compile all accepted documents, and hold the live inputs unchanged. Run the
final fresh critic and builder's raw-source/all-page/variation audit concurrently.
Finish only with final `CLEAR`, no builder mismatch, and no unresolved ledger
item; otherwise reopen the earliest governing loop.

## Mechanical Evidence Helpers

Use the bundled inspector when it supports the input formats available. Pass it
the regular files from the closed evidence set and interpret its observation
inventory beside the structural sources and renders:

```bash
python3 <skill-dir>/scripts/inspect_evidence.py \
  <scratch>/inspect source.docx source.tex reference.pdf
```

For a user-named directory, enumerate the regular files physically contained in
that directory recursively. Treat a symlink target as additional evidence after
the user names it. Invoke the inspector with the resulting files, read extracted
text page by page beside the page render, and inspect the original source to
recover semantics and reading order.

Render Typst with the project's established command and font paths. Render DOCX
or other editable formats with the application that produced or officially
exports them when available. Record tool versions when renderer differences
might explain a residual.

Use the PDF comparator for disposable all-page evidence:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf <scratch>/scan --dpi 200

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  <scratch>/scan <scratch>/detail --finding <finding-id> --dpi 300
```

Here `<scratch>` is the run's single system-temporary scratch root. Prepare the
named subdirectory as new or empty when the helper requires it, and place all
such disposable trees in that scratch root.

Read `index.json`, page rasters, overlays, absolute differences, text diffs,
font inventories, bboxes, and projection/band measurements as complementary
signals. Compare the reference and candidate in their native page coordinates.
Choose crops from semantic elements and suspected causal boundaries, including
large pixel hotspots when they correspond to those regions.

Automate compile, render, extract, inventory, count, and observation of declared
activation events. Let the project choose its source/case layout. Use numeric
summaries and fixture results as inputs to Codex's integrated judgment of
semantic ownership, element completion, residual acceptance, and readiness.

Read [implementation patterns](references/implementation-patterns.md) when
content-dependent layout or ownership is unclear. Read the
[visual comparison playbook](references/validation-playbook.md) when a residual
needs focused diagnosis. These references supply implementation and diagnostic
guidance; the Element Completion Loop owns artifact choice and acceptance.

Load each short Typst engine tip when its named issue becomes active:

- [natural width versus wrapped extent](references/typst-tip-natural-width.md);
- [source baseline pitch versus Typst leading](references/typst-tip-line-pitch.md);
- [font resolution and separate text/math routes](references/typst-tip-font-resolution.md);
- [combined math accents](references/typst-tip-combined-accents.md);
- [localized standard references and CJK lexical boundaries](references/typst-tip-localized-references.md);
- [first-line indentation on injected prose](references/typst-tip-injected-paragraph.md).

These references supply reusable engine techniques. Derive target values and
publication policies from the source evidence.

## Judgment Guide

Use positive evidence to distinguish:

- author content from reusable template policy;
- fixed publication dimensions from content-dependent extents;
- deliberate line/page breaks from natural flow;
- font or glyph substitution from geometry drift;
- upstream container errors from downstream accumulated displacement;
- asset differences from layout differences;
- renderer-only raster differences from structural differences.

Classify a residual as renderer-only after exact content, semantic structure,
applicable font/glyph choice, line formation, strokes, and governing layout
rules agree. Use disagreement in any of those relations to continue causal
inspection.

Treat a uniform block displacement as evidence to inspect its shared
alignment, inset, or placement rule. Treat accumulating vertical drift as
evidence to inspect the earliest repeated line pitch or block spacing. Treat
matching text anchors with differing rules as evidence to inspect strokes.
Treat a wrong image extent as evidence to inspect its intrinsic asset, sizing,
fit, and container width. First inspect the implicated element and its parents;
then choose a repair from the semantic and structural evidence.

## Finish

Finish when a new author can create and revise representative manuscripts
through the semantic public API and standard Typst content, while the template
owns publication policy and expresses the inferred document semantics. The
official instance and justified variations must render robustly, every reference
page must be inspected, and each recorded mismatch must be repaired and retested
or individually accepted by the user. Apply the step 9 closure records and final
critic conditions below to decide readiness.

After the last change to the template, usage, asset, bibliography data, or style,
compile the official instance and every accepted variation from the current
source. Enter the final iteration of the Author-Usage Critic Loop: run the fresh
critic and the builder's raw-source, all-reference-page, all-varied-page, public
API, ownership, and render audit concurrently while those live files remain
unchanged.
Readiness requires official local fidelity, varied author behavior, and correct
API/ownership together. Route a material finding from either review back to the
earliest governing loop and continue through repair, retest, refreshed closure
records, and a new final review.

After every branch has a non-invalidated closure entry, the final critic reports
`CLEAR`, the final builder audit records no unaccepted mismatch, and the finding
ledger has no unresolved item, return the generated template, usage, variation,
and PDF paths with one sentence naming the compiled documents, inspected pages,
activated variations, and final critic status. Leave
regenerable bulk renders and superseded iterations in the system-temporary
scratch root. When unavailable source authority or a required user choice leaves
a closure field unresolved, consult the user and keep that branch active until
the decision is available.
