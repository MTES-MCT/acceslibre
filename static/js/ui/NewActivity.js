function NewActivity(root) {
  root.addEventListener('input', function (e) {
    const { checked } = e.target

    let inputNewActivity = document.getElementById('new_activity')
    let checkbox = document.getElementById('no_activity')

    let selectActivity = document.getElementById('autocomplete-activity')
    let label = document.querySelector('label[for="new_activity"]')

    if (checked) {
      inputNewActivity.classList.remove('hidden')
      label.classList.remove('hidden')
      inputNewActivity.focus()

      selectActivity.classList.add('hidden')
      checkbox.classList.add('hidden')
      selectActivity.querySelector('input').value = gettext('Autre')
    } else {
      inputNewActivity.classList.add('hidden')
      label.classList.add('hidden')
      inputNewActivity.focus()

      selectActivity.classList.remove('hidden')
      checkbox.classList.remove('hidden')
      selectActivity.querySelector('input').value = gettext('Autre')
    }
  })
}

export default NewActivity
