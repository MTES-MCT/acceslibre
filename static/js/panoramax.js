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
})
