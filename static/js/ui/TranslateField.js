class TranslateField {
  constructor(el) {
    this.el = el
    this.pk = el.dataset.pk
    this.field = el.dataset.field
    this.apiKey = el.dataset.apiKey
    this.btn = el.querySelector('.translate-field__btn')
    this.result = el.querySelector('.translate-field__result')
    this.btn.style.display = 'block'
    this.result.style.display = 'block'

    if (!this.btn || !this.result) {
      console.warn('TranslateField: missing btn or result in', el)
      return
    }

    this.btn.addEventListener('click', () => this.translate())
  }

  async translate() {
    this.setLoading(true)
    const csrfToken = document.querySelector('input[type="hidden"][name="csrfmiddlewaretoken"]')?.value

    try {
      const response = await fetch(`/api/accessibilite/${this.pk}/translate/`, {
        timeout: 10000,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Api-Key ${this.apiKey}`,
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          field: this.field,
          target_lang: document.documentElement.lang || 'en',
        }),
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()

      if (data.translated) {
        this.showTranslation(data.translated)
      } else {
        this.showError(gettext('Aucune traduction disponible.'))
      }
    } catch {
      this.showError(gettext('La traduction a échoué, veuillez réessayer.'))
    } finally {
      this.setLoading(false)
    }
  }

  setLoading(isLoading) {
    this.btn.disabled = isLoading
    this.btn.setAttribute('aria-busy', isLoading)
    this.btn.textContent = isLoading ? gettext('Traduction en cours\u2026') : gettext('Traduire')
  }

  showTranslation(text) {
    this.result.style.display = 'block'
    // Defer text injection so the live region is observed empty first,
    // ensuring assistive tech announces the mutation.
    window.requestAnimationFrame(() => {
      this.result.textContent = text
    })
    this.btn.style.display = 'none'
  }

  showError(message) {
    this.result.style.display = 'block'
    this.result.setAttribute('role', 'alert')
    window.requestAnimationFrame(() => {
      this.result.textContent = message
    })
  }
}

export default function translateField(el) {
  return new TranslateField(el)
}
