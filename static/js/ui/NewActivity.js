function NewActivity(root) {
  root.addEventListener('click', function (event) {
    event.preventDefault()

    let inputNewActivity = document.getElementById('new_activity')
    let link = document.getElementById('no_activity')
    let selectActivity = document.getElementById('autocomplete-activity')
    let label = document.querySelector('label[for="new_activity"]')

    inputNewActivity.classList.remove('hidden')
    label.classList.remove('hidden')
    inputNewActivity.focus()

    selectActivity.classList.add('hidden')
    link.classList.add('hidden')
    selectActivity.querySelector('input').value = gettext('Autre')
  })
}

export default NewActivity
