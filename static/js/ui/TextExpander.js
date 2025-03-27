function TextExpander(root) {
  const seeMoreContent = root.querySelector('.see-more-content')
  const seeMoreCta = root.querySelector('.see-more-cta')

  if (!seeMoreContent || !seeMoreCta) return

  seeMoreCta.textContent = gettext('Voir plus')
  seeMoreCta.setAttribute('aria-expanded', false)

  seeMoreContent.hidden = true

  // Button event listener, when clicked upon, text should be displayed/hidden
  seeMoreCta.addEventListener('click', () => {
    seeMoreContent.classList.toggle('text--expanded')

    const isExpanded = seeMoreContent.classList.contains('text--expanded')

    seeMoreCta.textContent = isExpanded ? gettext('Voir moins') : gettext('Voir plus')
    seeMoreCta.setAttribute('aria-expanded', isExpanded)
    seeMoreContent.setAttribute('aria-expanded', isExpanded)
    seeMoreContent.hidden = !isExpanded
  })
}

export default TextExpander
