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

Inventory that set before editing. Inspect every named source and every page of
each reference. When sources disagree about a reusable rule, identify the exact
conflict and ask the user which source governs. Treat file metadata, extracted
text, XML properties, bboxes, and pixels as observations; infer their meaning by
reading the structural source together with the rendered document.

## Core Workflow

1. **Collect mechanical evidence.** First inventory files, hashes, editable
   structure, text, page geometry, embedded fonts, and page images. Then render
   editable sources with their established application or compiler so their
   intended appearance and pagination are visible.
2. **Establish content correspondence.** First compare meaningful wording,
   symbols, equations, images, tables, citations, order, and explicit breaks.
   Then correct content differences before using geometry to tune layout.
3. **Map the actual document.** Read
   [the element and parameter checklist](references/component-property-ledger.md)
   and use relevant branches in scratch notes. First identify the hierarchy and
   semantic role of each observed element; then inspect applicable parameters
   and add any project-specific element the checklist does not name.
4. **Design from evidence.** First identify author-editable semantic slots and
   repeated publication rules; then choose an API that exposes the former and
   keeps the latter private. Preserve free-form content when the source exposes
   it. Keep sample wording and one-off visual compensation out of the API.
5. **Implement in dependency order.** Start with page geometry and fonts, then
   containers and flow, frontmatter, paragraphs and headings, lists/equations,
   figures/tables, and references. Prefer standard Typst elements and `set` or
   `show` rules. Choose `context`, `layout`, or `measure` when behavior depends
   on available space; add a helper only for an evidenced repeated semantic
   gap; add a library only when a remaining requirement justifies it.
6. **Challenge uncertain rules.** First render the official content. Then make
   focused temporary examples that vary only the content or flow needed to test
   an inference, such as a wrapping title, a page-crossing list, or a long
   bibliography. Keep a useful project fixture when the project warrants it;
   do not require a fixture family, manifest, schema, or gate.
7. **Compare hierarchically.** First compare page count, page boxes, content,
   fonts, and whole-page alignment. Then inspect the riskiest elements with
   crops, overlays, diffs, text/image bboxes, and high-resolution rasterization.
   Finally inspect downstream flow and the last page. Measurements locate and
   quantify differences; Codex decides their meaning and importance.
8. **Repair causally.** First state which reusable rule should explain a
   material residual and predict the direction of change. Then change the
   smallest governing rule, rerender the affected example, and check whether
   the prediction held. Reinspect every affected downstream page and relevant
   variation; revise the hypothesis when it did not hold.

Use fresh output directories so stale artifacts cannot appear current. Ask the
user only when source authority, intended semantics, edit scope, or acceptable
residuals require their decision.

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
