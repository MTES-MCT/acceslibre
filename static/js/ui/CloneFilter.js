let toEmit = []
function cloneFilter(root) {
  root.addEventListener('click', function (event) {
    toEmit.push({ type: root.getAttribute('data-event-type'), target: event.target })
  })
}

export function cloneFilterSubmit(root) {
  root.addEventListener('click', () => {
    toEmit.forEach((event) => {
      document.dispatchEvent(new CustomEvent(event.type, { detail: { source: event.target, skipRefresh: true } }))
    })
    toEmit = []

    document.getElementById('search-form').submit()
  })
}

export default { cloneFilter, cloneFilterSubmit }
