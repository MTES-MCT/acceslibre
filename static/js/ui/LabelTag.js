function LabelTag(root) {
  root.addEventListener('click', function (event) {
    const isEventFromUser = event.isTrusted
    let eventType = root.getAttribute('data-event-type')
    const input = event.target.parentElement.querySelector('input')
    input.checked = !input.checked

    if (isEventFromUser === true) {
      document.dispatchEvent(new CustomEvent(eventType, { detail: { source: event.target } }))
    }
  })
}

export default LabelTag
