# Localized Standard References

Keep ordinary `@label` references as the author route. At a lexical boundary
where Japanese or another Unicode identifier character follows the label, use
the explicit standard form:

```typst
@fig:overview。
#ref(<fig:overview>)では次を示す。
#cite(<source-key>)によれば、
```

Implement localized wording in a template-owned `show ref` rule. Enter its
localized branch when `it.form == "normal"`, `it.supplement == auto`, and
`it.element` is a numbered target. Distinguish `math.equation`, `figure`, and
`figure(kind: table)`. Obtain target-location counters through:

```typst
counter(math.equation).at(element.location())
counter(figure.where(kind: element.kind)).at(element.location())
```

Format the number from target evidence, preserve the link with
`link(element.location(), ...)`, and return the original `it` for unhandled
forms. Derive reference prefixes and punctuation separately from caption
supplements. Extract equation, figure, and table prose references separately.

Re-probe the matching minimal case after an engine upgrade.
