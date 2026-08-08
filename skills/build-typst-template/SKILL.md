---
name: build-typst-template
description: Build, reconstruct, or harden a reusable Typst document template from project-specific DOCX, PDF, TeX/LaTeX, or Typst evidence. Use when Codex must infer an author-facing API and layout rules from supplied publication sources, reproduce a reference document across its pages, or diagnose and repair template drift through structural and visual inspection.
---

# Build Typst Template

Reconstruct the document system evidenced by the project. Let Codex judge the
document semantics, relevant parameters, public API, Typst implementation,
visual differences, repairs, and readiness. Use automation only to expose facts
that make those judgments faster.

## North Star

Port the publication format as an authoring system that a new author can use
without learning the source template's layout machinery. The Typst template
owns publication policy; its user supplies ordinary semantic document content
through a small justified API and standard Typst elements. The system must
reproduce the official instance and remain coherent when realistic titles,
authors, paragraphs, lists, equations, figures, tables, citations, references,
and page flow change. The official sample is necessary evidence for that port,
not the whole deliverable.

Treat every inspection, compile, crop, difference, fixture, and element loop as
evidence or a bounded subproblem serving this document-level objective. A local
metric or completed procedure is progress only when it improves the inferred
authoring system without shifting layout knowledge into sample content or
breaking the rest of the document. Reconnect each local decision to the author
workflow, template-owned rule, and document-wide behavior it is meant to secure.

## Bound the Evidence

Define evidence as every user-named file plus every regular file recursively
contained in a user-named directory. Calibrate only from that closed set. Add a
parent, sibling, prior output, or symlink target only when the user names it.

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
value, surface the conflict and governing sources instead of replacing the rule
with a nearby calibration.

Promote a choice to a template default, public API, or document semantic when
the closed evidence or explicit user direction assigns it that reusable role.
Let structural publication rules and exact official content and formatting
govern the intended target. When portability, a generic convention, or
implementation convenience suggests an alternative, treat it as a reported
constraint or candidate user decision while preserving the evidenced target.
Keep literal one-off guidance in the official fixture; expose it through the API
when evidence identifies a recurring author-controlled semantic field.

## Core Workflow

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
   the fresh output before adapting it. The bundled pair provides one public
   wrapper with a positional body and one private
   `_render_body(body) = body` hook. Replace that hook from target evidence when
   the body needs a different flow such as `columns(...)`. Keep page, column
   count, gutter, break, and flow policy private in the template; treat them as
   body-container parameters rather than scaffold variants or author controls.
   Derive the target's semantic API, publication policy, content-dependent
   rules, and calibration, including fixed offsets, from the target structural
   and rendered evidence. Expose observed author slots and preserve their
   free-form content while keeping publication rules private. Establish page
   setup, major containers, and rough natural flow, then compile and immediately
   render the official instance plus the smallest public-API variation that
   activates and distinguishes the current skeleton contract. Later elements
   receive their own variations when they become active. This first pair
   precedes repeated geometry tuning and creates
   an early feedback point; it is not evidence of fidelity or completion by
   itself.
4. **Complete elements in dependency order.** Keep one hierarchy branch active.
   Open its packet after its `Requires` context exists and close it through
   its `Emits` and `Recheck` relations. Within a composite packet, keep one
   direct child active at a time in the packet's route. Reopen the earliest
   governing packet when later evidence changes an upstream contract.
   Establish a composite parent's contract enough to define its children,
   complete those children in reading order, and then close the parent contract;
   work upstream before downstream through page, containers, frontmatter,
   paragraphs/headings, lists/equations, figures/tables, and references.
   Use the Element Completion Loop below to establish each active element's
   official content, semantic API, and first meaningful variation before
   geometry tuning. Close each branch from paired evidence, then continue
   through every reference page.
5. **Deepen uncertain rules.** The element loop renders its first official and
   varied instances before geometry tuning. When that pair leaves competing
   inferences, add a focused temporary example that varies only the content or
   flow needed to distinguish them. Retain a project fixture in proportion to
   its demonstrated use.
6. **Compare hierarchically.** First compare page count, page boxes, content,
   fonts, and whole-page alignment. Then inspect the riskiest elements with
   crops, overlays, diffs, text/image bboxes, and high-resolution rasterization.
   Finally inspect downstream flow and the last page. Measurements locate and
   quantify differences; Codex decides their meaning and importance.
7. **Repair causally.** First state which reusable rule should explain a
   material residual and predict the direction of change. Then change the
   smallest governing rule, rerender the affected example, and check whether
   the prediction held. Reinspect every affected downstream page and relevant
   variation; revise the hypothesis when it did not hold.

Use fresh output directories so stale artifacts cannot appear current. Ask the
user only when source authority, intended semantics, edit scope, or acceptable
residuals require their decision.

For a roughly 30-minute optimization, note elapsed time at the first activating
pair and final paired closure. When a run exceeds the target, identify its
longest avoidable interval and change that part of the next run; time informs
prioritization, not acceptance.

## Element Completion Loop

Use the document hierarchy and semantic elements as the unit of progress. Keep
one branch active and attach each rule to its semantic owner. A composite parent
can remain open while its children are completed; close it before moving to an
unrelated branch.

Each active branch is a nested part of the complete authoring system, not an
independent optimization target. Before changing it, identify the author action
or publication invariant it must support and the upstream and downstream
contracts it touches. After changing it, judge both its focused evidence and its
contribution to the usable whole. Pixel scores, elapsed time, number of compiled
fixtures, and number of visited elements describe observations; none substitutes
for that causal and document-level judgment.

