class BackButton {
  constructor(el) {
    this.el = el
    this.onClick = this.onClick.bind(this)
    this.el.addEventListener('click', this.onClick)
  }

  onClick(event) {
    event.preventDefault()

    // No history, fallback
    if (window.history.length <= 1 || !document.referrer) {
      const fallback = this.el.dataset.fallbackUrl
      if (fallback) {
        window.location.href = fallback
        return
      }
    }
    window.history.back()
  }
}

export default BackButton
