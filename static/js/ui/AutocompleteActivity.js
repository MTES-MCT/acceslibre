import Autocomplete from '@trevoreyre/autocomplete-js'

document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('autocomplete-activity')
  if (!root) {
    return
  }
  const inputElement = root.querySelector('input')
  const activities = JSON.parse(inputElement.dataset.searchLookup)

  new Autocomplete(root, {
    getResultValue: (result) => result.name,
    search: (searchTerm) => {
      if (searchTerm.length < 3) {
        return []
      }

      const exactResults = activities.filter((activity) =>
        activity.keywords.some(
          (keyword) => keyword.localeCompare(searchTerm, undefined, { sensitivity: 'base' }) === 0
        )
      )

      const otherKeywordResults = activities
        .filter((activity) =>
          activity.keywords.some((keyword) =>
            keyword
              .toLowerCase()
              .normalize('NFD')
              .replace(/[\u0300-\u036f]/g, '')
              .includes(
                searchTerm
                  .toLowerCase()
                  .normalize('NFD')
                  .replace(/[\u0300-\u036f]/g, '')
              )
          )
        )
        .filter((activity) => !exactResults.includes(activity))

      return exactResults.concat(otherKeywordResults)
    },
    renderResult: (result, props) => {
      const active = props['aria-selected'] ? 'active' : ''
      return `
        <li class="list-group-item a4a-autocomplete-result ${active}" ${props}>
          ${result.name}
        </li>
      `
    },
    onSubmit: (result) => {
      if (result != gettext('Autre')) {
        document.querySelector('#activity_suggested>span').innerHTML = ''
        document.getElementById('activity_suggested').classList.add('hidden')

        const noActivity = document.getElementById('no_activity')
        noActivity.value = ''
        noActivity.classList.remove('hidden')
      }
    },
  })
})
