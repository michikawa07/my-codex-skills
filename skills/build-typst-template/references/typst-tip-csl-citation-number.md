# CSL numeric citation presentation

Read this when a numeric citation's brackets or vertical position differ from
the target. CSL means Citation Style Language. Keep the manuscript route as
standard Typst `@key` or `#cite(...)` syntax; let the CSL style format its
number, link, cluster, and locator.

Use a built-in CSL style when it already matches. For inline square brackets,
use this citation layout in a custom CSL style:

```xml
<citation>
  <layout prefix="[" suffix="]" delimiter=", ">
    <text variable="citation-number"/>
  </layout>
</citation>
```

For consecutive parenthesized numbers at the upper right, format each number
and raise the whole citation layout:

```xml
<citation>
  <layout delimiter="" vertical-align="sup">
    <text variable="citation-number" prefix="(" suffix=")"/>
  </layout>
</citation>
```

Set the bibliography entry label separately under `<bibliography>`; the
`<citation>` layout controls prose citations only. Recompile a single citation,
a multiple-key citation, a locator, and a reversed citation order. Confirm
their visible form, links, numbering, and bibliography order together.
