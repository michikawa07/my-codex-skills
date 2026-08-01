# Component Property Ledger

Use this ledger before writing template rules. Its purpose is to reconstruct a
positive, element-level specification from the project's evidence. It is not a
generic publication profile and it is not a post-hoc failure list.

## 1. Enumerate Components in Reading Order

Walk the authoritative source and reference in this order, retaining repeated
semantic roles and each observed heading level:

1. page, header, and footer;
2. each localized title/subtitle (Japanese/English when evidenced);
3. each localized author group (Japanese/English when evidenced), including any
   presenter mark;
4. affiliations;
5. abstract;
6. keywords;
7. ordinary body paragraph;
8. each heading level separately;
9. list;
10. display equation and its number;
11. figure and caption;
12. table and caption;
13. citation and bibliography.

For every known role, record either `present` or `verified absent` with evidence.
If the source contains another semantic role, add it in its actual reading-order
position; do not force it into the nearest known name. A role or property that
has not been checked is `unresolved`, not absent.

DOCX XML, TeX commands, and PDF geometry provide facts, not semantic labels.
Codex assigns the semantic role by reading the source and rendered reference.
Record that judgment and its evidence explicitly. In particular, a DOCX style
name, `textAlignment`, or paragraph index does not by itself establish a title,
horizontal alignment, or author-facing API.

## 2. Record Properties, Not Just Components

Use one ledger row per property so provenance and uncertainty are not hidden in
a large component summary:

```text
order | component/semantic range | property | source evidence | confidence |
target value | standard Typst author syntax | implementation choice |
official crop/anchor | variation fixture
```

For each `present` component, cover every applicable item below:

- semantic range: the exact text, object, repeated class, page region, or
  transition governed by the row;
- font: family, face, size, weight, style, tracking, and width/scale;
- horizontal alignment, baseline, and vertical alignment;
- color when evidenced;
- line behavior: leading, available line width, wrapping, and intentional
  breaks;
- block behavior: width, inset/indent, space above, space below, and break/keep
  policy;
- element-specific behavior: numbering, equation-number position, prefix,
  strokes, table grid/column widths, and cell padding where applicable;
- table row height, cell vertical alignment, and repeated-header behavior where
  applicable;
- figure intrinsic extent and displayed extent;
- flow: relation to the preceding/following element, columns, and pages;
- source evidence: file, style/instance/line/page, extracted fact, and visual
  crop or anchor;
- confidence: `direct` for an explicit normative or editable value, `repeated`
  for consistent behavior across occurrences, `inferred` for a testable
  interpretation, or `unresolved`;
- positive target value, including its unit and coordinate system;
- standard Typst author syntax or evidenced wrapper argument;
- chosen implementation rule;
- official crop/anchor used to remeasure it;
- the frontmatter or body-flow variation that challenges the rule.

Do not start implementation while any reference-present component has a blank
applicable property, an unresolved semantic range, an unsupported target value,
or an unexplained implementation choice. A single bbox or pixel hotspot cannot
fill a property row without structural/source evidence.

## 3. Choose the Least Specialized Implementation

For each completed component, use this ladder and record the first rung that can
express the evidenced rule:

1. standard Typst `set`/`show` rules and standard elements;
2. `measure`, `layout`, or `context` for genuinely content-dependent behavior;
3. a local helper only for a repeated project semantic gap that standard
   elements cannot express clearly;
4. an external library only when a documented requirement remains unmet and
   the dependency's concrete benefit is recorded.

Select the rung from the positive semantic/property requirement. A pixel
residual supplies a measurement target, not a technology choice. Author content
remains in author syntax; reusable publication policy remains in the template.

Implement and positively match components in dependency order:

```text
page + fonts
  -> each frontmatter element, one by one
  -> body paragraph + each heading level
  -> equation + number
  -> figure + caption
  -> table + caption
  -> citations + bibliography
```

After each element, compile the official fixture and compare its declared crop,
anchors, font facts, and flow target before integrating the next element. Then
rerun every official page and both variation fixtures. A downstream element
must not be used to compensate for an upstream mismatch.

## 4. Completion Evidence

The ledger is complete only when:

- every known and newly discovered semantic role is `present` or `verified
  absent` with evidence;
- all applicable property rows for present roles are resolved;
- the official measurement reaches its positive target across every page;
- the corresponding variation exercises the same governing rule successfully;
- generated bibliography data and any positively justified bibliography style
  asset are consumed through standard citation/bibliography semantics;
- no fixture-only compensation is carrying template policy.

The absence of checker failures does not replace this evidence.
