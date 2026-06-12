// Priority order: querySelector returns the first match in document order, not
// in selector-list order, so each tier is queried separately.
const ERROR_SELECTORS = ['.fr-alert--error', '.fr-alert--warning', '.fr-message--error', '.fr-error-text']

function FocusOnLoad(node) {
  // When the page is rendered with validation errors, send focus to the first
  // error instead of the step title so the user lands on what needs fixing.
  const error = ERROR_SELECTORS.reduce((found, selector) => found || document.querySelector(selector), null)

  if (error) {
    if (!error.hasAttribute('tabindex')) error.setAttribute('tabindex', '-1')
    error.focus()
    return
  }

  // In the edit flow, steps are changed through the dropdown; keep focus on it
  // after the reload so the user can keep navigating.
  const stepSelect = document.querySelector('#contrib-edit-cta')
  if (stepSelect) {
    stepSelect.focus({ preventScroll: true })
  }
}

export default FocusOnLoad
