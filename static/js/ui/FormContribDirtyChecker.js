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
  // const modal = document.querySelector('')

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

  // TODO: Handle checkboxes since there are multiple choices
  const getMapInputs = () => new Map(getInputNodes().map((input) => [input.name || input.id, input.value]))

  // Make it immutable as it will serve as a base for subsequent comparisons
  const originalInputsMap = Object.freeze(getMapInputs())

  // Check if there were any changes whenever we select a step to go to
  dropdown.addEventListener('input', async (e) => {
    const updatedInputsMap = getMapInputs()

    // Simple string comparison to check for diffs
    const original = Array.from(originalInputsMap.values()).join()
    const updated = Array.from(updatedInputsMap.values()).join()
    const hasDiffs = original !== updated

    console.log({ original, updated, hasDiffs, updatedInputsMap })
    console.log({ hasDiffs })

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
      console.log(key, value)
      formData.append(key, value)
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
