function LabelTag(root) {
  root.addEventListener('click', function (event) {
    let eventType = root.getAttribute('data-event-type')

    document.dispatchEvent(new CustomEvent(eventType, { detail: { source: event.target } }))
  })
}

export default LabelTag
