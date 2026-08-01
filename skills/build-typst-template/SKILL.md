---
name: build-typst-template
description: Build, reconstruct, or harden reusable Typst document templates from Word/DOCX, PDF, TeX/LaTeX, or existing Typst evidence. Use when Codex must reproduce an official sample across every page, separate semantic author API from layout machinery, diagnose layout drift, or verify titles, authors, figures, tables, equations, lists, references, fonts, and pagination with a repeatable acceptance contract.
---

# Build Typst Template

Reconstruct the document system that produced the sample. A sample PDF supplies
observations; it does not by itself define the reusable rule.

## Separate the Three Responsibilities

| Responsibility | Owner | Result |
|---|---|---|
| Scope, editable files, source precedence, intended author choices, accepted residuals | user | explicit decisions |
| Infer semantic structure, choose the public API, derive layout rules, classify visual residuals | Codex | specification and implementation |
| Hash inputs, compile fixtures, separate comparison signals, scan every PDF page, verify text/end markers, and gate approved contracts | bundled scripts | repeatable evidence |

Keep these boundaries explicit. The verifier proves declared conditions; it does
not decide which reference is authoritative or whether a remaining glyph-shape
difference is acceptable.

## Establish a Contract Without Turning It Into Data Entry

Resolve the directory containing this `SKILL.md` as `<skill-dir>`, then create a
starter manifest in the document project:

```bash
python3 <skill-dir>/scripts/verify_template.py init acceptance.json
```

Read [references/acceptance-manifest.md](references/acceptance-manifest.md).
Start from the skeleton, inspect the evidence and fixture, and record only
authority, fixture meaning, author choices, supported capabilities, positive
text/diagnostic expectations, and accepted residual decisions. The verifier
observes hashes, DOCX/PDF inventory, reference page/geometry/font candidates,
tool versions, candidate embedded fonts, dependencies, and visual metrics.

The manifest is the boundary between judgment and repetition:

- Put an intent value in the manifest after its meaning and evidence are understood.
- Let the verifier execute every repeatable check after that value is fixed.
- When evidence leaves authority, residual risk, or edit scope unresolved, record
  that state and ask the user one concrete question.

## Establish Evidence Authority

Apply these positive branches:

| Available evidence | Use it for | Resulting action |
|---|---|---|
| Written publication rule states a property | normative requirement | implement and cite that property |
| PDF exported by the intended authoring application | final geometry and appearance | calibrate page and component positions against it |
| DOCX, TeX, or another editable source | structure and authoring semantics | inspect styles, sections, object types, and explicit breaks |
| Repeated examples show the same behavior | reusable-rule evidence | formulate one rule and test it with varied content |
| One sample alone shows a behavior | hypothesis | create a boundary fixture before promoting it to a rule |
| Sources prescribe different behavior | user decision | present the exact conflict and ask which source governs |

Operate on the approved edit set. When the required change falls outside that
set, request an explicit scope expansion. This protects concurrent user work
without spending time monitoring unrelated files.

Use the original application to create a matched reference variant when a test
depends on that application's wrapping or pagination. When that application is
unavailable, classify the corresponding visual claim as unresolved while
continuing structural work supported by the available evidence.

## Build a Comparable Official Fixture

Pixel differences become layout evidence when reference and candidate contain
the same wording, explicit line breaks, equations, images, table data, and
bibliography entries. First make the usage fixture content-equivalent to the
official sample, including meaningful brackets, symbols, units, and reference
labels.

When content differs, choose one of these branches:

- Create a temporary matched reference and run full visual calibration.
- Compare only properties independent of content, such as paper geometry, while
  withholding conclusions about wrapping and pagination.

Keep the reusable template and the official fixture separate. Put real author
choices such as an intentional line break or table column widths in the fixture;
put typography, spacing, measurement, pagination, and overflow handling in the
template.

## Design the Public API by Meaning

Evaluate an API element by what it represents, rather than by its name:

| Meaning | Typst interface |
|---|---|
| Ordinary heading, figure, table, equation, list, label, or reference | standard Typst syntax styled through `set` and `show` |
| Document metadata such as title, authors, affiliations, abstract, keywords | one document wrapper |
| Author-controlled content choice such as a deliberate break or column width | explicit usage-file data |
| Reusable semantic structure absent from standard Typst | a generally named helper with nominal and boundary fixtures |
| Calibration, measured offset, caption hang, pagination, or overflow policy | private template implementation |
| Visual discrepancy unique to one sample | investigate content measurement and flow before creating any API |

A renamed placement flag or continuation helper remains the same flawed API when
the author still has to understand template internals. The underlying problem is
the leaked responsibility, not the identifier.

Prefer this authoring shape:

```typst
#import "template.typ": *

#show: body => template(
  title: [...],
  authors: (...),
  abstract: [...],
  keywords: (...),
  body,
)

== Standard heading

#figure(...)
#table(...)
$ equation $
```

Before implementing components, read
[references/implementation-patterns.md](references/implementation-patterns.md).

## Derive Rules From Content and Structure

