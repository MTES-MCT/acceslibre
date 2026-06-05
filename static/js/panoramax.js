import '@panoramax/web-viewer'

document.addEventListener('DOMContentLoaded', () => {
  const browser = document.querySelector('pnx-viewer')
  const xyzField = document.getElementById('xyz-coords')
  const imageId = document.getElementById('image-id')

  if (browser && xyzField) {
    const updateXYZandImageID = (event) => {
      const { x, y, z } = event.detail
      const xyz = `${x}/${y}/${z}`
      xyzField.value = xyz
      imageId.value = browser.getAttribute('picture')
    }

    browser.addEventListener('psv:view-rotated', updateXYZandImageID)
    browser.addEventListener('psv:position-changed', updateXYZandImageID)
  }

  const viewer = document.querySelector('pnx-photo-viewer')
  if (viewer) {
    const xyz = viewer.getAttribute('xyz')

    viewer.addEventListener('psv:picture-loaded', () => {
      if (xyz) {
        const [x, y, z] = xyz.split('/').map(Number)
        viewer.psv.setXYZ(x, y, z)
      }
    })
  }

  enhancePanoramaxLegendA11y()
})

// RGAA 6.1: the Panoramax legend (shadow DOM, third-party component) ships
// non-explicit links. Make their accessible names explicit and signal that
// they open in a new window. Re-applied on every Lit re-render via observers.
function enhancePanoramaxLegendA11y() {
  const legend = document.querySelector('pnx-widget-legend')
  if (!legend) {
    return
  }

  const enhanceExternalLink = (link, label) => {
    if (!link || link.dataset.a11yEnhanced) {
      return
    }
    link.setAttribute('aria-label', `${label} - ${gettext('nouvelle fenêtre')}`)
    link.setAttribute('rel', 'noopener')
    const icon = document.createElement('span')
    icon.setAttribute('aria-hidden', 'true')
    icon.textContent = ' ↗'
    link.appendChild(icon)
    link.dataset.a11yEnhanced = 'true'
  }

  const enhance = () => {
    const root = legend.shadowRoot
    if (!root) {
      return
    }

    enhanceExternalLink(
      root.querySelector('.presentation a[target="_blank"]'),
      gettext('En savoir plus sur Panoramax')
    )

    const pictureRoot = root.querySelector('pnx-picture-legend')?.shadowRoot
    if (pictureRoot) {
      pictureRoot.querySelectorAll('a[target="_blank"]').forEach((link) => {
        if (link.href.includes('/?pic=')) {
          enhanceExternalLink(link, gettext('Voir le point de vue photo sur Panoramax'))
        } else {
          const licence = link.textContent.trim()
          enhanceExternalLink(link, `${gettext('Voir la description complète de la licence')} ${licence}`)
        }
      })
      if (!pictureRoot._a11yObserved) {
        pictureRoot._a11yObserved = true
        new MutationObserver(enhance).observe(pictureRoot, { childList: true, subtree: true })
      }
    }
  }

  const start = () => {
    if (!legend.shadowRoot) {
      requestAnimationFrame(start)
      return
    }
    enhance()
    new MutationObserver(enhance).observe(legend.shadowRoot, { childList: true, subtree: true })
  }

  start()
}
