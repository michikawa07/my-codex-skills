# Document and Page

**Requires** — Closed evidence inventory and a shallow all-page pass identifying
page roles, major regions, reading order, and repeated regions.

**Owns** — The coordinate system, document-wide semantics, page sequence, and
page regions inherited by every later branch.

**Emits** — Page geometry and variants, global semantic services, and the
available regions into which frontmatter and body flow render.

**Recheck** — Every reference page, first/odd/even behavior, page transitions,
global counters/links, and downstream wrapping after a page-level change.

For the active element, first recover its contract: semantic content, parent
and sibling relationships, fixed versus content-dependent behavior, inherited
versus local policy, author-editable fields, and invariants under ordinary
content changes.

Establish Page enough to define its children, then route one direct child at a
time: Header followed by Footer unless source order establishes the reverse.
Close Page after both active children preserve its contract. Reopen Page when
either child changes the body coordinate system.

- **Document [C]** — document metadata and language; authoring boundary;
  section/page sequence; global counters, outlines, labels, links, and color.
  - **Page [C]** — paper size and orientation; margins/content box; background;
    first/odd/even page variants; numbering and page counter resets.
    - **Header [C,T]** — semantic content, fields, running-title rules, rule or
      stroke, distance from page/body, first/odd/even visibility.
    - **Footer [C,T]** — semantic content, page-number format/alignment, rule or
      stroke, distance from page/body, first/odd/even visibility.
