// Architecture-only starting point. Derive every publication rule from the
// target evidence before delivery.
#let _render_body(body) = body

#let paper(
  body,
  title: none,
  authors: none,
  abstract: none,
  keywords: none,
) = {
  if title != none { title; parbreak() }
  if authors != none { authors; parbreak() }
  if abstract != none { abstract; parbreak() }
  if keywords != none { keywords; parbreak() }

  _render_body(body)
}
