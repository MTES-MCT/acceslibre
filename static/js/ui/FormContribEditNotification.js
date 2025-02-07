import { EDIT_CONTRIB_NOTIFICATION_KEY } from '../constants/localStorageKeys'

function FormContribEditNotification(root) {
  if (!root) return

  const notificationNode = root.querySelector('#contrib-edit-notification')

  if (!notificationNode) return

  const notification = JSON.parse(window.localStorage.getItem(EDIT_CONTRIB_NOTIFICATION_KEY))
  const notificationHasError = !!notification?.hasError
  const closeBtn = notificationNode.querySelector('button.fr-btn--close')

  if (!closeBtn) return

  if (notification) {
    notificationNode.classList.add(notificationHasError ? 'fr-alert--error' : 'fr-alert--success')
    notificationNode.querySelector('#contrib-edit-notification-message').textContent = notification.message
    notificationNode.querySelector('#contrib-edit-notification-title').textContent = notification.title
    notificationNode.classList.remove('hidden')
    window.localStorage.removeItem(EDIT_CONTRIB_NOTIFICATION_KEY)
  }

  closeBtn.addEventListener('click', function () {
    this.parentNode.remove()
  })
}

export default FormContribEditNotification
