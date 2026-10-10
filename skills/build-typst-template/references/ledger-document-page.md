# Document and Page

**Requires** — Closed evidence inventory and a shallow all-page pass identifying
page roles, major regions, reading order, and repeated regions.

**Owns** — The coordinate system, document-wide semantics, page sequence, and
page regions inherited by every later component.

**Emits** — Page geometry and variants, global semantic services, and the
available regions into which frontmatter and body flow render.

**Recheck** — Page geometry across the observed page roles, first/odd/even
behavior, page transitions, global counters/links, and body-region wrapping
after a page-level change.

For the active element, first record its semantic content, parent
and sibling relationships, fixed versus content-dependent behavior, inherited
versus local policy, author-editable fields, and invariants under ordinary
content changes.

Establish Page enough to define its children, then process Header and Footer in
the source-established order, using Header followed by Footer as the default.
Close Page after its coordinate system, page variants, Header, and Footer
preserve those page observations. Reopen Page when a child changes the body
coordinate system.

- **Document [C]** — document metadata and language; authoring boundary;
  section/page sequence; global counters, outlines, labels, links, and color.
  When visible title or author values also populate `document` metadata, read
  [display content and PDF metadata](typst-tip-display-content-metadata.md)
  before selecting their record and metadata-field types.
  - **Page [C]** — paper size and orientation; margins/content box; background;
    first/odd/even page variants; numbering and page counter resets.
    - **Header [C,T]** — semantic content, fields, running-title rules, rule or
      stroke, distance from page/body, first/odd/even visibility.
    - **Footer [C,T]** — semantic content, page-number format/alignment, rule or
      stroke, distance from page/body, first/odd/even visibility.
