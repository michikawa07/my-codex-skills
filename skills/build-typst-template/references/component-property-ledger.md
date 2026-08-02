# Document Element and Parameter Checklist

Use this as a thinking aid while reading the actual sources. Copy useful prompts
into scratch notes in whatever form helps the task. It is not a required
artifact, fixed schema, exhaustive taxonomy, or completion gate. Add unknown
elements under their real parent and omit branches that evidence does not
support.

First inspect the source structure and rendered pages; then choose semantics,
targets, author syntax, and Typst rules from that evidence.

## Parameter Bundles

Apply **C** to every container: width and height policy (fixed, intrinsic,
fill-parent, measured, min/max); horizontal and vertical alignment; padding or
insets on every edge; internal and external spacing; columns, gutters, flow,
overflow, keep/break, and page behavior.

Apply **T** to every text-bearing element: font family, face, and fallback;
size; weight and style; glyph horizontal scale or character width; tracking and
word spacing; color and baseline/vertical position; horizontal/vertical
alignment; line pitch; available width, wrapping, and explicit breaks; first,
hanging, left, and right indents; space before and after; keep-with-next,
keep-lines, widow/orphan, and page-break behavior.

For each applicable prompt, first inspect normative or structural values,
repeated instances, and visual measurements; then choose the semantic owner,
target, confidence, author syntax, and implementation. A scratch note may be a
sentence, table, annotated crop, or source comment.

## Hierarchical Element Prompts

- **Document [C]** — document metadata and language; authoring boundary;
  section/page sequence; global counters, outlines, labels, links, and color.
  - **Page [C]** — paper size and orientation; margins/content box; background;
    first/odd/even page variants; numbering and page counter resets.
    - **Header [C,T]** — semantic content, fields, running-title rules, rule or
      stroke, distance from page/body, first/odd/even visibility.
    - **Footer [C,T]** — semantic content, page-number format/alignment, rule or
      stroke, distance from page/body, first/odd/even visibility.
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
  - **Body container [C]** — usable region; section flow; frontmatter
    transition; page and column balancing policy.
    - **Columns [C]** — count, widths, gutter, rules, balance, span behavior,
      reading order, column/page breaks.
      - **Paragraphs [T]** — paragraph semantics; justification and hyphenation;
        first/hanging indent; inter-paragraph policy.
      - **Heading level 1..N [C,T]** — identify every observed level separately;
        hierarchy, counter/reset, numbering/prefix/suffix, punctuation, outline
        and bookmark behavior; run-in/block form; keep with following content.
      - **Lists [C,T]** — ordered/unordered/description semantics; nesting;
        marker or counter style, prefix/suffix, alignment, marker-body gap,
        counter reset/continuation, page flow.
        - **Items [C,T]** — marker attachment; item indentation and spacing;
          paragraph children; keep/break and split behavior.
      - **Equations [C,T]** — inline/display semantics; math font and glyph
        treatment; alignment and indent; counter/reset, number format and
        prefix/suffix; number position; label/reference semantics; keep/break.
      - **Figures [C]** — semantic kind, placement/float policy, counter/reset,
        label/reference semantics, keep with caption, page/column span.
        - **Images [C]** — source asset and intrinsic dimensions; displayed
          width/height; aspect ratio, fit, crop, scaling/interpolation,
          alignment, border/stroke, alt text.
        - **Captions [C,T]** — position; kind/prefix, counter and number format,
          separator/punctuation; single/multiline alignment; shared width;
          distance to object and following flow.
      - **Tables [C]** — semantic kind; total width; column count and width
        policy; grid/stroke sides, thickness, style and color; header repetition;
        counter/reset, label/reference semantics; caption position; page/column
        span and break behavior.
        - **Rows [C]** — header/body/footer role; natural/min/fixed height;
          separators; keep/split/repeat behavior; zebra/background styling.
          - **Cells [C,T]** — column/row span; content kind; width/height policy;
            padding; horizontal/vertical alignment; wrapping and overflow;
            background; per-edge strokes.
      - **Citations [T]** — citation key/target semantics; numeric/author-year
        form; cluster ordering and ranges; prefix/suffix, locator, brackets,
        punctuation, spacing, links, and line breaking.
  - **References [C,T]** — bibliography source and placement; heading and
    outline behavior; sorting, filtering, numbering/counter, columns and page
    flow.
    - **Bibliography entries [C,T]** — author/title/container/year and other
      field semantics; label/number format; punctuation and emphasis; hanging
      indent; entry spacing; URL/DOI/link treatment; wrapping, keep, and breaks.

## Cross-Checks

Inspect relationships as well as isolated elements: inherited versus local
fonts, parent content width versus child wrapping, spacing collapse, baseline
alignment between mixed content, counter continuity, label/reference targets,
frontmatter-to-body transition, column/page continuation, and final-page tails.
Then vary the smallest relevant content dimension to test whether the chosen
rule generalizes.
