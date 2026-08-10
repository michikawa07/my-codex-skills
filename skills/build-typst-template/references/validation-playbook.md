# Visual Comparison Playbook

Use this reference when whole-page comparison reveals a remaining difference that needs
focused diagnosis. Interpret its observations through the active element's
author syntax, owner category, official relations, activating variation, and
document-level completion conditions in `SKILL.md`.

## Establish Comparable Inputs

First render the reference with its established producer and the candidate with
the project's Typst command. Then confirm that meaningful content, page order,
paper boxes, rotation, and intended assets correspond. Record renderer and font
paths when they can affect the result.

Record any user-confirmed comparison-only guidance as an explicit object or
region mask. Inspect the mask boundary so neighboring publication content
remains part of the comparison.

Use a new or empty subdirectory inside the run's system-temporary scratch root:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf <scratch>/scan --dpi 200
```

Start with `<scratch>/scan/index.json` and inspect every page. Read these signals
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

Combine the complementary signals that expose the element's content, geometry,
formation, and flow.

## Focus on a Semantic Region

Choose a title block, heading, equation number, image, caption, table rule,
reference entry, transition, or final-page tail whose role is understood. Then
request high-resolution detail for a reported finding or an explicit box:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py detail \
  <scratch>/scan <scratch>/detail --finding <finding-id> --dpi 300
```

Inspect the element together with enough parent and following context to reveal
alignment, available width, spacing, and downstream flow. Compare in native page
coordinates to preserve displacement evidence. Confirm its outer placement in
the parent, direct-child placement and spacing inside its container, and internal
text/math form, glyphs/fonts, rows/cells, rules/borders, padding, and alignment as
applicable.

## Form and Test a Repair Hypothesis

First classify the difference as content, font/glyph, fixed geometry,
content-dependent flow, stroke, asset, or renderer rasterization. Then locate
the first affected branch defined in `SKILL.md` and inspect its parent parameters.

Useful source-to-output patterns include:

- coherent `dx`/`dy`: shared container alignment, inset, or placement;
- progressively growing vertical `dy`: earliest repeated line pitch or gap;
- changed wrap: font metrics, tracking, available width, indent, or explicit
  break;
- aligned text with a different band: stroke thickness or position;
- image extent/centroid mismatch: asset, intrinsic size, fit, crop, or alignment;
- downstream-only shift: preceding element height, spacing, or keep/break rule.

State the predicted signed change, edit the smallest reusable Typst rule, and
rerender. First check the focused region; then inspect downstream elements, all
affected pages, and a relevant content variation. When the observation moves in
a different direction, revise the predicted cause/direction and rerender.

## Record the Judgment

Record the region and page, observation, likely cause, rule changed, predicted
and observed direction, affected elements/pages, and remaining uncertainty. Codex decides
when the evidence is sufficient and reports remaining differences that change
content, formation, placement, or flow to the user.
Record the official element's content/formation/placement match and varied
author syntax/call-path behavior separately; both
are required for an element to close.
