# Natural Width Before Wrapped Extent

Use this when one publication form applies to a single-line object and another
form applies after wrapping, such as centered versus hanging captions.

Inside the actual local `layout`, compose and style the exact compact candidate.
Use unconstrained `measure(candidate).width` to decide whether it fits on one
line. Use `measure(candidate, width: size.width)` to inspect its wrapped extent:

```typst
#layout(size => {
  let natural = measure(candidate).width
  if natural <= size.width {
    render-single-line(candidate)
  } else {
    render-wrapped(candidate, size.width)
  }
})
```

Source evidence establishes whether the publication uses these two forms.
