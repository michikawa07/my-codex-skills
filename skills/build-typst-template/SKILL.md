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
   [the element and parameter checklist](references/component-property-ledger.md)
   and use relevant branches in scratch notes. From the shallow pass, identify
   the wrapper, page roles, major containers, reading order, repeated regions,
   and author-editable slots. Map detailed elements and parameters when each
   becomes active.
3. **Build and compile the skeleton.** When the closed evidence includes a named
   working Typst template or document, use its standard-element plumbing and
   responsibility structure as architecture evidence. Derive the target's
   semantic API, publication policy, content-dependent rules, and calibration,
   including fixed offsets, from the target structural and rendered evidence.
   Expose observed author slots and preserve their free-form content while
   keeping publication rules private. Establish page setup, major containers,
   and rough natural flow, then compile. This first Typst compile precedes deep
   inspection of later elements or pages and creates an early feedback point;
   it is not evidence of fidelity or completion by itself.
4. **Complete elements in dependency order.** Keep one hierarchy branch active.
   Establish a composite parent's contract enough to define its children,
   complete those children in reading order, and then close the parent contract;
   work upstream before downstream through page, containers, frontmatter,
   paragraphs/headings, lists/equations, figures/tables, and references.
   Establish each active element's exact official content and semantic API
   before geometry tuning. Continue through every reference page.
5. **Challenge uncertain rules.** First render the official content. Then make
   focused temporary examples that vary only the content or flow needed to test
   an inference, such as a wrapping title, a page-crossing list, or a long
   bibliography. Retain a project fixture in proportion to its demonstrated use.
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
content and flow changes, and ownership of governing rules. Use checklist
branches to surface questions; let source and render evidence determine the
actual contract and its coherent parameter bundle. The target is a positive
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
   author-editable fields, template-owned policy, and invariants. Include any
   project-specific element the checklist does not name.
3. **Official content.** Establish exact correspondence for the active element's
   wording, symbols, equations, assets, citations, order, and deliberate breaks.
4. **Owned parameter bundle.** Infer a coherent governing bundle from structural
   and rendered evidence. Assign each rule to the element whose semantics it
   governs, covering applicable typography, alignment, width/wrap, spacing,
   breaks, numbering, strokes, padding, markers, and asset treatment.
5. **Generative implementation.** Express the contract with standard Typst
   semantics, `set`/`show` rules, and natural flow. Use contextual measurement
   when local available space governs the result, and place reusable constants
   at their semantic owner rather than compensating in sample content.
6. **Focused confirmation.** Compare the local target through exact content,
   its crop, bboxes, fonts, line formation, and relation to its parent,
   preceding sibling, and following flow. Use the earliest governing rule to
   explain related residuals.
7. **Minimal variation.** Exercise the smallest meaningful content or flow
   change. Confirm what remains invariant, what changes, and that the author did
   not need layout-only arguments or special sample markup.
8. **Regression and completion.** Rerender through the public author workflow
   and recheck the parent, completed neighbors, and affected document-wide flow.
   When one coherent contract explains the official instance and variation,
   complete the element and advance in hierarchy and reading order. Reopen it
   when later evidence refines an upstream rule.

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
