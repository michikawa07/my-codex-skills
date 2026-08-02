---
name: build-typst-template
description: Build, reconstruct, or harden a reusable Typst document template from project-specific DOCX, PDF, TeX/LaTeX, or Typst evidence. Use when Codex must infer an author-facing API and layout rules from supplied publication sources, reproduce a reference document across its pages, or diagnose and repair template drift through structural and visual inspection.
---

# Build Typst Template

Reconstruct the document system evidenced by the project. Let Codex judge the
document semantics, relevant parameters, public API, Typst implementation,
visual differences, repairs, and readiness. Use automation only to expose facts
that make those judgments faster.

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
3. **Build and compile the skeleton.** Expose observed author slots and preserve
   their free-form content while keeping publication rules private. Establish
   page setup, major containers, and rough natural flow, then compile. This first
   Typst compile precedes deep inspection of later elements or pages.
4. **Complete elements in dependency order.** Work on one active element at a
   time, parent before child and upstream before downstream: page, containers,
   frontmatter, paragraphs/headings, lists/equations, figures/tables, and
   references. Establish its exact official content and semantic API before
   geometry tuning. Continue through the full hierarchy and every reference page.
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

Use the document hierarchy and semantic elements as the unit of progress. Attach
each parameter inventory to its owning element; complete it before advancing.

The parent container establishes the child's coordinate system, available
width, inherited rules, and flow context. Interpret and tune child parameters
inside that established context. Typography is structural too: font face,
size, tracking, and line pitch change wrapping and element extent, which moves
downstream content. Therefore complete parents before children and earlier flow
elements before later ones.

For one element at a time:

1. Mark its semantic boundary, role, and author-facing content or API, including
   any project-specific element the checklist does not name.
2. Establish exact content correspondence for that element by comparing its
   official wording, symbols, equations, images, tables, citations, order, and
   explicit breaks. Resolve semantic differences before geometry tuning.
3. Select the positive evidence target and collect its applicable parameter
   bundle: typography, alignment, width/wrap, spacing, break behavior, and any
   element-specific strokes, numbering, padding, or asset behavior.
4. Implement that bundle with standard Typst elements, `set`/`show` rules, and
   natural flow; use contextual measurement when the result depends on local
   available space.
5. Compare the focused element using its crop plus relevant bboxes, fonts, line
   breaks, and relation to the parent and immediately preceding element.
6. Exercise the smallest content variation that challenges the inferred rule,
   then recheck the parent and previously completed neighbor for regression.
7. When the evidence supports completion, lock the governing reusable rule and
   advance in hierarchy and reading order.

Element completion is Codex's evidence-based judgment, not a numeric gate. It
means the semantic author API is correct, the local visual target is matched,
parent and neighbor relations are correct, a relevant content variation is
stable, and standard Typst semantics remain intact. Residual classification
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

Finish when the template expresses the inferred document semantics, the public
API contains only justified author choices, representative content renders
robustly, every reference page has been inspected, and each material residual
has an understood cause and scope. This is Codex's evidence-based judgment, not
the result of a machine threshold.

Report the evidence used, API and implementation choices, render commands,
pages and focused regions inspected, causal repairs tested, remaining residuals
and their likely causes, and any decision still needed from the user. Preserve
the user's final authority to accept the result.
