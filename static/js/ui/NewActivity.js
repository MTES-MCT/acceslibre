function NewActivity(root) {
  root.addEventListener('click', function (event) {
    event.preventDefault()
    let inputNewActivity = document.getElementById('new_activity')
    let selectActivity = document.getElementById('autocomplete-activity')

    inputNewActivity.classList.remove('hidden')
    inputNewActivity.focus()
    selectActivity.classList.add('hidden')
    selectActivity.querySelector('input').value = gettext('Autre')
  })
}

export default NewActivity
