# Typst Template Acceptance Manifest

`acceptance.json` records decisions that cannot be obtained mechanically. The
bundled verifier records hashes, inventories, compiled PDFs, text, fonts,
geometry, and comparison measurements. This division prevents a measurement
copied from one sample from silently becoming a layout rule.

## Lifecycle

```bash
python3 <skill-dir>/scripts/verify_template.py init acceptance.json
python3 <skill-dir>/scripts/verify_template.py inspect acceptance.json audit/inspect
python3 <skill-dir>/scripts/verify_template.py run acceptance.json audit/run-001
```

`init` never overwrites a manifest. `inspect` observes evidence without
compiling fixtures. `run` compiles every fixture and writes a compact root
report plus detail artifacts. Each output directory must be new or empty, which
keeps an accepted result reproducible without worktree monitoring.

The generated academic-paper manifest is a scaffold with valid role names, an
official fixture, and its calibration comparison. Populate the declared
evidence paths and fixture sources before `inspect` or `run`; those commands
validate the current files rather than manufacturing missing examples.

## Exact Schema

Paths below are relative to `project_root` unless stated otherwise. The project
root itself is relative to the manifest and fixture sources must remain inside
it. Evidence may be an absolute path, so an official PDF or DOCX can stay
outside the project. Region coordinates are visual-page points: `(x_pt, y_pt)`
starts at the top-left of the rendered, rotation-applied page; `x` increases to
the right and `y` increases downward. They are not PDF user-space coordinates,
whose customary origin is lower-left.

```json
{
  "schema_version": 1,
  "project_root": ".",
  "font_paths": ["fonts"],
  "required_available_fonts": ["Times New Roman", "MS Mincho"],
  "required_typst_version": "0.14.2",
  "comparison_settings": {
    "scan_dpi": 150,
    "pixel_threshold_percent": 3.0,
    "geometry_tolerance_pt": 0.1
  },
  "evidence": [
    {
      "id": "official-docx",
      "path": "evidence/official.docx",
      "role": "structural-source"
    },
    {
      "id": "official-pdf",
      "path": "evidence/official.pdf",
      "role": "visual-reference",
      "approved_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    },
    {
      "id": "word-calibration-review",
      "path": "evidence/word-calibration-review.md",
      "role": "review-record",
      "approved_sha256": "123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0"
    },
    {
      "id": "accepted-typst-official",
      "path": "evidence/accepted-typst-official.pdf",
      "role": "accepted-typst-baseline",
      "approved_sha256": "23456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef01"
    },
    {
      "id": "shared-publication-logo",
      "path": "/path/to/shared/publication-logo.svg",
      "role": "external-dependency",
      "approved_sha256": "3456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef012"
    }
  ],
  "required_capabilities": [
    {"id": "frontmatter", "require_diagnostic": false},
    {"id": "image-sizing", "require_diagnostic": true},
    {"id": "table", "require_diagnostic": false},
    {"id": "bibliography", "require_diagnostic": false}
  ],
  "fixtures": [
    {
      "id": "official-sample",
      "source": "fixtures/official.typ",
      "role": "official",
      "intent": "Content-equivalent official sample; body uses 図1 and 表1 while captions use Fig. 1 and Table 1.",
      "covers": [
        {"capability": "frontmatter", "case": "nominal"},
        {"capability": "frontmatter", "case": "boundary"},
        {"capability": "image-sizing", "case": "nominal"},
        {"capability": "table", "case": "nominal"},
        {"capability": "bibliography", "case": "nominal"}
      ],
      "page_contract": {"minimum_pages": 1},
      "required_embedded_fonts": ["TimesNewRomanPSMT"],
      "approved_external_dependencies": ["shared-publication-logo"],
      "positive_text": {
        "required_text": ["図1", "表1", "Fig. 1", "Table 1", "BIBLIOGRAPHY-END"],
        "ordered_text": ["Fig. 1", "BIBLIOGRAPHY-END"]
      },
      "comparisons": [
        {
          "id": "word-calibration",
          "purpose": "calibration",
          "reference_evidence": "official-pdf",
          "basis": {
            "mode": "content-equivalent",
            "evidence": "word-calibration-review"
          },
          "visual": {"mode": "evidence"},
          "inspection": {
            "status": "approved",
            "evidence": "word-calibration-review"
          }
        },
        {
          "id": "typst-zero-regression",
          "purpose": "regression",
          "reference_evidence": "accepted-typst-official",
          "basis": {
            "mode": "content-equivalent",
            "evidence": "accepted-typst-official"
          },
          "visual": {"mode": "zero"}
        }
      ]
    },
    {
      "id": "table-boundary",
      "source": "fixtures/table-boundary.typ",
      "role": "stress",
      "intent": "Tall header, wrapped cells, root/fraction content, and a page-crossing table preserve complete rules and following flow.",
      "covers": [
        {"capability": "image-sizing", "case": "boundary"},
        {"capability": "table", "case": "boundary"},
        {"capability": "bibliography", "case": "boundary"}
      ],
      "positive_text": {
        "required_text": ["TABLE-END", "AFTER-TABLE"],
        "ordered_text": ["TABLE-END", "AFTER-TABLE"]
      },
      "comparisons": []
    },
    {
      "id": "atomic-image-diagnostic",
      "source": "fixtures/atomic-image-diagnostic.typ",
      "role": "diagnostic",
      "intent": "An atomic figure/caption exceeding a page reports the supported actionable diagnostic.",
      "covers": [{"capability": "image-sizing", "case": "diagnostic"}],
      "required_diagnostic_text": ["ACTIONABLE FIGURE DIAGNOSTIC"]
    }
  ]
}
```