Treat each element as a semantic layout contract within its parent context.
Recover its purpose, author-facing boundary, invariant behavior under justified
content and flow changes, and ownership of governing rules. Use the current
branch packet to surface questions; let source and render evidence determine
the actual contract and its coherent parameter bundle. A packet supplies the
current branch's questions while the router preserves the whole capability
horizon. The target is a positive
rule that generates both the official instance and justified variations;
compilation, avoided failures, or a small undifferentiated pixel residual alone
cannot establish that rule.

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
2. **Meaning and API.** State the element's semantic purpose, boundary,
   author-editable fields, template-owned policy, and invariants. Select the
   smallest author-controlled content or flow change that can distinguish its
   generative rule from an official-instance workaround. Include any
   project-specific element the checklist does not name.
3. **Official content.** Establish exact correspondence for the active element's
   wording, symbols, equations, assets, citations, order, and deliberate breaks.
4. **Early variation.** Materialize the selected change through the public
   author workflow and render it before parameter or geometry tuning. Predict
   what remains invariant, what changes, and how both cases affect the parent,
   neighbors, and downstream flow.
5. **Owned parameter bundle.** Infer a coherent governing bundle from structural
   and rendered evidence. Assign each rule to the element whose semantics it
   governs, covering applicable typography, alignment, width/wrap, spacing,
   breaks, numbering, strokes, padding, markers, and asset treatment.
6. **Generative implementation.** Express one contract for the official and
   varied instances with standard Typst semantics, `set`/`show` rules, and
   natural flow. Use contextual measurement when local available space governs
   the result. Place reusable constants at their semantic owner rather than
   compensating in sample content.
7. **Paired confirmation.** Compare the official local target and the varied
   case through exact content, crops, bboxes, fonts, line formation, and their
   relations to parent, neighbors, and following flow. Confirm the predicted
   invariant or change, including that the variation activates its intended
   branch, and use the earliest governing rule to explain residuals.
8. **Branch closure.** Rerender both cases through the public author workflow
   and recheck the parent, completed children and neighbors, and affected
   document-wide flow. Close a leaf when one coherent contract explains both
   cases. Close a composite parent after its supported children are closed and
   their composition preserves the parent contract. Then advance in hierarchy
   and reading order; reopen the branch when later evidence refines an upstream
   rule.

Element completion is Codex's evidence-based judgment, not a numeric gate. It
means the semantic purpose, API, invariants, and rule ownership are expressed
correctly; the official content and local visual target match; parent and
neighbor relations survive a relevant variation; and standard Typst semantics
remain intact. Residual classification
identifies a cause and repair hypothesis; it does not itself establish
acceptance. Keep the element active while a material local visual or semantic
target remains mismatched, including bibliography field order or punctuation
and equation placement. Advance only when evidence supports the target or the
user explicitly accepts that specific residual. Ask the user only when source
authority or acceptance actually requires their decision; a renderer-origin
diagnosis alone leaves the residual unaccepted.

For every claimed author route, trace author syntax to its expected output or
policy and its observed extracted or rendered output. Do this for standard
Typst routes as well as wrapper fields, including references and bibliography
entries.

## Mechanical Evidence Helpers

Use the bundled inspector when it supports the input formats available. Pass it
the regular files from the closed evidence set; it records observations rather
than a specification:

```bash
python3 <skill-dir>/scripts/inspect_evidence.py \
  audit/inspect source.docx source.tex reference.pdf
```

For a user-named directory, enumerate its regular files recursively without
following symlinks before invoking a version of the inspector that accepts only
files. Read extracted text page by page beside the page render. Inspect the
original source as well; extraction can omit semantics or reorder content.

Render Typst with the project's established command and font paths. Render DOCX
or other editable formats with the application that produced or officially
exports them when available. Record tool versions when renderer differences
might explain a residual.

Use the PDF comparator for disposable all-page evidence:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf audit/scan --dpi 200

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/scan audit/detail --finding <finding-id> --dpi 300
```

Read `index.json`, page rasters, overlays, absolute differences, text diffs,
font inventories, bboxes, and projection/band measurements as complementary
signals. Do not register or rescale the candidate into agreement. Choose crops
from semantic elements and suspected causal boundaries, not merely the largest
pixel hotspot.

Read [implementation patterns](references/implementation-patterns.md) when
content-dependent layout or ownership is unclear. Read the
[visual comparison playbook](references/validation-playbook.md) when a residual
needs focused diagnosis. Neither reference defines a required artifact or
acceptance gate.

## Judgment Guide

Use positive evidence to distinguish:

- author content from reusable template policy;
- fixed publication dimensions from content-dependent extents;
- deliberate line/page breaks from natural flow;
- font or glyph substitution from geometry drift;
- upstream container errors from downstream accumulated displacement;
- asset differences from layout differences;
- renderer-only raster differences from structural differences.

Classify a residual as renderer-only after the direct rules and semantic output
agree; otherwise use the disagreement to continue causal inspection.

Treat a coherent block displacement as evidence to inspect its shared
alignment, inset, or placement rule. Treat accumulating vertical drift as
evidence to inspect the earliest repeated line pitch or block spacing. Treat
matching text anchors with differing rules as evidence to inspect strokes.
Treat a wrong image extent as evidence to inspect its intrinsic asset, sizing,
fit, and container width. First inspect the implicated element and its parents;
then choose a repair from the semantic and structural evidence.

## Finish and Report

Finish when a new author can create and revise representative manuscripts
through the semantic public API and standard Typst content, while the template
owns publication policy and expresses the inferred document semantics. The
official instance and justified variations must render robustly, every reference
page must be inspected, and each material residual must have an understood cause
and scope. This is Codex's evidence-based judgment, not the result of a machine
threshold.

Report the evidence used, API and implementation choices, render commands,
pages and focused regions inspected, causal repairs tested, remaining residuals
and their likely causes, and any decision still needed from the user. Preserve
the user's final authority to accept the result.
