# Typst Template Implementation Patterns

Read this reference when converting observed document behavior into reusable
Typst rules. Choose the API from the target evidence; the examples illustrate
responsibility placement.

## Contents

- [Place Responsibilities by Meaning](#1-place-responsibilities-by-meaning)
- [Prefer Standard Elements](#2-prefer-standard-elements)
- [Measure at the Local Width](#3-measure-at-the-local-width)
- [Let Breakable Content Break](#4-let-breakable-content-break)
- [Make Frontmatter Grow Naturally](#5-make-frontmatter-grow-naturally)
- [Keep Calibration Private](#6-keep-calibration-private)
- [Recheck Downstream Flow](#7-recheck-downstream-flow)

## 1. Place Responsibilities by Meaning

| Meaning | Preferred location |
|---|---|
| Page geometry, type rules, spacing, numbering, overflow policy | template |
| Title, authors, abstract, keywords, selected assets | usage file |
| Deliberate line break or table width chosen for this document | usage file |
| Ordinary heading, figure, table, equation, list, label, reference | standard Typst syntax |
| Repeated project-specific semantic structure | project-named helper |
| Literal wording from one official sample | official fixture |
| Non-public producer guidance excluded by user decision | recorded comparison mask |

Use the ownership already assigned through `SKILL.md`. Place author semantics in
the usage route, publication policy in the template, official literals in the
official fixture, and comparison exclusions in an exact recorded mask. Keep
internal offsets and pagination rules behind the author-facing API, and keep
neighboring publication content visible around every mask.

Derive the document wrapper from the structural source. These are equally valid
when their projects support them:

```typst
#import "journal.typ": journal-paper
#show: journal-paper.with(title: [...], author-block: [...])
```

```typst
#import "conference.typ": conference
#show: doc => conference(
  title-ja: [...],
  title-en: [...],
  doc,
)
```

Preserve the wrapper shape supported by the target structural source.

## 2. Prefer Standard Elements

Style semantics through show rules:

```typst
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => project-heading(it)

#show figure.where(kind: table): set figure.caption(position: top)
#show figure.caption: it => project-caption(it)
```

Keep headings as `heading`, tables as `table`, and equations as
`math.equation`. This preserves counters, labels, references, queries, and
pagination behavior. Start each route by recording the ordinary author syntax,
the target rendered output, and the observed output after template styling.
Create a helper when the source contains a concrete additional manuscript
semantic beyond standard syntax. Treat source-language convenience macros as
evidence for output policy and test the corresponding standard Typst route.

## 3. Measure at the Local Width

Content can wrap differently inside a grid, column, or narrowed block. Measure
where the object will render:

```typst
#let guarded(body) = layout(size => {
  let extent = measure(body, width: size.width)
  assert(extent.width <= size.width, message: "Object is too wide")
  body
})
```

Measure inside the actual parent layout after it provides finite local space.
Defer calculations that encounter preliminary zero or unbounded dimensions to
that finite layout pass.

## 4. Let Breakable Content Break

Keep breakable tables and lists in natural flow. Place internal start and end
markers in their content when testing a page crossing so the render shows the
element itself traversing the boundary.

Preserve the underlying table as a breakable `table`, and style captions and
repeated headers through that structure.

Atomic figures and equations need a different rule:

- keep the object whole when it fits the usable local region;
- apply evidenced publication scaling when it can fit through that policy;
- emit an actionable error when the object exceeds the evidenced fit policy.

Produce either the complete object under the evidenced fit/scale policy or the
actionable error.

## 5. Make Frontmatter Grow Naturally

Emit each source-supported optional field together with its adjacent spacing in
the same content branch. Measure a title or author block when the publication
requires it to remain atomic. Derive frontmatter height from its content so a
longer title increases the block and moves the body transition.

When this behavior is uncertain, render a focused frontmatter variation that
changes only this dimension. Use it to judge whether the API value is consumed
and the first body content remains visible and ordered after the frontmatter.

## 6. Keep Calibration Private

Publication-fixed values can be named private constants with a source note:

```typst
#let _caption-gap = 3.2mm // official rule, section 4.2
```

A raster-measured value can serve as a private calibration value after varied
content confirms its reusable role. Keep `_caption-gap`, placement, continuation,
and similar sample-positioning controls private in the file assigned by the four
owner categories in `SKILL.md`.

## 7. Recheck Downstream Flow

Typography and vertical extent are coupled. After changing title, heading,
equation, caption, table, or reference layout:

1. compile the affected fixture;
2. inspect the changed region;
3. inspect following content and the final page;
4. rerender the relevant content variations;
5. rerun the official all-page comparison when the change can affect it.

Evaluate the repair through the changed region, affected downstream pagination,
and relevant author variations together.
