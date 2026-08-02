# Typst Template Implementation Patterns

Read this reference when converting observed document behavior into reusable
Typst rules. The examples show responsibility placement, not a required API.

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

An API name does not fix a responsibility leak. If authors must understand an
internal offset or pagination trick, the control is still in the wrong layer.

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

Do not normalize both into a universal metadata record.

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
pagination behavior. Create a helper only when standard syntax cannot represent
the author-facing meaning cleanly.

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

Do not measure at full page width and reuse the result inside a narrower parent.
Preliminary measurement can also expose zero or unbounded dimensions; defer a
decision until the local layout provides finite space.

## 4. Let Breakable Content Break

Tables and lists should normally use natural flow. Keep their internal start and
end markers in the content when testing a page crossing. External page breaks
prove only that the surrounding document reached another page.

Do not place a breakable table in a fixed-height or unbreakable wrapper. If a
caption or repeated header needs special treatment, preserve the underlying
table as a table and style that structure.

Atomic figures and equations need a different rule:

- keep the object whole when it fits the usable local region;
- scale only when the publication rule permits scaling;
- reject it with an actionable message when it cannot fit;
- never silently clip it.

## 5. Make Frontmatter Grow Naturally

Model source-supported optional fields explicitly, but let absent fields remove
their own spacing. Measure a title or author block when the publication requires
it to remain atomic. Avoid fixed heights copied from the official fixture: a
longer title must increase the block and move the body transition.

When this behavior is uncertain, render a focused frontmatter variation that
changes only this dimension. Use it to judge whether the API value is consumed
and the first body content remains visible and ordered after the frontmatter.

## 6. Keep Calibration Private

Publication-fixed values can be named private constants with a source note:

```typst
#let _caption-gap = 3.2mm // official rule, section 4.2
```

A raster-measured value without normative provenance can still be a private
calibration value, but verify it with varied content before treating it as a
general rule. Do not export `_caption-gap`, `placement`, `continuation`, or an
equivalent flag solely to position one sample.

## 7. Recheck Downstream Flow

Typography and vertical extent are coupled. After changing title, heading,
equation, caption, table, or reference layout:

1. compile the affected fixture;
2. inspect the changed region;
3. inspect following content and the final page;
4. rerender the relevant content variations;
5. rerun the official all-page comparison when the change can affect it.

Local visual improvement is not sufficient when it changes pagination.
