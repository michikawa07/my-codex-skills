---
name: build-typst-template
description: Build, reconstruct, or harden a reusable Typst document template from project-specific DOCX, PDF, TeX/LaTeX, or Typst evidence. Use when Codex must derive an author-facing API from the supplied publication structure, reproduce an official sample across every page, separate author choices from layout machinery, or diagnose template drift with focused fixtures and hierarchical PDF comparison.
---

# Build Typst Template

Reconstruct the document system evidenced by the project. Do not force projects
into one metadata model, wrapper name, capability list, or acceptance profile.

## Working Contract

Keep three responsibilities separate:

| Responsibility | Owner |
|---|---|
| Choose authoritative inputs, edit scope, and accepted residuals | user |
| Infer semantics, design the project API, implement rules, classify residuals | Codex |
| Extract facts, compile declared fixtures, lint source boundaries, compare PDFs | bundled scripts |

Automation reports observations and failed declared checks. It does not decide
source authority, API meaning, visual acceptability, or project completion.

## Minimal Workflow

1. Inspect every user-named source before designing the API.
2. Lock the official fixture content to the reference.
3. Derive the public API from structural evidence.
4. Implement document rules while keeping author choices in usage files.
5. Maintain exactly three project-declared success fixtures: official,
   frontmatter variation, and body-flow variation.
6. Compile all three, scan every official page, and inspect risk-ranked details.
7. Change a reusable rule, rerun affected fixtures, then rerun all three.
8. Report evidence, residual causes, and any decision still required from the
   user.

Use fresh output directories so stale PDFs or scans cannot masquerade as current
results.

## Inspect and Lock Evidence

Run the evidence inspector before editing the official fixture:

```bash
python3 <skill-dir>/scripts/inspect_evidence.py \
  audit/inspect source.docx source.tex reference.pdf
```

It records hashes and format facts. For PDFs it also records every page's
geometry, embedded font names, and page-separated extracted text. Read the text
files against the rendered reference page by page. Extraction is a checklist,
not a semantic or visual oracle.

Apply these positive authority rules:

| Evidence | Positive use |
|---|---|
| Written publication rule | implement the stated normative property |
| Editable DOCX, TeX, or Typst source | derive structure and authoring semantics |
| Export from the intended authoring application | calibrate appearance and pagination |
| Repeated behavior | formulate and vary one reusable rule |
| Behavior seen once | retain as a hypothesis until a relevant variation supports it |

If two authoritative inputs prescribe different values for the same reusable
property, name that property and ask which governs. Different file formats,
producer names, or candidate omissions do not themselves establish a conflict.

Transcribe the official sample's meaningful text, explicit breaks, equations,
tables, captions, references, notes, symbols, and intentional spelling exactly.
Do not tune the reference text to make the candidate pass. Compare layout only
after the official fixture is content-equivalent.

## Derive the Public API From This Project

Before implementation, read
[references/component-property-ledger.md](references/component-property-ledger.md)
and create that element-by-element ledger in the work log. Enumerate the known
frontmatter/body/structural roles in reference reading order, add roles the
project actually contains, and mark a known role absent only after verifying its
absence. Resolve every applicable typography, alignment, width/wrap, spacing,
break, numbering/stroke/padding, flow, evidence, target, author-syntax,
implementation, crop/anchor, and variation field before implementing it. The
eight broad categories are not an adequate reconstruction specification.

Follow the ledger's implementation ladder: standard Typst rules/elements first,
then contextual measurement for content dependence, then a local helper for an
evidenced repeated semantic gap, and an external library only for a documented
remaining requirement with a recorded dependency benefit. Select it from the
positive semantic/property requirement; a pixel residual supplies a measurement
target, not a technology choice. Match page/fonts, each frontmatter
element, body/headings, equations, figures/tables, and references in dependency
order, validating each element's crop/measurement before full-page integration.

Add a public argument only when an editable source or written rule exposes an
author-editable semantic slot. Derive its name, shape, and optionality from that
evidence. Preserve free-form content when the source exposes free-form content;
do not invent records merely because another publication used them.

Also inventory citations and the reference list in the structural source. When
they occur:

- create a project bibliography data file from those entries;
- cite with Typst's standard `@key` or `cite` semantics and render with
  `bibliography` rather than a hand-formatted list;
- use a built-in bibliography style when it can reproduce the reference;
- create a project style asset only when positive reference evidence shows that
  built-in styling cannot do so, and record that evidence in the work log.

