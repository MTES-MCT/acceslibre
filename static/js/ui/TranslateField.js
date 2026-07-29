import DOMPurify from 'dompurify'

class TranslateField {
  constructor(el) {
    this.el = el
    this.pk = el.dataset.accessPk
    this.field = el.dataset.field

    this.btn = this._createBtn()
    this.result = this._createResult()

    el.append(this.btn, this.result)

    this.btn.addEventListener('click', () => this.translate())
  }

  _createBtn() {
    const btn = document.createElement('button')
    btn.className = 'translate-field__btn fr-btn fr-btn--secondary fr-btn--sm'
    btn.setAttribute('aria-label', gettext('Traduire ce champ en anglais'))
    btn.textContent = gettext('Traduire')
    return btn
  }

  _createResult() {
    const div = document.createElement('div')
    div.className = 'translate-field__result'
    div.setAttribute('aria-live', 'polite')
    div.setAttribute('aria-atomic', 'true')
    div.style.display = 'none'
    return div
  }

  async translate() {
    this.setLoading(true)
    const csrfToken = document.querySelector('input[type="hidden"][name="csrfmiddlewaretoken"]')?.value

    try {
      const response = await fetch(`/api/accessibilite/${this.pk}/translate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
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
    const html = DOMPurify.sanitize(text.replace(/\n/g, '<br>'), { ALLOWED_TAGS: ['br'] })
    window.requestAnimationFrame(() => {
      this.result.innerHTML = `\u201c${html}\u201d`
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
