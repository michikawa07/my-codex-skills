# Typst Template Implementation Decisions

Use these decisions to convert observed layout behavior into reusable Typst
rules. Each branch records observed failure → structural cause → positive rule →
mechanical fixture/evidence → remaining classification judgment. Verify each
selected branch with both an official fixture and a boundary fixture.

## 1. Public API Placement

The failure mode is responsibility leakage: the document author must understand
calibration or pagination internals to use ordinary content. Renaming the leaked
flag or wrapper leaves that failure unchanged.

| Content or behavior | Place it here | Verification |
|---|---|---|
| Heading, figure, table, equation, list, label, reference | standard Typst element plus template `set`/`show` | fixture uses only the standard construct |
| Title, author, affiliation, abstract, keyword metadata | document wrapper | nominal and long-front-matter fixtures |
| Deliberate author choice such as a line break, image width, table columns | usage file | value has a content meaning visible to the author |
| Layout calibration, page-top spacing, measured hang, overflow policy | private template function | usage fixture contains no corresponding control |
| New semantic object absent from Typst | semantic helper | helper works for multiple contents and has a boundary fixture |
| One sample's unique visual arrangement | fixture content plus a general layout rule | another sample exercises the same rule |

When ordinary source syntax expresses the author’s meaning, the fixture uses
that syntax and the template supplies styling. When a recurring structure has
meaning absent from Typst, create a named semantic helper and give it nominal
and boundary fixtures. When a difference is only one sample's geometry, inspect
measurement and flow before choosing an interface.

## 2. Variable Extent and Spacing

The recurring failure is compensating one parameter with another: fixed boxes,
negative moves, and spacer pairs can match a one-line sample while hiding the
true paragraph or object extent.

| Condition | Layout rule | Test |
|---|---|---|
| Content can wrap or gain superscripts | return its natural measured height | add one line and a superscript |
| Source defines a minimum line or row height | use the minimum plus measured overflow | short and tall contents share the same rule |
| Source defines paragraph before/after spacing | implement that spacing at the paragraph boundary | normal flow and page-top cases |
| Position depends on an object's actual bounds | measure the rendered object | root, fraction, presenter marker, title glyph |
| A prior value appears only as an offset that cancels another offset | recover the underlying paragraph/object rule | remove either offset in a temporary branch and inspect causality |

Use the full-page comparison after changing leading or paragraph spacing because
small differences accumulate into later page breaks.

Read compact all-page scan evidence before opening a full-resolution crop. Scan
measurements distinguish signal kinds; source and rendering evidence still
classify whether the cause is content, font/toolchain, geometry, ink, or layout.
Select detail by semantic risk, then promote a recurrent meaningful hotspot into
a region contract.

## 3. Titles, Authors, and Affiliations

| Condition | Layout rule | Test |
|---|---|---|
| Title line count varies | natural-height line stack with the source line pitch | one, two, and three lines in each language |
| The publication expects an author-selected break | preserve that explicit break as content | compare a temporary reference variant from the original application |
| Author names contain affiliation superscripts | measure the intended line box separately from the superscript glyph | Japanese-to-Romanized author gap and baseline |
| Presenter is marked by a glyph | match glyph family, size, outline, and baseline | high-resolution presenter-marker region |
| Author or affiliation count grows | let the block push following content by its measured height | many-author and many-affiliation fixture |

Measure Japanese title, English title, Japanese authors, Romanized authors, and
affiliations as separate anchors. A full-page average can hide a collision at one
boundary.

## 4. Inline and Display Mathematics

The source's mathematical structure governs the output. Similar-looking glyphs
can have different semantics and different layout boxes.

| Source structure | Typst representation | Verification |
|---|---|---|
| Literal slash expression | horizontal slash form | expected expression text and high-resolution crop |
| Stacked fraction | explicit vertical fraction | measured height and following-rule clearance |
| Parenthesized numerator/denominator around a slash | explicit parentheses plus horizontal fraction | parentheses, slash, and baseline all visible |
| Mathematical square root | `sqrt` structure | root bar covers the intended expression |
| Literal root symbol followed by math | text glyph plus math content | no generated overbar |
| Display equation with number | measure formula and number field together | short, tall, wide, and page-boundary fixtures |

When a template internally redraws display math through an inline context, set
the intended fraction style inside that renderer. The effective inner context,
rather than the author's outer syntax, controls the result.

Use the normal reserved display height for nominal equations and add measured
overflow for taller equations. Move an atomic equation as one object when the
remaining page space is smaller than its measured height. Emit a diagnostic when
formula plus number field exceeds the usable width.

## 5. Figures, Captions, and Grouped Content

