function ExportResultsBtn(root) {
  if (!root) return

  root.addEventListener('click', async (event) => {
    event.preventDefault()
    const form = root.parentElement
    const url = new URL(form.getAttribute('action'), window.location.origin)
    const params = new URLSearchParams(new FormData(form))
    url.search = params

    fetch(url, { method: 'GET' })
      .then((response) => response.json())
      .then((data) => {
        displayMessage(data.message, data.success)
      })
  })
}

function displayMessage(message, type) {
  type = type === true ? 'success' : 'error'
  const messageBox = document.createElement('div')
  messageBox.className = `message-box ${type}`
  messageBox.innerHTML = message

  document.body.appendChild(messageBox)

  setTimeout(() => {
    messageBox.remove()
  }, 5000)
}

export default ExportResultsBtn
