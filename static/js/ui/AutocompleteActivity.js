import Autocomplete from '@trevoreyre/autocomplete-js'

document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('autocomplete-activity')

  if (!root) {
    return
  }

  const inputElement = root.querySelector('input[name="activite"]')
  const activities = JSON.parse(inputElement.dataset.searchLookup)
  const onSubmit = (slug) => {
    const activitySlugInput = document.querySelector('input[type="hidden"][name="activity_slug"]')

    if (activitySlugInput) {
      activitySlugInput.value = slug
    }

    hideErrorMessage()
  }

  const autocomplete = new Autocomplete(root, {
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
    onSubmit: ({ slug }) => onSubmit(slug),
  })

  function hideErrorMessage() {
    inputElement.form.querySelector('#activite-input-messages').classList.add('fr-hidden')
    inputElement.form.querySelector('#activite-input-messages').parentElement.classList.remove('fr-input-group--error')
  }

  // Dirty hack to support press Key enter (Lib is broken)
  autocomplete.input.addEventListener('keydown', (event) => {
    const { key } = event
    const isDropdownExpanded = !!autocomplete?.expanded

    // We do not want to submit the form if the suggestion list is opened, only when it's closed.
    if (key === 'Enter' && isDropdownExpanded) {
      // Prevent form submission
      event.preventDefault()

      const slug = autocomplete?.core?.selectedResult?.slug

      if (slug) {
        // Populate hidden input
        onSubmit(slug)
      }
    }
  })

  autocomplete.input.addEventListener('input', () => {
    const value = autocomplete.input.value.trim()

    if (value === '') {
      const activitySlugInput = document.querySelector('input[type="hidden"][name="activity_slug"]')
      if (activitySlugInput) {
        activitySlugInput.value = ''
      }
    }
  })
})
