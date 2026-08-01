# Typst Template Validation Playbook

Use this playbook after the acceptance manifest defines what the project means
by correct. Automation produces evidence and gate results; visual interpretation
and source conflicts remain engineering decisions.

## 1. Observe, Then Freeze Only Approved Intent

The verifier observes hashes, DOCX/PDF inventory, page geometry/count, font
candidates, dependencies, tool versions, extracted text, and metrics. Put only
these decisions in `acceptance.json`:

- authoritative reference PDF and structural source
- exact official fixture source
- intended fixture meaning and comparison basis
- required Typst family names and exact normalized embedded PDF font names
- source-supported visual mode and residual decision
- required text and ordered end markers
- expected success and expected diagnostic fixtures
- approved input hashes after a baseline is accepted

The failure addressed here is test drift: changing content, fonts, renderer, or
reference while interpreting metric changes as template progress. Reference page
count and geometry are observed, not manually duplicated.

## 2. Run the Fixed Verifier

Resolve the Skill directory and run into a new project-visible directory:

```bash
python3 <skill-dir>/scripts/verify_template.py run \
  acceptance.json layout-audit/run-001
```

The verifier uses fixed operations rather than manifest-supplied shell commands:

1. hash declared evidence
2. inventory declared DOCX structure without interpreting it
3. resolve required Typst fonts
4. compile declared fixtures and capture warnings/dependencies
5. verify expected success or expected diagnostic outcomes
6. extract candidate text and embedded PDF fonts
7. verify page counts, required text, order, and end markers
8. write a per-page scan record: all-layer raster evidence for `evidence`, or
   non-raster content/font/geometry preflight for gated modes
9. for `zero`/`approved-budget`, write a per-page 300 DPI gate record and retain
   failure artifacts only for failed targets; no duplicate raster scan is needed
10. write `run.json`, `summary.txt`, logs, PDFs, text, scan index, and selected
    detail artifacts

The output directory is new for each run, so prior evidence remains available
for regression comparison. Put retained runs where the user can open them from
their host environment; use temporary directories for disposable experiments.

## 3. Interpret Automated Gates

| Gate | What a pass proves | What still needs judgment |
|---|---|---|
| Evidence/dependency hashes | tested files are the declared files | authority and semantic correctness |
| Clean compile and font checks | intended toolchain/fonts were available and embedded | glyph-shaping equivalence |
| Page count and geometry | document has the declared physical structure | correctness of content positions |
| Required and ordered text | named content and tails survived extraction | visual typography and PDF reading-order limits |
| Expected diagnostic | impossible input fails through the intended path | whether the input should be supported instead |
| Full-page pixel metrics | visual change locations and magnitude | cause and importance of each residual |
| Region metrics | named local visual evidence | semantic correctness inside that region |

Treat the verifier's `pass` as a necessary machine result. Combine it with the
manual causal review before declaring the template complete.

## 4. Compare Content Before Geometry

Use full visual calibration when the candidate and reference carry equivalent
content. Verify equivalence through the strongest available positive contract:

- exact or normalized extracted-text match when the PDF encodings permit it
- required complete snippets for equations, tables, units, and bibliography
- image and source dependency hashes
- explicit record of instructional annotations excluded from the fixture

When content equivalence cannot be established, select `geometry-only`: inspect
paper geometry and artifact presence while reporting wrapping and pagination as
unresolved. When the original application is available, create a temporary
matched reference variant and select `content-equivalent`.

## 5. Scan Every Page, Then Diagnose Selected Detail

For `visual.mode: "evidence"`, run `compare_pdfs.py scan` at the default
150 DPI over every page; a reasoned `comparison_settings.scan_dpi` override may
change it. For `zero` and `approved-budget`, the verifier runs a
non-raster content/font/geometry preflight and lets the 300 DPI gate perform the
sole full-page raster pass. The comparison keeps the rendered page origin and
scale. Its compact index separates content, font, toolchain, page-geometry, ink,
and pixel signals and proposes grid hotspots. This preserves evidence of margin,
global translation, line pitch, and page flow without loading every image and
metric into one context.

Read the index first. Rank findings by semantic risk and magnitude, then use
`detail --page`, `--box`, or `--finding` for the required high-resolution crop.
Measurement kind reports how PDFs differ; source and rendering evidence classify
why. This keeps the all-page scan complete while attention remains targeted.

The full-page report supplies difference and ink bounds. Promote a component to
a named visual-page-point region when that evidence identifies a local question whose
importance survives full-page aggregation:

- titles and each author/affiliation boundary
- abstract, keywords, and page-top headings
- equation body and number field
- figure/caption boundary
- table headers, brackets, rules, and final row
- bibliography heading, wrapped entries, and final entry
- footer

Use a region to answer a local question while retaining every page in the scan
and, when approved, the compact gate as the downstream regression condition.
This addresses the historical failure where a
small author overlap and a wrong presenter glyph disappeared inside a low
aggregate page score.

Region coordinates use top-left page points after page rotation, with `x`
increasing rightward and `y` downward. This matches the rendered comparison
image and deliberately differs from lower-left PDF user-space coordinates.

## 5a. Risk Catalog and Escaped-Defect Loop

Every finding belongs to one or more of these risks. The catalog separates
location evidence from causal judgment, so a low aggregate pixel score cannot
erase a locally important defect.

