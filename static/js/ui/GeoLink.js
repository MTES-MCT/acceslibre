import geo from '../geo'

function GeoLink(root) {
  if (!root) return

  root.addEventListener('click', (event) => {
    event.preventDefault()
    event.stopPropagation()

    const parentNode = root.closest('[data-erp-identifier]')

    if (!parentNode) return

    const identifier = parentNode.dataset?.erpIdentifier

    if (identifier) {
      geo.openMarkerPopup(identifier)
    }
  })
}

export default GeoLink
