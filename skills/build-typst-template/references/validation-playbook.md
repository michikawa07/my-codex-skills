# Typst Template Validation Playbook

Use this reference after evidence inspection and whenever a coherent template
change is ready for fixture verification.

## Contents

- [Project Check File](#1-project-check-file)
- [Run Artifacts](#2-run-artifacts)
- [Source Boundary](#3-source-boundary)
- [Read the Official Scan Hierarchically](#4-read-the-official-scan-hierarchically)
- [Interpret Signals Separately](#5-interpret-signals-separately)
- [Repair Loop](#6-repair-loop)

## 1. Project Check File

Keep `checks.json` small and project-specific:

```json
{
  "project_root": ".",
  "template_entry": "template.typ",
  "entry_symbol": "robomech",
  "font_paths": ["/mnt/c/Windows/Fonts"],
  "bibliography_data": "references.bib",
  "comparison_dpi": 300,
  "fixtures": [
    {
      "id": "official",
      "kind": "official",
      "source": "fixtures/official.typ",
      "reference_pdf": "evidence/official.pdf",
      "required_text_file": "evidence/official-required.txt",
      "geometry_tolerance_pt": 0.1,
      "text_thresholds": {
        "reference_coverage": 0.95,
        "candidate_precision": 0.95,
        "ordered_similarity": 0.90
      }
    },
    {
      "id": "frontmatter-long",
      "kind": "frontmatter",
      "source": "fixtures/frontmatter-long.typ",
      "ordered_text": ["FRONTMATTER-LAST", "BODY-FIRST"]
    },
    {
      "id": "body-flow",
      "kind": "body-flow",
      "source": "fixtures/body-flow.typ",
      "minimum_pages": 2,
      "page_flows": [
        {"start": "LIST-START", "end": "LIST-END", "following": "LIST-AFTER"},
        {"start": "TABLE-START", "end": "TABLE-END", "following": "TABLE-AFTER"}
      ]
    }
  ]
}
```

Exactly one fixture of each `kind` is allowed. All three must compile
successfully; there is no diagnostic outcome or capability inventory.

Paths are relative to `project_root`, which is relative to `checks.json`.
`template_entry`, fixture sources, reference PDFs, and required-text files stay
inside the project root. Font paths may be absolute.

Optional fixture checks are:

- `required_text`: literal snippets that must occur after Unicode normalization
  and whitespace removal;
- `required_text_file`: one required snippet per nonblank line;
- `ordered_text`: snippets that must occur in the declared order;
- `minimum_pages`: positive lower page bound;
- `page_flows`: markers that occur once, cross from start to end page, and place
  the end before following content.

The body-flow fixture declares at least two flows: one for a naturally crossing
list and one for a naturally crossing table. The checker does not assign those
meanings from marker names; the project does. If the official source contains a
display equation or a figure/caption, body-flow must also exercise that standard
structure. When `bibliography_data` is declared, official and body-flow both use
standard citation plus bibliography semantics and consume the file. Declare
`bibliography_style_asset` only for a positively justified project style file;
built-in style names need no asset declaration.

The official fixture additionally declares its reference, geometry tolerance,
and normalized-text thresholds. Geometry tolerance cannot exceed `0.1 pt`, text
thresholds cannot be weaker than coverage `0.95`, precision `0.95`, and ordered
similarity `0.90`, and `comparison_dpi` cannot be below 300. The checker derives
the embedded face set from the reference; there is no worker-selected required
font list. It fails exact normalized set differences, ordered word-anchor or
numbered-equation drift, and local ink/rule/image structure displacement above
the fixed `0.25 pt` cap on any page. These are structural preflights, not pixel
identity or visual acceptance. Use the comparator directly for a disposable
lower-DPI diagnostic.

Every locked official snippet must occur in the reference PDF before it is
checked in the candidate. Font normalization removes only subset prefixes and
conservatively normalizes spelling/case; it does not collapse styles or guess
aliases. Add an equivalence only after positive evidence establishes one.

## 2. Run Artifacts

Run:

```bash
python3 <skill-dir>/scripts/check_fixtures.py checks.json audit/run-001
```

The output contains:

- `report.json` and `summary.txt`;
- compiler logs and Typst dependency JSON;
- all three candidate PDFs;
- page-separated extracted text;
- PDF geometry and embedded-font observations;
- official normalized content metrics;
- reference-derived font-face results and every-page word, equation, and
  local-ink/rule/image preflights;
- line-evidenced source layout inventories and standard-structure observations;
- bibliography data/style dependency consumption when declared;
- the official comparator `scan/index.json` and page details.

`report.json` also contains `repair_targets`, a deterministic queue capped at
about twelve entries. It summarizes existing evidence rather than adding a new
gate: reference/candidate embedded faces, each failing page's earliest and
maximum same-line coherent token-cluster median, equation body/number anchors,
and one representative local band/ink delta per failing page. Isolated raw word
maxima remain diagnostic because repeated tokens can have different semantic
locations. `summary.txt` prints the actionable targets compactly
with a correction direction. A target is a causal repair hypothesis, not a
completion decision.

Hashes bind the report to the current config, template, sources, reference,
required-text file, dependencies, logs, PDFs, and comparison index. The checker
does not ask the author to copy hashes into the config.

## 3. Source Boundary

The source lint checks only mechanically observable ownership:

- template and fixture are distinct;
- the template exports the project-declared `entry_symbol`;
- each fixture imports that symbol, directly or through `*`, from the exact
  template path;
- each fixture references the symbol without redefining it;
- Typst's dependency graph contains the template;
- a fixture does not call a private symbol defined by that template.

It accepts both `.with(...)` and `doc => wrapper(..., doc)` forms. It does not
inspect metadata fields, ban page breaks or widths, or decide whether an author
choice belongs in the fixture. Separately, `source_inventory` reports each
layout-sensitive construct and absolute dimension with a source line. Classify
those observations in the work log; the inventory is not a deny-list.

## 4. Read the Official Scan Hierarchically

Start with `comparison/index.json`:

1. page count and page correspondence;
2. per-page geometry and rotation;
3. normalized and raw extracted text;
4. embedded font-family sets;
5. render producer and tool versions;
6. page ranking and hotspot findings.

Then request high-resolution detail for the most semantically risky findings:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py detail \
  audit/run-001/comparison \
  audit/detail-title \
  --finding <finding-id> --dpi 300
```

The comparator does not register or rescale pages. Geometry displacement,
wrapping drift, and missing ink remain visible.

The batch checker consumes this scan mechanically. It fails when any ordered
word anchor, numbered equation body/number anchor, local tile ink centroid or
extent, or dense local row/column band moves by more than `0.25 pt`; changed ink
presence and insufficient every-page spatial coverage also fail. The reference
and the source-observed structure count select the anchors, not a worker list.
This connects coarse rules, images, and block drift to status without certifying
aesthetics.

## 5. Interpret Signals Separately

| Signal | Establishes | Does not establish |
|---|---|---|
| Clean compile and dependency | fixture consumed the template | correct API meaning |
| Required/order/page-flow text | visible tail and ordering behavior | visual placement quality |
| Page geometry | paper boxes and rotation | content alignment |
| Reference-derived font inventory | exact normalized embedded face set | identical glyph rasterization |
| Word/equation/local-ink preflight | bounded structural displacement on every page | aesthetic or pixel acceptance |
| Pixel/ink hotspot | difference location and magnitude | cause or importance |
| Text coverage and order | content comparability | visual equivalence |

Inspect frontmatter, the frontmatter/body transition, equation numbers, caption
prefixes, table rules, list/table tails, references, and the final page whenever
they occur. Classify the cause before editing.

## 6. Repair Loop

For a failure:

1. fix missing or wrong official content before layout;
2. fix missing fonts before tuning geometry;
3. locate the highest-risk visual difference;
4. map it to the structural source and template rule;
5. change the rule, not a sample-only offset or public flag;
6. rerun the affected fixture;
7. rerun all three and the official comparison.

Before step 5, predict which signed reference→candidate delta the governing rule
will reduce. After the focused rerun, require that residual to move toward zero.
Then require no regression on any other official page or any of the three
fixtures. If the prediction fails, reject the hypothesis and reclassify the
cause; do not preserve it with a sample-only offset or a weaker threshold.

When a reviewer finds an escaped defect, add the smallest positive check to the
existing fixture that owns the behavior. Avoid creating a universal profile or
new permanent fixture family for a single publication defect.

Do not call the result ready while source-inventory spacing, font, or placement
observations remain unclassified or unexplained one-off compensation remains.
