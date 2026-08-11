# Figures

**Requires** — Established body/column insertion context, page flow, inherited
typography, and evidence for asset identity and figure semantics.

**Owns** — Figure placement, sizing, caption composition, numbering, labels,
and figure-reference rendering.

**Emits** — A standard figure route that preserves publication policy for
single/multiline captions and justified asset/flow variations.

**Recheck** — Intrinsic and displayed image extent, single/column/page span,
caption wrapping, figure-caption attachment, reference prose, and following
column/page flow.

Process one direct child at a time after establishing Figures: Images, Captions,
then Figure references. The reference route is closed against the already
observed caption supplement and counter. Close the figure after their
composition preserves numbering, attachment, placement, and downstream flow.
When a caption prefix and body share the first line, read [run-in labels with
aligned continuation lines](typst-tip-run-in-label-continuation.md).

- **Figures [C]** — semantic kind, placement/float policy, counter/reset,
  label/reference semantics, keep with caption, page/column span.
  - **Images [C]** — source asset and intrinsic dimensions; displayed
    width/height; aspect ratio, fit, crop, scaling/interpolation,
    alignment, border/stroke, alt text.
  - **Captions [C,T]** — position; kind/prefix, counter and number format,
    separator/punctuation; single/multiline alignment; shared width;
    distance to object and following flow.
  - **Figure references [T]** — actual author syntax; localized prose
    prefix and number format; spacing and link target; distinction from
    the caption supplement; observed inline result.

Activate the relevant sizing, wrapping, placement, or span change in the
consolidated variation. Predict which extent changes and which relationships
remain invariant before tuning geometry.
