function BtnToCopy(root) {
  if (!root) return

  const btn = root.querySelector('#btn-to-copy')
  const urlToCopy = btn.dataset['url']
  const voiceOverText = root.querySelector('#btn-to-copy-voice-over-text')

  if (!navigator.clipboard) {
    btn.classList.add('display--none')
  }

  if (!urlToCopy || !voiceOverText || !btn || !navigator.clipboard) return

  document.addEventListener('click', () => {
    navigator.clipboard.writeText(urlToCopy).then(() => {
      voiceOverText.innerText = gettext('Le lien a été copié.')
    })
  })
}

export default BtnToCopy
