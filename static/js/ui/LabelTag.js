function LabelTag(root) {
  root.addEventListener('click', function (event) {
    let eventType = root.getAttribute('data-event-type')
    const input = event.target.parentElement.querySelector('input')
    input.checked = !input.checked
    document.dispatchEvent(new CustomEvent(eventType, { detail: { source: event.target } }))
  })
}

export default LabelTag
