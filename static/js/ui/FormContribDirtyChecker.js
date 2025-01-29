const INPUT_SELECTORS = [
  'input[type="text"]',
  'input[type="url"]',
  'input[type="email"]',
  'input[type="checkbox"]:checked',
  'input[type="radio"]:checked',
  'input[type="number"]',
  'input[type="hidden"]',
  'textarea',
].join(',')

const BLACKLISTED_CLASS_SELECTORS = ['leaflet-control-layers-selector']

async function FormContribDirtyChecker(root) {
  const dropdown = document.querySelector('#contrib-edit-cta')
  const csrfToken = document.querySelector('input[type="hidden"][name="csrfmiddlewaretoken"]')?.value

  // URL used for subsequent call to update current step's values
  const currentStepUrl = dropdown?.dataset?.currentUrl
  const modal = document.querySelector('dialog#contrib-edit-modal-controls')
  const openModalBtn = document.querySelector('button#contrib-edit-open-btn')
  const cancelBtn = document.querySelector('button#contrib-edit-modal-cancel-btn')
  const saveBtn = document.querySelector('button#contrib-edit-modal-save-btn')
  const closeBtn = document.querySelector('button[aria-controls="contrib-edit-modal-controls"]')

  if (
    !root ||
    !dropdown ||
    !csrfToken ||
    !currentStepUrl ||
    !cancelBtn ||
    !saveBtn ||
    !modal ||
    !openModalBtn ||
    !closeBtn
  ) {
    return
  }

  // Sort to guarantee the order since the method querySelectorAll doesn't
  const getInputNodes = () =>
    Array.from(root.querySelectorAll(INPUT_SELECTORS))
      .sort()
      .filter((input) => {
        // Exclude blacklisted inputs and ensure the input has a "name" or "id" attribute
        return !BLACKLISTED_CLASS_SELECTORS.includes(input.classList.value) && (input.name || input.id)
      })

  const getMapInputs = () => {
    const map = new Map()

    getInputNodes().forEach((input) => {
      const identifier = input.name || input.id
      const isCheckbox = input.type === 'checkbox'
      const { value } = input

      if (map.has(identifier) && isCheckbox) {
        map.set(identifier, [...map.get(identifier), value])
      } else {
        if (isCheckbox) {
          map.set(identifier, [value])
        } else {
          map.set(identifier, value)
        }
      }
    })

    return map
  }

  // Make it immutable as it will serve as a base for subsequent comparisons
  const originalInputsMap = Object.freeze(getMapInputs())

  // Check if there were any changes whenever we select a step to go to
  dropdown.addEventListener('input', async (e) => {
    const updatedInputsMap = getMapInputs()

    // Simple string comparison to check for diffs
    const original = Array.from(originalInputsMap.values()).join()
    const updated = Array.from(updatedInputsMap.values()).join()
    const hasDiffs = original !== updated

    if (!hasDiffs) {
      const redirectionUrl = e.target.value

      if (redirectionUrl) {
        window.location.assign(`${redirectionUrl}`)
      }
    } else {
      openModalBtn.click()
    }
  })

  saveBtn.addEventListener('click', async () => {
    const redirectionUrl = dropdown.value

    if (!redirectionUrl) return

    const updatedInputsMap = getMapInputs()
    const entries = updatedInputsMap.entries()
    const formData = new URLSearchParams()

    entries.forEach(([key, value]) => {
      if (Array.isArray(value) && value.length > 0) {
        value.forEach((v) => {
          formData.append(key, v)
        })
      } else {
        formData.append(key, value)
      }
    })

    fetch(currentStepUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken,
      },
      credentials: 'include',
      body: formData,
    })
      .then(() => {
        window.location.assign(redirectionUrl)
      })
      .catch((e) => {
        console.error('Error occurred', e)
      })
  })

  cancelBtn.addEventListener('click', () => {
    closeBtn.click()
  })
}

export default FormContribDirtyChecker
