# TeX Figure and Table Placement

Apply these steps to both image figures and captioned tables:

1. Recover class/package defaults and each object's TeX placement options.
   Implement the defaults in the template, including float locations, spacing,
   page constraints, and the source environment's table-breaking behavior.
2. Specify `placement` explicitly on every `figure(...)` in `usage.typ` and
   retained variations, using the object's TeX options or effective default.
   Preserve the source intent of `h`, `t`, `b`, `p`, and `!` through the selected
   Typst placement and supporting layout rules.
3. Keep the original options in comparison fixtures. Verify both default and
   explicitly specified behavior at chapter openings and page transitions,
   including text flow, captions, numbering, and references. Resolve each
   difference in its owning template rule or per-object setting.
