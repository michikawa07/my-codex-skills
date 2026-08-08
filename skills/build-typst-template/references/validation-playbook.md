# Visual Comparison Playbook

Use this reference when whole-page comparison reveals a residual that needs
focused diagnosis. The outputs are observations for Codex to interpret, not a
schema, acceptance threshold, or readiness decision.

## Establish Comparable Inputs

First render the reference with its established producer and the candidate with
the project's Typst command. Then confirm that meaningful content, page order,
paper boxes, rotation, and intended assets correspond. Record renderer and font
paths when they can affect the result.

Record any user-confirmed comparison-only guidance as an explicit object or
region mask. Inspect the mask boundary so neighboring publication content
remains part of the comparison.

Use fresh output directories:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf audit/scan --dpi 200
```

Start with `audit/scan/index.json` and inspect every page. Read these signals
separately:

| Signal | Useful evidence |
|---|---|
| page count/geometry | pagination, paper box, orientation |
| extracted text/diff | content and reading-order correspondence |
| embedded fonts | face use and possible fallback |
| page raster/overlay | coherent alignment and visible omissions |
| absolute difference/hotspots | where ink differs |
| text or ink bbox | signed position and extent differences |
| row/column projections | rules, baselines, and repeated bands |

No one signal establishes semantic correctness or visual acceptability.

## Focus on a Semantic Region

Choose a title block, heading, equation number, image, caption, table rule,
reference entry, transition, or final-page tail whose role is understood. Then
request high-resolution detail for a reported finding or an explicit box:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/scan audit/detail --finding <finding-id> --dpi 300
```

Inspect the element together with enough parent and following context to reveal
alignment, available width, spacing, and downstream flow. Preserve displacement
evidence by avoiding registration or rescaling. Compare the element's internal
text/math form, glyphs/fonts, rows/cells, rules/borders, padding, and alignment
as applicable; matching outer anchors alone does not establish fidelity.

## Form and Test a Repair Hypothesis

First classify the residual as content, font/glyph, fixed geometry,
content-dependent flow, stroke, asset, or renderer rasterization. Then locate
the earliest governing element and inspect its parent parameters.

Useful causal patterns include:

- coherent `dx`/`dy`: shared container alignment, inset, or placement;
- progressively growing vertical `dy`: earliest repeated line pitch or gap;
- changed wrap: font metrics, tracking, available width, indent, or explicit
  break;
- aligned text with a different band: stroke thickness or position;
- image extent/centroid mismatch: asset, intrinsic size, fit, crop, or alignment;
- downstream-only shift: preceding element height, spacing, or keep/break rule.

State the predicted signed change, edit the smallest reusable Typst rule, and
rerender. First check the focused region; then inspect downstream elements, all
affected pages, and a relevant content variation. If the observation moves in a
different direction, revise the causal hypothesis instead of hiding it with a
sample-only offset.

## Record the Judgment

Keep only the notes useful for explaining the result: region and page,
observation, likely cause, rule changed, predicted and observed direction,
affected scope, and remaining uncertainty. Codex decides when the evidence is
sufficient and reports material residuals to the user. Record official local
fidelity and varied author-route behavior separately; both are required for an
element to close.