The example is a schema illustration. A real manifest must cover each declared
capability in its `nominal` and `boundary` cases, and also `diagnostic` when
`require_diagnostic` is true. The verifier reports missing coverage; it does
not infer which capabilities a publication needs.

## Fields and Their Meaning

| Field | Mechanical behavior | Decision recorded by author/Codex |
|---|---|---|
| `font_paths` | passed to Typst | where publication fonts are supplied |
| `required_available_fonts` | checks Typst's font listing | required family names |
| `required_typst_version` | optional exact version check | whether an accepted run freezes Typst version |
| `comparison_settings` | sets evidence-scan and measurement defaults | any non-default value needs `reason` |
| `evidence` | hashes every file; inventories DOCX and PDF | source role and optional approved SHA-256 |
| `required_capabilities` | verifies fixture coverage | supported public behavior |
| `fixtures` | compiles source and records artifacts | role, intent, positive contracts, and comparison basis |

Schema objects are closed: unknown keys and missing required keys are input
errors at the manifest, evidence, capability, coverage, fixture, page-contract,
positive-text, comparison, basis, inspection, and gate-contract levels. Extend
the script and documentation together when a genuinely new decision is needed;
a misspelled or unimplemented field must not be silently ignored.

Gate resolution is fixed at 300 DPI by `compare_pdfs.py` and recorded in gate
output; it is not an author decision. The former `comparison_settings.gate_dpi`
field is now unknown and rejected, including when its value is 300.

An evidence item has unique safe `id`, `path`, and one exact role:

- `structural-source`
- `visual-reference`
- `review-record`
- `accepted-typst-baseline`
- `external-dependency`

An optional `approved_sha256` is a 64-character SHA-256 chosen only after the
input is accepted; a changed hash becomes an automated failure. A review used
by `inspection`, a baseline used by `zero`, and every evidence item named by
`approved_external_dependencies` require this hash and must match it in the
current run.

A fixture has unique safe `id`, project-relative `source`, role, nonempty
`intent`, and `covers`. At least one `official` fixture exists, and every
official fixture has at least one comparison. Fixture role determines outcome:
`official` and `stress` compile successfully; `diagnostic` fails and contains
every `required_diagnostic_text` fragment. Diagnostic coverage appears only on
a diagnostic-role fixture, and a diagnostic fixture covers only diagnostic
cases. The manifest therefore has no `expected_outcome` field.

The verifier validates that `intent`, capability IDs, fixture roles, and basis
evidence are present and internally consistent. It cannot establish that the
declared capability describes the source, that the fixture faithfully
implements it, or that two documents are truly content-equivalent. Codex makes
those semantic judgments from the source and records the supporting evidence;
the script verifies declaration structure and evidence identity.