Fixed compensation is structurally wrong when the formatted object's extent can
change: it makes correctness depend on the calibration sample. Apply this
selection rule:

| Property | Implementation source |
|---|---|
| Publication-fixed margin, rule thickness, or minimum line box | named constant with cited provenance |
| Content-dependent width or height | `measure`, `layout`, `context`, natural flow, and content-aware insets |
| Local container-dependent size | measure at the actual local width |
| Breakable content | allow Typst pagination and verify its tail survives |
| Atomic content that fits the usable region | keep the complete object together |
| Atomic content larger than the usable region | emit an actionable diagnostic |

Implement in dependency order:

1. page, fonts, paragraph flow, footer
2. headings and body flow
3. title, authors, affiliations, abstract, keywords
4. equations and number fields
5. figures, captions, images, grouped content
6. tables, rules, headers, pagination
7. lists and tail behavior
8. cross-references and bibliography

Compile the complete official fixture after each component because a local
change can alter every downstream page.

## Make Structural Claims Behavioral

Create fixtures that exercise the public interface rather than scanning for a
few forbidden spellings. A textual deny-list is easy to evade while preserving
the same leaked responsibility.

Declare at least these contracts in `acceptance.json`:

- one-line and multi-line titles, subtitles, authors, and affiliations
- headings in normal flow and at page boundaries
- inline slash/fraction semantics and tall display equations
- relative and narrow-parent images, including preliminary zero dimensions
- numbered, unnumbered, wrapped, and narrow captions
- short, narrow, tall-header, and multi-page tables with repeated rules
- lists whose tails cross pages and tails longer than one page
- one-, two-, and three-digit references plus every supported bibliography type
- explicit diagnostic fixtures for overwide or over-tall atomic content

For the known JSME-style distinctions, positive text contracts state Japanese
body references (`図1`, `表1`) separately from English caption prefixes
(`Fig. 1`, `Table 1`). Caption size, bibliography-heading spacing, and the
presenter marker are geometry questions, so they receive named visual regions
rather than approximate text proxies. A 0/0 preliminary image measurement is a
compilation-and-tail boundary fixture. Chapter overrides and nested-figure
spacing first receive a declared ownership choice: author content/local choice
or template flow rule.

Place unique end markers after breakable stress objects and declare them as
required text. Declare complete expected bibliography snippets so locale changes
such as `p.` becoming another label fail through absence of the approved output,
rather than through a growing list of banned words.

## Run the Mechanical Loop

After the manifest is filled, run:

```bash
python3 <skill-dir>/scripts/verify_template.py run \
  acceptance.json layout-audit/run-001
```

Use a new, user-accessible output directory for each run. The verifier performs
the fixed work: evidence/dependency hashes, DOCX/PDF inventory, compilation,
font observation, text/end-marker contracts, and expected diagnostics.
`compare_pdfs.py scan` separates content, font, toolchain, page geometry, ink,
and pixel signals into compact `index.json`, page detail records, and grid
hotspot candidates. `detail` rereads a selected page, box, or finding at the
requested high resolution. `gate` makes a compact decision only for approved `zero` or
`approved-budget` contracts.

Read the scan index first, rank findings by semantic risk as well as magnitude,
then read selected detail. Every page remains in the scan without placing all
images and raw metrics in one context. Measurement kind locates a difference;
causal classification is a separate engineering decision. Promote a meaningful
recurrent hotspot to a named ROI for repeatable local evidence.

## Diagnose What Automation Detects

Read [references/validation-playbook.md](references/validation-playbook.md) after
the first verifier run. Let automation locate and quantify differences; use
engineering judgment to classify their causes.

After each implementation change:

1. run the entire manifest into a fresh output directory
2. read the scan index, then inspect affected or risk-ranked detail
3. inspect downstream page flow and structural end markers
4. record the causal classification and the rule changed
5. preserve or update acceptance values only after the change is understood

An aggregate score is a detector, not a diagnosis. Local overlaps, missing
brackets, wrong fraction structure, presenter glyphs, and locale-generated words
can remain important even when a full-page ratio is small.

## Completion States

Use exactly one final state:

- **complete**: every page has mode-appropriate comparison evidence—a per-page
  scan record in every mode and, for `zero`/`approved-budget`, a per-page 300 DPI
  gate record; gated modes do not require a duplicate raster scan. Approved
  visual contracts pass their compact gate; risk-ranked and declared details
  have recorded inspection/classification; API semantics were reviewed; source
  conflicts and residuals have recorded decisions; unrelated files stayed
  outside the edit set.
- **incomplete**: at least one declared contract fails; report its evidence and
  continue the loop.
- **blocked**: an authoritative source, required font, or user decision needed to
  define correctness is unavailable; report the precise missing input.

Source inspection is always allowed. If a required font is missing or
compilation emits a fallback warning, the verifier acceptance run cannot pass.
The project/template completion state is `blocked` until the required font
resolves without fallback. Any fallback compile or structural experiment based
on fallback output is diagnostic non-acceptance evidence only.

Describe residual differences quantitatively and by cause. Reserve claims such
as “pixel-identical” for the exact pages and regions whose zero-difference
contracts passed.