| Risk | Positive evidence that exposes it |
|---|---|
| 1. Coverage | nominal, boundary, and required diagnostic fixture coverage |
| 2. Geometry | page count, boxes, margins, and declared anchor/ROI evidence |
| 3. Glyph | required embedded font plus high-resolution glyph ROI |
| 4. Semantic text | complete required literals and ordered tail markers |
| 5. Math structure | source-structure fixture and equation/rule-clearance crop |
| 6. Flow | page-crossing fixture followed by a unique marker |
| 7. Container extent | local-width/natural-height fixture, including 0/0 preliminary image sizing |
| 8. Rules | table header, bracket, vertical-rule, and lower-rule ROIs |
| 9. Environment | toolchain/version/font inventory and cross-environment fixture |
| 10. API responsibility | standard-syntax fixture and public-API review |
| 11. Diagnostics | deliberately impossible fixture with actionable required text |
| 12. Artifact usability | compact index first and retained failure images in user-visible output |

When human review finds an escaped difference, do not merely lower a global
threshold. Record the observed signal, structural cause, and user-visible
consequence. Then add the smallest positive contract that would have detected
it: a literal/marker for a text distinction, ROI for a localized geometry or
glyph question, or a nominal/boundary/diagnostic fixture for a behavior. Re-run
the complete manifest and use the new result as evidence. This converts a human
discovery into a future machine check without claiming pixels can infer cause.

In this template family that loop has distinct entries for: Japanese body
`図`/`表` versus caption `Fig.`/`Table`; a 9.5 pt caption; bibliography-heading
space; zero-premeasurement image sizing; presenter-circle glyph geometry;
chapter defaults versus an intentional local override; and nested figure
ownership. They have different causes, so they should not share one generic
layout-difference exception.

## 6. Classify the Cause

| Observation | Next investigation | Typical correction |
|---|---|---|
| Text contract differs | fixture/source structure | restore equivalent wording, symbols, data, or locale terms |
| Page geometry differs | page and section settings | correct paper, margins, header/footer geometry |
| Anchors drift progressively | line pitch and paragraph boundaries | implement the actual leading/spacing property |
| One variable-height block shifts following content | natural extent and minimum-height rule | return measured height plus supported minimum |
| Glyph edges differ while anchors and wrapping agree | font shaping/rasterization | record the residual and preserve structural geometry |
| Wrapping differs | local width, font advance, content equivalence | measure at the local container and verify fonts |
| Table rule intersects content | tallest cell bounds and shared insets | derive row height/clearance from content |
| Later rows or following text disappear | breakability of the actual container | make the content-bearing element breakable and verify its end marker |
| CLI and preview text differ | tool version, document language, CSL locale | make the approved locale term explicit and test both environments |

Choose a correction that explains the observation. Then exercise the same rule
with different content. A nearby offset that merely cancels the symptom will
fail this second fixture.

## 7. Structural Acceptance Matrix

| Component | Nominal contract | Boundary contract | Diagnostic contract |
|---|---|---|---|
| Title/front matter | one line, normal authors | multi-line bilingual titles, many authors | declared single-line area overflow |
| Heading | normal flow | page top, after equation | — |
| Equation | short formula | tall/wide/page-boundary formula | formula plus number exceeds usable width |
| Image | fixed natural size | relative, zero-premeasurement, narrow parent | unresolved or over-tall atomic object |
| Caption | short numbered | wrapped, multi-digit, unnumbered | atomic figure/caption exceeds page |
| Table | short table | tall header, narrow/multi-page, repeated rules | unsupported atomic table structure |
| List | short list | page crossing, short tail, oversized tail | — |
| References | one digit | two/three digits, wrapped, multi-page | — |
| Bibliography | common article | every supported item type and locale | malformed required metadata |

Put a unique required text marker after each breakable boundary object. A marker
proves that the complete object and following flow reached the PDF; it does not
replace visual inspection of rules and spacing.

## 8. Choose a Visual Mode From Evidence

| Evidence condition | Visual mode and process |
|---|---|
| same toolchain and intentionally unchanged baseline | `zero`; raw changed-pixel count must be exactly zero |
| original-application reference with classified residuals | `approved-budget`; record cause, scope, and publication risk |
| reference/candidate content not established equivalent | `evidence`; generate artifacts and withhold wrapping/pagination conclusions |

`geometry-only` records physical geometry and artifact presence without a visual
layout claim. `evidence` records scan evidence and does not run a visual
acceptance gate; its required approved inspection determines whether pending
clears. `zero` and `approved-budget` run `gate` after the scan.

Calibration, geometry-only, and approved-budget comparisons remain
`inspection_pending` until their `inspection` names an approved matching
`review-record`. With that inspection and a passing approved-budget gate, the
comparison can clear pending and contribute to completion.

Use `zero` for a before/after regression rendered by the same toolchain when
the change is expected to leave the official fixture untouched. This is raw
pixel equality, not a 3% thresholded-difference measurement. The 3% default
belongs to `evidence` and `approved-budget` measurements; an approved-budget
override requires a documented reason.

For Word-to-Typst comparisons, first classify the residual at full resolution.
Then freeze page and region limits that preserve all known structural and
semantic requirements. Record the decision that supports a nonzero limit.

The default PDF geometry tolerance of `0.1 pt` accounts for common A4 decimal
rounding between exporters. Select a stricter value when the publication rule
defines one.

## 9. Final Regression

After the final template change:

1. run the full manifest into a fresh directory
2. confirm `run.json` reports `pass`
3. confirm every page has its mode-appropriate scan record and, for a gated
   mode, its per-page gate record; inspect risk-ranked plus declared detail
   artifacts without requiring a duplicate raster scan
4. compare every formerly failing component with its selected latest detail
5. review the public API by meaning
6. run `git diff --check` on changed text files
7. confirm the edit set contains only approved files

Report tested fixtures, exact toolchain, automated results, manual classifications,
and remaining decisions. This makes “complete” a reproducible claim rather than
a summary of whichever crop was inspected last.
