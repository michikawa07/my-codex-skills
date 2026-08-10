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
critic-to-builder findings. The scratch root contains inspector and comparator
output, probe copies, focused sources, logs, and rejected or intermediate
builds. Reuse that scratch root during the run,
creating a new or empty subdirectory there only when a tool requires one. At
completion, copy only decisive probe or comparison artifacts that support the
verified result or an individually user-accepted exception into one `evidence/`
directory in the authoring root. These two roots contain the complete generated
workspace. Use critic findings exclusively as internal repair input and keep the
task active until closure.

1. **Collect mechanical evidence.** Inventory files, hashes, formats, page
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
   Keep that branch current until paired renders support its official local
   observation, activating variation observation, and applicable packet
   `Recheck` relations; record those observations, then advance through every
   element on every reference page. Reopen the earliest governing branch when
   later evidence refines an upstream contract.
5. **Deepen uncertain rules.** The element loop renders its first official and
   varied instances before geometry tuning. When that pair leaves competing
   inferences, temporarily isolate the minimal content or flow needed to
   distinguish them, then carry the supported rule and activating case back to
   the primary documents.
6. **Compare hierarchically.** Run the all-page comparison, then use the
   [visual comparison playbook](references/validation-playbook.md) to inspect
   semantic regions, internal formation, downstream flow, and the last page.
7. **Repair causally.** State the reusable rule and signed change predicted to
   explain a material residual. Use the visual comparison playbook to test that
   hypothesis and recheck its affected scope.
8. **Critique and refactor the author usage.** After the element and fidelity
   loop produces a coherent candidate, compile its current sources and run the
   Author-Usage Critic Loop directly on those sources and PDFs. Preserve the
   established render while addressing supported usage findings. When a finding
   exposes a flawed element contract rather than a local source-structure
   problem, reopen the earliest governing element branch and repeat this outer
   candidate loop.

Request a user decision when source authority, intended semantics, edit scope,
or residual acceptance depends on it.

After a context compaction or resumed run, restore the North Star, router
cursor, active packet, and roughly the five most recent causal observations
before editing or judging completion. Resume the open branch at its first
unsupported closure relation, and advance the cursor from supported branch
closure evidence.

Record elapsed time as secondary evidence. First obtain exact official fidelity,
reusable author behavior, and an independent acceptance covering every material
residual decision. Profile that accepted path afterward and shorten it toward a
roughly 30-minute workflow while preserving the same result and evidence.

## Element Completion Loop

Apply this loop to the active branch selected by the router. Attach each rule to
its semantic owner and close the branch through its packet relations.

Connect each active branch to the complete authoring system. Before changing it,
identify the author action or publication invariant it must support and the
upstream and downstream contracts it touches. After changing it, judge its
focused evidence and its contribution to the usable whole. Use pixel scores,
elapsed time, compiled fixtures, and visited elements as observations within
that causal and document-level judgment.

Treat each element as a semantic layout contract within its parent context.
Recover its purpose, author-facing boundary, invariant behavior under justified
content and flow changes, and ownership of governing rules. Use the current
branch packet to surface questions; let source and render evidence determine
the actual contract and its coherent parameter bundle. A packet supplies the
current branch's questions while the router preserves the whole capability
horizon. Derive a positive rule that generates the official instance and
justified variations, then confirm it through semantic output, local formation,
and affected document flow.

The parent container establishes the child's coordinate system, available
width, inherited rules, and flow context. Interpret and tune child parameters
inside that established context. Typography is structural too: font face,
size, tracking, and line pitch change wrapping and element extent, which moves
downstream content. Therefore establish parents before children, close composite
parents after their children, and work earlier flow elements before later ones.

Raise one active element from a rough implementation to a supported semantic
contract before moving to the next. Follow this order, revisiting an earlier
view when later evidence refines it:

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
5. **Owned parameter bundle.** Infer a coherent governing bundle from structural
   and rendered evidence. Assign each rule to the element whose semantics it
   governs, covering applicable typography, alignment, width/wrap, spacing,
   breaks, numbering, strokes, padding, markers, and asset treatment.
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
   and boundaries. Require agreement in all applicable relations.
8. **Varied route confirmation.** Confirm the declared activating observation,
   the predicted invariant/change, standard author syntax, ownership boundary,
   and downstream behavior. Trace the actual author input through the template
   to its extracted and rendered output.
9. **Branch closure.** Rerender both cases through the public author workflow
   and recheck the parent, completed children and neighbors, and affected
   document-wide flow. A leaf closes after official local confirmation and
   varied route confirmation hold under one coherent contract. Close a
   composite parent after its supported children are closed and their
   composition preserves the parent contract. Then advance in hierarchy and
   reading order; reopen the branch when later evidence refines an upstream
   rule.

