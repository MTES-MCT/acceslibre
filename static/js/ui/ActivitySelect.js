function ActivitySelect(root) {
  root.addEventListener('change', function () {
    let noActivity = document.getElementById('no_activity')
    let activitySuggested = document.getElementById('activity_suggested')
    let activity = document.getElementById('activite')

    if (activity.value != gettext('Autre')) {
      document.querySelector('#activity_suggested>span').innerHTML = ''
      noActivity.value = ''
      activitySuggested.classList.add('hidden')
      noActivity.classList.remove('hidden')
    }
  })
}

export default ActivitySelect