Declare the data file, and the style asset if one is genuinely required, in
`checks.json`. Exercise citation and bibliography consumption in the existing
official and body-flow fixtures; do not add a bibliography fixture family.

Apply these interface rules:

- Style ordinary headings, figures, tables, equations, lists, labels, and
  references through standard Typst elements.
- Use one project-named document wrapper when the source has a document-level
  metadata and layout boundary.
- Add a helper only for a project-specific semantic structure that standard
  Typst does not express clearly or that repeats with the same meaning.
- Keep deliberate line breaks, table column widths, selected assets, and other
  author content choices in fixtures.
- Keep typography, measured spacing, caption behavior, pagination policy, and
  overflow handling in the template.
- Keep sample wording and one-off visual compensation out of the public API.
- Do not expose placement or continuation switches whose only purpose is to
  reproduce one sample.

Read [references/implementation-patterns.md](references/implementation-patterns.md)
before implementing content-dependent layout.

## Classify Layout Ownership

After the first fixture run, read the line-evidenced `source_inventory` for the
template and all three fixtures. Classify every reported spacing, font,
placement, break, layout construct, and absolute dimension in the work log:

```text
path:line | observed source | semantic owner | evidence | action
```

Use `author content`, `template policy`, `one-off compensation`, or `unresolved`
as the owner. An author-selected asset size, table width, or deliberate break is
allowed when structural evidence makes it an author choice. Do not use the
inventory as a deny-list. Move reusable policy into the template and remove or
resolve unexplained compensation. Do not report the template ready while a
spacing, font, or placement observation remains unclassified, `unresolved`, or
an unexplained one-off compensation.

## Prefer Rules Over Offsets

Use constants only for publication-fixed dimensions with identifiable evidence.
For content-dependent extents, use natural flow and local measurement:

| Property | Implementation source |
|---|---|
| Fixed paper geometry, margin, type size, rule thickness | evidenced constant |
| Content-dependent width or height | `measure`, `layout`, `context`, natural flow |
| Local-width behavior | measure at the actual local width |
| Breakable list or table | allow pagination and check its tail |
| Atomic object that fits | keep the complete object together |
| Atomic object too large | emit a project-appropriate actionable error |

A measured offset can calibrate a fixed publication rule. It is not a substitute
for measuring content that may wrap, grow, or move between pages.

Implement in dependency order: page and fonts, paragraph flow, headings,
frontmatter, equations, figures and captions, tables and lists, then references.
Compile the official fixture after each cross-cutting change because local
height changes move all downstream content.

## Use Exactly Three Fixtures

The fixture names and API are project-declared; only their purposes are fixed.

1. **Official** reproduces the supplied sample completely and names its visual
   reference. It calibrates content, geometry, fonts, pagination, and appearance.
2. **Frontmatter variation** changes frontmatter content while keeping the body
   stable. Use a meaningful long or multiline case supported by this source.
   Check the final frontmatter marker precedes the first body marker, then inspect
   the transition for clipping or overlap.
3. **Body-flow variation** keeps compact frontmatter and grows ordinary body,
   list, and table content enough to cross pages naturally. Put start/end markers
   inside each breakable element and a following marker after it. When the
   official source contains a display equation or a figure with caption, also
   exercise each here with standard Typst syntax; keep their styling in the
   template.

Do not add a generic capability matrix, generated fixture family, or mandatory
diagnostic. Add a new project fixture only after an observed defect cannot be
expressed by one of these three; ask before expanding the permanent workflow.

Declare paths and positive checks in the project's small `checks.json`. Read
[references/validation-playbook.md](references/validation-playbook.md) for its
exact fields and interpretation.

Run the batch checker:

```bash
python3 <skill-dir>/scripts/check_fixtures.py \
  checks.json audit/run-001
```

The checker verifies the declared source boundary, source inventories, clean
Typst compilation, dependency and bibliography consumption, hashes, page/text
checks, standard-structure coverage, and page-flow markers. For the official
fixture it derives the embedded font-face set from the reference PDF and fails
missing or extra candidate faces after conservative exact normalization; do not
supply a hand-picked font list. It also runs the sibling comparator at least
300 DPI and applies fixed `0.25 pt` structural preflights across every page:
ordered text-word anchors, source-counted numbered-equation body/number anchors,
and local ink extents plus dense row/column bands. These catch displacement and
coarse block, rule, and image-structure drift; they do not establish pixel
identity or aesthetic acceptance. Use `compare_pdfs.py scan` directly for a
disposable lower-DPI diagnostic.

## Compare Every Page, Then Focus

