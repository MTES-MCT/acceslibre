function FocusTo(root) {
  const trigger = root.querySelector('[data-focus-to]') ?? root
  const targetSelector = trigger.getAttribute('data-focus-to')
  const target = targetSelector ? document.querySelector(targetSelector) : root

  if (!trigger || !target) return

  trigger.addEventListener('click', () => {
    target.focus()
  })
}

export default FocusTo
