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

  enableKeyboardOnFocus()
  enhancePanoramaxLegendA11y()
})

// RGAA 12.x: the Panoramax viewer reacts to keyboard shortcuts via a window-level
// keydown listener gated by psv.state.keyboardEnabled. The component only flips
// that flag on mouse click / character keypress, so a keyboard-only user can
// never reach it. Make the host focusable and enable the shortcuts while it
// holds focus, disabling them on blur so they don't fire from elsewhere.
function enableKeyboardOnFocus() {
  // Keys the viewer consumes for navigation; prevent them from also scrolling
  // the page while the viewer holds focus.
  const SCROLL_KEYS = [
    'ArrowUp',
    'ArrowDown',
    'ArrowLeft',
    'ArrowRight',
    'PageUp',
    'PageDown',
    'Home',
    'End',
    ' ',
    'Spacebar',
  ]
  document.querySelectorAll('pnx-photo-viewer, pnx-viewer').forEach((host) => {
    host.setAttribute('tabindex', '0')
    host.addEventListener('focus', () => host.psv?.startKeyboardControl?.())
    host.addEventListener('blur', () => host.psv?.stopKeyboardControl?.())
    host.addEventListener('keydown', (event) => {
      if (event.target !== host || !SCROLL_KEYS.includes(event.key)) {
        return
      }
      host.psv?.startKeyboardControl?.()
      event.preventDefault()
    })
  })
}

// RGAA 6.1: the Panoramax legend (shadow DOM, third-party component) ships
// non-explicit links. Make their accessible names explicit and signal that
// they open in a new window. Re-applied on every Lit re-render via observers.
function enhancePanoramaxLegendA11y() {
  const legend = document.querySelector('pnx-widget-legend')
  if (!legend) {
    return
  }

  // Lit re-renders the legend on every picture change, overwriting the title and
  // wiping any icon we appended. So enhancement must be idempotent and re-run
  // after each render. We watch with observers and mask our own writes (disconnect
  // while writing) to avoid a feedback loop, since setAttribute fires the observer
  // even when the value is unchanged.
  const rootObserver = new MutationObserver(() => enhance())
  const pictureObserver = new MutationObserver(() => enhance())

  const setExternalLink = (link, label, visibleText) => {
    if (!link) {
      return
    }

    link.setAttribute('title', `${label} - ${gettext('nouvelle fenêtre')}`)
    link.setAttribute('rel', 'noopener')

    // Replace the on-screen text when it isn't self-explanatory (e.g. the photo
    // link only shows the author name). The descriptive label stays in title.
    if (visibleText && link.firstChild?.textContent !== visibleText) {
      link.textContent = visibleText
    }

    // Append the new-window indicator once; Lit drops it on re-render so we
    // re-add it whenever it is missing. The legend lives in a shadow root that
    // can't reach the DSFR icon font, so we reproduce DSFR's external-link icon
    // (remixicon external-link-line) as an inline SVG mask tinted to the link
    // colour — same box-with-arrow as fr-link[target="_blank"].
    if (!link.querySelector('[data-a11y-icon]')) {
      const svg =
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>" +
        "<path d='M10 6v2H5v11h11v-5h2v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6zm11-3v8h-2V6.413l-7.793 7.794-1.414-1.414L18.585 5H13V3h8z'/></svg>"
      const mask = `url("data:image/svg+xml,${encodeURIComponent(svg)}") no-repeat center / contain`
      const icon = document.createElement('span')
      icon.setAttribute('aria-hidden', 'true')
      icon.setAttribute('data-a11y-icon', '')
      icon.style.cssText = [
        'display:inline-block',
        'width:1em',
        'height:1em',
        'margin-left:0.25em',
        'vertical-align:middle',
        'background-color:currentColor',
        `-webkit-mask:${mask}`,
        `mask:${mask}`,
      ].join(';')
      link.appendChild(icon)
    }
  }

  const enhance = () => {
    const root = legend.shadowRoot
    if (!root) {
      return
    }

    rootObserver.disconnect()
    pictureObserver.disconnect()

    setExternalLink(root.querySelector('.presentation a[target="_blank"]'), gettext('Panoramax'))

    const pictureRoot = root.querySelector('pnx-picture-legend')?.shadowRoot
    if (pictureRoot) {
      pictureRoot.querySelectorAll('a[target="_blank"]').forEach((link) => {
        if (link.href.includes('/?pic=')) {
          // Visible text becomes the author name; cache it on first pass so the
          // descriptive title survives our own text replacement and re-renders.
          const author = link.dataset.a11yAuthor || (link.dataset.a11yAuthor = link.textContent.trim())
          setExternalLink(link, 'Voir sur Panoramax', gettext('Voir sur Panoramax'))
        } else {
          const licence = link.textContent.replace('↗', '').trim()
          setExternalLink(link, licence)
        }
      })
      pictureObserver.observe(pictureRoot, { childList: true, subtree: true })
    }

    rootObserver.observe(root, { childList: true, subtree: true })
  }

  const start = () => {
    if (!legend.shadowRoot) {
      requestAnimationFrame(start)
      return
    }
    enhance()
  }

  start()
}
