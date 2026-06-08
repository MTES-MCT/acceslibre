// Messages rendered server-side sit in the DOM before the page loads, so their
// role="alert"/aria-live region never mutates and assistive tech stays silent
// Inject the text after load to trigger the live-region announcement.
function NotificationAlert(node) {
  const target = node.querySelector('.accessibility-notification-text')
  if (!target) return

  const text = node.getAttribute('data-notification-text')
  // Defer past the initial render so the live region is observed as empty first,
  // then sees the mutation.
  window.requestAnimationFrame(() => {
    target.textContent = text
  })
}

export default NotificationAlert
