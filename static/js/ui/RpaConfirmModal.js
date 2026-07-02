import { RPA_CONFIRMED_KEY } from '../constants/localStorageKeys'

// localStorage stores the list of ERP ids for which the user has already
// confirmed the RPA (Registre Public d'Accessibilité) notice.
function getConfirmedIds() {
  try {
    const raw = window.localStorage.getItem(RPA_CONFIRMED_KEY)
    const parsed = raw ? JSON.parse(raw) : []

    return Array.isArray(parsed) ? parsed.map(String) : []
  } catch (e) {
    return []
  }
}

export function isRpaConfirmed(erpId) {
  if (!erpId) return false

  return getConfirmedIds().includes(String(erpId))
}

export function markRpaConfirmed(erpId) {
  if (!erpId) return

  const ids = getConfirmedIds()

  if (!ids.includes(String(erpId))) {
    ids.push(String(erpId))
    window.localStorage.setItem(RPA_CONFIRMED_KEY, JSON.stringify(ids))
  }
}

function getModal() {
  return document.querySelector('dialog#rpa-confirm-modal')
}

function discloseModal(modal) {
  if (typeof dsfr === 'function') {
    dsfr(modal).modal.disclose()
  } else {
    document.querySelector('#rpa-confirm-modal-open-btn')?.click()
  }
}

function concealModal(modal) {
  if (typeof dsfr === 'function') {
    dsfr(modal).modal.conceal()
  }
}

// Run `onConfirmed` immediately when the RPA notice was already confirmed for
// this ERP, otherwise open the modal and defer until the user confirms.
export function ensureRpaConfirmed(onConfirmed) {
  const modal = getModal()
  const erpId = modal?.dataset?.erpId

  // No modal or no ERP id: don't block the flow.
  if (!modal || !erpId || isRpaConfirmed(erpId)) {
    onConfirmed()
    return
  }

  const confirmBtn = modal.querySelector('#rpa-confirm-modal-confirm-btn')
  if (!confirmBtn) {
    onConfirmed()
    return
  }

  const handler = () => {
    confirmBtn.removeEventListener('click', handler)
    markRpaConfirmed(erpId)
    concealModal(modal)
    onConfirmed()
  }
  confirmBtn.addEventListener('click', handler)

  discloseModal(modal)
}

function getSelectedUserType() {
  const checked = document.querySelector('input[name="user_type"]:checked')
  if (checked) return checked.value

  const hidden = document.querySelector('input[type="hidden"][name="user_type"]')
  return hidden ? hidden.value : null
}

function isRpaExemptionSelected() {
  return !!document.querySelector('input[name="rpa_exemption"]:checked')
}

function shouldDisplayModal() {
  const modal = getModal()
  const erpId = modal?.dataset?.erpId

  if (!modal || !erpId || isRpaConfirmed(erpId)) return false

  if (!isRpaExemptionSelected()) return false

  const hasUserType = document.querySelector('input[name="user_type"]')

  if (hasUserType) return getSelectedUserType() === 'gestionnaire'

  return true
}

// Gate a control's click behind the RPA notice, deferring `action` until the
// user has confirmed (once per ERP, choice is stored in localstorage to not display the modal multiple times).
function gateClick(el, action) {
  if (!el) return

  el.addEventListener('click', (event) => {
    if (!shouldDisplayModal()) return

    event.preventDefault()
    ensureRpaConfirmed(action)
  })
}

// Submit a button's form preserving its name/value, falling back to a click.
const submitForm = (btn) => () => {
  const form = btn.form

  if (form && typeof form.requestSubmit === 'function') {
    form.requestSubmit(btn)
  } else {
    btn.click()
  }
}

// Gate step navigation (next/previous) and publication behind the RPA notice.
function RpaConfirmModal(root) {
  if (!root) return

  const publishBtn = document.querySelector('#contrib-edit-publish-btn')
  const nextBtn = document.querySelector('#contrib-next-btn')
  const prevLink = document.querySelector('#contrib-prev-btn')

  gateClick(publishBtn, submitForm(publishBtn))
  gateClick(nextBtn, submitForm(nextBtn))
  gateClick(prevLink, () => window.location.assign(prevLink.href))
}

export default RpaConfirmModal
