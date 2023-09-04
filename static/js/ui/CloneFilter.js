let toEmit = []
function CloneFilter(root) {
  root.addEventListener('click', function (event) {
    let eventType = root.getAttribute('data-event-type')
    toEmit.push({ type: eventType, target: event.target })
    console.log(`Need to emit ${toEmit}`)
  })
}

export function CloneFilterSubmit(root) {
  root.addEventListener('click', function () {
    toEmit.forEach((event) => {
      document.dispatchEvent(new CustomEvent(event.type, { detail: { source: event.target } }))
    })
    toEmit = []
  })
}

export default { CloneFilter, CloneFilterSubmit }