Success fixtures require `positive_text.required_text`; optional
`positive_text.ordered_text` proves that tail markers still occur in sequence.
They may declare `page_contract.minimum_pages` and
`required_embedded_fonts`. Embedded names are compared by exact normalized
identity: strip a six-letter PDF subset prefix, lowercase, and remove
non-alphanumeric characters; substring matches are not accepted. Inspect the
candidate `pdffonts` result before recording the expected normalized name.
`approved_external_dependencies` contains evidence IDs whose role is exactly
`external-dependency` and whose `approved_sha256` matches the current file.
Other evidence roles or an unapproved/changed external file do not authorize an
out-of-root dependency. A successful fixture with any compiler warning fails
its compile contract. These are positive behavioral claims, rather than proxy
implementation restrictions.

## Comparisons: Scan, Detail, Gate

Each success fixture may have zero or more `comparisons`; every official fixture
has at least one. A comparison has:

| Field | Values | Meaning |
|---|---|---|
| `id` | safe unique ID | artifact namespace |
| `purpose` | `calibration`, `regression` | Word/reference learning versus Typst-baseline protection |
| `reference_evidence` | PDF evidence ID | declared visual input |
| `basis.mode` | `content-equivalent`, `geometry-only` | whether full visual layout has a valid content basis |
| `basis.evidence` | manifest evidence ID | record supporting the selected comparison basis |
| `visual.mode` | `evidence`, `zero`, `approved-budget` | observation, exact regression, or an approved residual contract |
| `inspection` | optional `{status: "approved", evidence: "evidence-id"}` | recorded human causal review |

`basis.evidence` names `structural-source`, `review-record`, or
`accepted-typst-baseline` evidence. `inspection.evidence` names a
`review-record` whose `approved_sha256` matches. A review note is therefore
evidence like a DOCX or PDF: declare and hash it before a comparison refers to
it. `geometry-only` pairs only with `visual.mode: "evidence"`: the verifier scans
content/font/geometry facts without asserting wrapping or pagination. A
content-equivalent comparison may use `evidence` while residuals are being
classified. That run finishes `inspection_pending` until its `inspection`
record is approved.

`purpose: "regression"` requires `visual.mode: "zero"`; `zero` is valid only
for regression. Its reference has role `accepted-typst-baseline`, has an
`approved_sha256`, and matches that hash in the current run. It requires
`raw_changed_pixels == 0` in every full-page and declared
region gate target, rather than treating changes below the 3% measurement
threshold as equal. It is not a sensible Word-to-Typst calibration criterion.
`approved-budget` records a classified nonzero current residual. It remains
`inspection_pending` until `inspection` names an approved, matching
`review-record`. After that inspection is recorded and the gate passes, the
comparison can clear pending and contribute to a complete result; the budget
does not substitute for causal review.

For `zero` or `approved-budget`, `visual` is passed to `compare_pdfs.py gate`.
An `approved-budget` contract accepts the following fields:

```json
{
  "mode": "approved-budget",
  "pixel_threshold_percent": 3.0,
  "geometry_tolerance_pt": 0.1,
  "page_budgets": {
    "1": {
      "max_changed_ratio": 0.002,
      "max_changed_pixels": 500,
      "cause": "documented font rasterization residual",
      "scope": "page 1 only",
      "approval": "review record 2026-08-01"
    }
  },
  "regions": [
    {
      "id": "presenter-marker",
      "page": 1,
      "x_pt": 72.0,
      "y_pt": 104.0,
      "width_pt": 18.0,
      "height_pt": 18.0,
      "budget": {
        "max_changed_ratio": 0.01,
        "max_changed_pixels": 80,
        "cause": "documented marker glyph residual",
        "scope": "presenter marker only",
        "approval": "review record 2026-08-01"
      }
    }
  ]
}
```

