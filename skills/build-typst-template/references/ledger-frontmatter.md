# Frontmatter

**Requires** — Established page region, reading order, inherited typography,
and the evidence-backed author-editable metadata fields.

**Owns** — The full frontmatter composition, optional-field collapse, atomic or
growing behavior, and child relationships.

**Emits** — A content-dependent frontmatter extent and a stable transition into
the body container.

**Recheck** — Short and multiline titles, changed author counts and affiliation
links, long abstract/keywords, omitted optional fields, and the body start.

Process one direct child at a time in evidenced reading order: Title, Subtitle,
Authors, Affiliations, Abstract, then Keywords when present. Presenter mark is
opened as an Authors child. Close each child against its immediate siblings;
close the container after the composition preserves optional collapse and the
body transition.

For linked author and affiliation records, read [stable author and affiliation
identifiers](typst-tip-author-affiliation-identifiers.md). When the same title
or author record supplies visible content and PDF metadata, read [display
content and PDF metadata](typst-tip-display-content-metadata.md). For an
Abstract or Keywords label that shares the first line with its body, read
[run-in labels with aligned continuation
lines](typst-tip-run-in-label-continuation.md).

- **Frontmatter container [C]** — reading order; optional-field collapse;
  atomic versus growing behavior; transition into body.
  - **Title [T]** — semantic/localized variants; grouping; prominence;
    punctuation; optionality.
  - **Subtitle [T]** — relation to title; optionality and collapsed spacing.
  - **Authors [C,T]** — order, grouping, separators, line formation; links to
    affiliations; correspondence semantics.
    - **Presenter mark [T]** — glyph/string, attachment target, placement,
      repetition, legend meaning, and interaction with wrapping.
  - **Affiliations [C,T]** — marker/link semantics; grouping, order,
    separators, and line formation.
  - **Abstract [C,T]** — label/prefix, language variants, run-in versus block,
    width and paragraph behavior.
  - **Keywords [C,T]** — label/prefix, separator and punctuation, item order,
    line formation, optionality.

For every text-bearing child, apply the **T** vocabulary from the router. For
every child container, apply **C**. Derive child
rules and content-dependent spacing from structural and rendered evidence, with
publication policy owned by the template.