The official comparison is hierarchical:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf audit/scan

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/scan audit/detail --finding <finding-id>
```

Read `index.json` first. Confirm page correspondence, geometry, content, font
sets, and render origin. Then inspect risk-ranked pages and hotspots at high
resolution. Never register or rescale the candidate into agreement: displacement
is evidence about the template.

Prioritize semantic risk over aggregate magnitude. Inspect frontmatter,
presenter marks, column transitions, equation numbers, caption prefixes, table
rules and repeated headers, list tails, references, and the final page when they
occur. A small full-page ratio can hide a missing glyph or an overlapping rule.

Classify each material residual before changing code. A passed structural
preflight does not waive this review:

- content mismatch
- font or glyph substitution
- fixed geometry error
- content-dependent flow error
- asset difference
- renderer-only raster difference
- unresolved source conflict

Change the smallest reusable rule that explains the observation. Preserve a
residual only after its cause and affected scope are understood.

Use the following causal map to turn a measured signature into a positive
repair. Treat `candidate - reference` as the signed delta:

| symptom | measurement signature | governing rule | positive repair | revalidation |
|---|---|---|---|---|
| a block moves coherently | similar word `dx`/`dy` from its first anchor onward | shared wrapper alignment, inset, or block placement | move the governing container by the negative delta | affected anchors approach zero; other blocks/pages do not move |
| downstream content accumulates vertical drift | small early `dy`, then progressively larger `dy` | earliest wrong leading, paragraph gap, or block spacing | correct that repeated spacing rule at the first divergence | cumulative `dy` collapses toward zero through later pages |
| equation body or number is displaced | equation body-left and number left/top reference→candidate→delta | template equation indent/alignment/number rule | correct the standard equation rule, preserving author math | all equation deltas approach zero and body-flow equation still works |
| text anchors agree but a line differs | dense horizontal/vertical rule-band delta or count change | table/grid stroke or rule placement | reproduce the evidenced stroke thickness and position | band edges/counts match without moving text anchors |
| figure region has wrong extent or center | local image ink bbox width/height or centroid delta | figure sizing/alignment and shared caption block | reproduce the evidenced asset box and alignment | image bbox deltas approach zero; caption and following flow remain stable |
| embedded faces are missing or extra | reference-derived face-set missing/extra entries | affected element font/show rule and fallback chain | select the evidenced face/style and remove unintended fallback | candidate face set equals reference before geometry tuning |

Do not add a fixture-only `move`, negative gap, or public offset to cancel one
observation. It hides the governing cause, usually changes downstream flow, and
has no positive prediction for the frontmatter/body-flow variations. A local
author value is acceptable only when structural evidence identifies it as
author content in the reconstruction map.

`check_fixtures.py` places at most about twelve compact `repair_targets` in
`report.json` and `summary.txt`. They are derived from the existing font,
per-page earliest/maximum same-line coherent token-cluster medians, equation,
and representative local band/ink measurements. Isolated raw word maxima remain
diagnostic because repeated words can match the wrong semantic occurrence. Each
target includes reference and candidate values plus the correction direction.
Use them as repair hypotheses, not as authority or automatic acceptance.

For every repair, state the predicted measurement and direction before editing,
then run a focused PDCA cycle:

1. change only the hypothesized governing template rule;
2. rerun the affected fixture and confirm the targeted signed residual moves
   toward zero, not merely below a threshold;
3. rerun every official page and all three fixtures, confirming that previously
   stable pages and the other two fixtures did not regress;
4. if the residual does not move in the predicted direction, reject or revert
   the hypothesis, reclassify the cause, and test a new governing rule. Do not
   weaken a gate or add a fixture-only compensation to preserve the hypothesis.

## Promote Escaped Defects Positively

When review finds a defect that the three fixtures missed:

1. record the visible signal and structural cause;
2. decide whether it belongs to author content or template policy;
3. add the smallest positive text, order, page-flow, or focused visual check to
   the relevant existing fixture;
4. change the reusable rule;
5. rerun all three fixtures and the official all-page scan.

Avoid deny-lists of implementation spellings. Test the behavior that should
survive instead.

## Report

Report the three fixture results, exact input/template hashes, compiler warnings,
reference-derived font comparison, official page/text/anchor/local-ink metrics,
page-flow and standard-structure evidence, bibliography dependencies, completed
ownership classifications, inspected visual regions, rule changes, and remaining
residual causes. Say that the result is ready for user review only when all
mechanical checks pass, every inventory item has a resolved owner, and every
material visual difference has been classified. User acceptance remains a user
decision.