A `zero` visual object has `{"mode": "zero"}` and may name regions without
budgets. It rejects `pixel_threshold_percent` and
`pixel_threshold_reason`: raw pixel equality is its entire visual criterion.
It may retain the default geometry tolerance or declare a justified
`geometry_tolerance_pt` with `geometry_tolerance_reason`. An
`approved-budget` visual object names at least one explicit page budget or
region budget; otherwise it has no approved residual to describe and the
verifier rejects it. Each approved budget requires exactly the five values
shown. In this nonzero mode, a threshold other than 3.0% or geometry tolerance
other than 0.1 pt requires the corresponding nonempty reason.

A zero-mode region uses the same visual-page coordinates and omits `budget`:

```json
{
  "mode": "zero",
  "regions": [
    {
      "id": "presenter-marker",
      "page": 1,
      "x_pt": 72.0,
      "y_pt": 104.0,
      "width_pt": 18.0,
      "height_pt": 18.0
    }
  ]
}
```

The zero ROI is optional named local audit and failure-diagnostic evidence. The
full-page raw-zero gate already implies equality inside it, so an ROI is neither
a weaker criterion nor an additional tolerance. It adds a stable local gate
record and, on failure, a named failed ID plus focused artifacts. A passing ROI
does not replace risk-driven detail inspection or causal review.

`visual.mode: "evidence"` uses the deliberately inexpensive default 150 DPI
all-layer scan and covers every page. `comparison_settings.scan_dpi` may change
that default when a documented reason justifies it. Its `index.json` holds
bounded findings and links to page detail records. `zero` and `approved-budget`
first scan non-raster
content/font/geometry evidence, then use the 300 DPI gate for the visual
decision; this avoids rasterizing every page twice. Request `detail` only for a
page, a visual-page-point box, or a named finding at the needed resolution.
`gate` caches each rendered page for its full-page and ROI checks. This keeps
all-page coverage while preventing repeated full-resolution work and unbounded
context.

The manifest-driven verifier remains the primary lifecycle. For targeted
investigation of an existing reference/candidate pair, the exact direct forms
are:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf audit/scan

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/scan audit/detail-finding --finding <finding-id-from-index>

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/scan audit/detail-box --page 1 --box 72 104 18 18

python3 <skill-dir>/scripts/compare_pdfs.py gate \
  reference.pdf candidate.pdf gate-contract.json audit/gate
```

`<finding-id-from-index>` is a placeholder that must be replaced by an ID
actually present in `audit/scan/index.json`; only ranked hotspots are retained
there, so no particular tile ID is guaranteed. Tile IDs use the stable form
`pPPP-rRRR-cCCC-tile` (one-based, zero-padded page, row, and column).
`--page` may select the whole page or combine with
`--box X Y WIDTH HEIGHT`; the box follows the top-left, post-rotation point
convention above. Add `--layers` and `--dpi` when the investigation needs a
selected signal or resolution. Each output directory is new or empty, just
like verifier output.

## Promote Human-Found Defects

Pixels locate a discrepancy but cannot decide its meaning. When a reviewer
finds an escaped defect, record its observed signal, structural cause, and
public consequence; add the smallest positive text contract, named ROI, or
nominal/boundary/diagnostic fixture that would expose it next time. Examples:

- `図1`/`表1` in Japanese body text and `Fig. 1`/`Table 1` captions require
  separate positive text snippets.
- A 9.5 pt caption and bibliography-heading spacing require a calibrated ROI
  plus full-page downstream-flow evidence.
- A 0/0 preliminary image measure requires a boundary fixture with its
  following marker, because a screenshot alone does not test compilation.
- Presenter-circle glyph geometry is a high-resolution ROI, distinct from
  author-line spacing.
- Chapter spacing and nested-figure spacing require a declared semantic choice:
  a local author override is fixture content, while nested figure ownership is
  a grouping/flow rule. They are not automatically residuals of the same kind.

This is the feedback loop for defects that aggregate pixel scores previously
missed: a human observation becomes a reproducible positive contract, not a
growing list of forbidden output strings.

## Result States

`run.json` separates `automation_status` from `completion_state`.
`automation_status: "pass"` means all declared machine contracts passed.
`completion_state: "inspection_pending"` means the machine run passed but a
calibration, geometry-only comparison, or approved-budget residual still needs
an approved matching `review-record`. Once that inspection exists, a passing
approved-budget gate no longer forces pending. Only claim template completion
after all required inspection records and relevant causal decisions exist.