Complete an element when an author can use its standard input route and vary its
content while the rendered result follows the evidenced publication rule. Check
the exact official content and appearance, placement and extent within the
parent, direct-child placement/insets/alignment/spacing/flow inside the
container, internal line or cell formation, neighboring spacing, and affected
column/page flow. Confirm the relevant variation through the same public route.
Keep the branch active for each material local or semantic mismatch, including
bibliography field order or punctuation and equation placement. Advance when
the target is supported or the user accepts that specific residual. Request the
user's decision when source authority or acceptance requires it. Classify a
renderer-origin residual after its content, semantics, fonts, formation, and
governing layout rule agree.

For every claimed author route, trace author syntax to its expected output or
policy and its observed extracted or rendered output. Do this for standard
Typst routes as well as wrapper fields, including references and bibliography
entries.

## Author-Usage Critic Loop

Run this loop after the element and fidelity loop reaches a coherent candidate.
Compile the latest official usage and accepted variations, then pause candidate
edits while the critic reads those current source files and their matching PDFs.

Start one fresh subagent without inherited conversation context and with maximum
reasoning effort. Give it only the latest official and varied author sources,
the template and dependencies needed to understand them, their matching output
PDFs, the exact authoring-root path `CRITIC_FINDINGS_PATH` for
`critic-findings.md`, and the critic guide
[`author-usage-critic.md`](references/author-usage-critic.md). Withhold the
builder's diagnosis, intended answer, prior findings, working notes, rejected
candidates, and conversation history. Instruct the critic to read that file
completely, judge the current result as a new author, choose implementation-
specific probes, and remain read-only on the supplied sources and PDFs. The
critic may create its own system temporary directory for a probe, copying only
the dependencies needed for that probe. Before starting each fresh critic,
remove the previous `critic-findings.md` so it cannot reveal earlier findings.
The critic writes its complete structured findings only to
`CRITIC_FINDINGS_PATH`; the builder reads that file and acts on it. Use this
authoring-root file as the sole persistent critic output.

Use this handoff, filling in the current paths:

```text
Act as a fresh, independent critic of the generated Typst authoring system.
Read CRITIC_GUIDE completely. Review CURRENT_SOURCE_FILES and their matching
CURRENT_OUTPUT_PDFS directly as a new author who did not participate in their
construction. Keep them read-only. If an adaptive compile probe is needed, copy
only the minimum required source dependencies into a system temporary directory
and run the probe there.

Write the complete required findings document to CRITIC_FINDINGS_PATH. Outside
your system temporary probe directory, write only that file. In your final
response, return its path and overall status to the builder.

Restrict review context to CRITIC_GUIDE, CURRENT_SOURCE_FILES,
CURRENT_OUTPUT_PDFS, and probe copies created in the system temporary directory.
Choose probes that expose the actual implementation rather than merely matching
names from the historical examples.

For every material finding, report the exact artifact location, author action,
probe or call trace, observed consequence, authoring-system harm, earliest
governing element or ownership boundary, smallest repair direction, and exact
retest. Treat compilation, page count, hashes, and aggregate pixel scores as
prerequisites or observations. Base substantive author-usage conclusions on the
author action, route trace, and observed semantic or rendered consequence.
```

Require artifact locations, author actions, executed probes or call traces, and
observed consequences for every material finding. Route each supported finding
to a local usage refactor, the earliest governing element or parent, or a user
decision. Reproduce decisive evidence before deciding whether to accept a
finding.

Maintain an accumulated finding ledger. After every repair, rerender the
affected official and varied cases. Any change to a reviewed source, dependency,
or output PDF invalidates the previous findings file; use a new fresh critic on
the new current files. Close the current iteration only when the latest findings
file is `CLEAR` and every earlier material or blocked ledger item is repaired
and retested or otherwise resolved, or when every such item is individually
accepted or otherwise resolved by the user. An unaccepted `REVISE` or `BLOCKED`
leaves the loop open. Treat `CLEAR` as scoped to the inspected current files and
executed probes. If no fresh subagent slot is available, consult the user
immediately and keep the builder paused until the user decides how to proceed.

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

Treat a coherent block displacement as evidence to inspect its shared
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
page must be inspected, and each material residual must be repaired and retested
or individually accepted by the user. Base readiness on that integrated
evidence-based judgment.

After the last change to the template, usage, asset, bibliography data, or style,
compile the official instance and every accepted variation from the current
source. Run the Author-Usage Critic Loop directly on those source files and their
matching PDFs. Keep them unchanged while the critic reads them; if any reviewed
source or PDF changes, discard that findings file and run a new fresh critic.

Then perform the separate final audit from the raw sources, all reference pages,
all varied pages, the public template/usage source, and those same current
outputs. Keep the candidate unchanged through both reviews; any change
invalidates both and requires a new final build and critic. Combine the
critic's raw observations with the source and render audit. Readiness requires
official local fidelity, varied author behavior, and correct API/ownership
together. If this audit or the critic exposes a material failure, route it back
to the earliest governing loop and continue through repair and retest.

After all completion conditions close, return the paths to the generated
template, usage, variation, and PDFs with a concise statement of the validation
completed. Leave regenerable bulk renders and superseded iterations in the
system-temporary scratch root. When unavailable source authority or a required
user choice prevents closure, consult the user at that point and keep the loop
open until the decision is available.
