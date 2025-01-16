function SyncInputsWithElement(root) {
  if (!root) return

  const inputNames = root.getAttribute('data-input-names')?.split(',')
  if (!inputNames) {
    return
  }

  inputNames.forEach((inputName) => {
    const inputElement = document.querySelector(`input[name="${inputName.trim()}"]`)

    if (!inputElement) {
      return
    }

    inputElement.addEventListener('input', () => {
      root.textContent = inputNames
        .map((name) => {
          const input = document.querySelector(`input[name="${name.trim()}"]`)
          return input ? input.value : ''
        })
        .join(' ')
    })
  })
}
export default SyncInputsWithElement