| Condition | Layout rule | Test |
|---|---|---|
| Image uses a relative width | resolve it against the actual containing block | full-width and narrow-parent fixtures |
| Preliminary measurement returns zero or unresolved dimensions | defer ratio-based sizing until dimensions resolve | relative and zero-premeasurement fixtures retain following text |
| Image fits its local container | preserve natural aspect ratio | fixed and relative widths |
| Atomic figure plus caption fits a page | keep the measured pair together | page-boundary fixture |
| Figure body can break, such as a long table | make the figure element itself breakable | final row and following end marker survive |
| Caption prefix varies in digits or numbering state | measure the rendered prefix and derive the hang | numbered, multi-digit, and unnumbered captions |
| Project already defines a grouping primitive | reuse it when its counter semantics match | independent figures and true subfigures keep correct counters |

Choose grouping by semantic counter structure. Two independent tables in a row
remain two independent table figures; a subfigure primitive represents a parent
with children even when the visual arrangement looks similar.

## 6. Tables

The recurring failure is using row indices, fixed boxes, or baseline moves to
mask the height of roots, fractions, units, and wrapped cells. Those values match
one table while disconnecting rules from the content they enclose.

| Source property | Typst rule | Verification |
|---|---|---|
| Publication or author fixes column widths | keep those horizontal widths as table content | compare table width and wrapping |
| Row height expands with content | natural cell height plus shared insets | normal, wrapped, root, fraction, and subscript cells |
| Source declares a minimum row height | minimum plus measured overflow | short and tall cells |
| Header contains quantity and unit lines | preserve their distinct structures and measure the tallest cell | brackets, unit baseline, lower-rule clearance |
| Vertical rules span the complete table | use the table's full default row range | header and continued-page rule continuity |
| Rule length follows table width | derive it from the laid-out table width | narrow and wide tables |
| Table crosses pages | make the containing table figure breakable | repeated header/rules, final row, end marker |

A useful starting rule is:

```typst
#show figure.where(kind: table): set block(breakable: true)
```

Verify this rule with the supported Typst version and every custom `figure` show
rule. Styling an outer wrapper alone can leave the actual figure atomic.

Treat units, brackets, exponent rows, and table data as content-equivalence
requirements. Pixel metrics cannot prove that a missing bracket is semantically
acceptable.

## 7. Lists and Page Flow

| Condition | Layout rule | Test |
|---|---|---|
| Standard list crosses a page | preserve one continuous standard list | sequence and end marker survive |
| A short tail would be isolated | keep the measured short tail together | one-item tail fixture |
| The tail itself exceeds a page | allow it to split naturally | oversized-tail fixture |

The template owns page-flow behavior. The author keeps writing the same list
syntax before and after a page break.

## 8. References and Bibliography

| Condition | Layout rule | Test |
|---|---|---|
| Manual reference number gains digits | reserve a measured or policy-defined number field | `(1)`, `(10)`, `(100)` wrap to the same body start |
| Page range exists | render the approved singular/plural page label | complete expected bibliography entry |
| Electronic article identifier exists | store and render it as an article identifier | entry contains the approved identifier phrase |
| Document language changes locale selection | define required CSL terms explicitly | compile the golden bibliography under each supported language |
| Word and Typst use the same family but different advances | compare anchors and wrapping before changing tracking | arbitrary long entries retain stable wrapping |

Compile every supported bibliography item type in one golden fixture. Require
complete expected entry snippets rather than testing only for the absence of a
known bad word.

## 9. Fonts and Rendering Environment

| Observed state | Valid use |
|---|---|
| Required families resolve and appear in the candidate PDF | visual geometry calibration |
| Required family is unavailable or compilation falls back | source inspection and diagnostic experimentation only |
| Same family appears in both PDFs but glyph edges differ | compare anchors, baselines, and line wrapping to classify shaping |

Source inspection is always allowed. If a required font is missing or
compilation emits a fallback warning, the verifier acceptance run cannot pass.
The project/template completion state is `blocked` until the required font
resolves without fallback. Any fallback compile or structural experiment based
on fallback output is diagnostic non-acceptance evidence only.

Record the exact Typst version, font paths, and embedded PDF font names in every
accepted run. A PDF created without the intended fonts is a different test input,
even when it compiles successfully.

## 10. Behavioral Evidence

For each capability, declare one positive result: `renders`, `paginates with a
tail marker`, or `fails with an actionable diagnostic`. Automation repeats those
facts; visual/text evidence locates a mismatch, and source/rendering evidence
classifies its cause. This preserves the observed requirements for natural-height
front matter, semantic math, content-height tables and full rules, local-width
images with zero-measure guards, continuous lists, and explicit bibliography
locale terms.
