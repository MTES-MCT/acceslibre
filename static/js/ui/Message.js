export default function showMessage(message) {
  document.querySelector('#js-notification-text').innerHTML = message
  document.querySelector('#js-notification').classList.remove('hidden')
}
