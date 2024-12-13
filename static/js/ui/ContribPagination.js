async function ContribPagination(root) {
  const PAGINATION_SIZE = 6
  const resultsContainer = root.querySelector('#internal-results-container')
  const viewMoreButtonContainer = root.querySelector('#view-more-button-container')
  const resultsCountContainer = root.querySelector('#internal-results-count-container')

  let currentPage = 1
  let currentCount = 0

  if (!root || !resultsContainer) return

  const apiKey = root.querySelector('[data-api-key]')?.dataset?.apiKey
  const apiUrl = root.querySelector('[data-api-url]')?.dataset?.apiUrl

  if (!apiKey || !apiUrl) return

  const params = getParams({ root, currentPage: 1, paginationSize: PAGINATION_SIZE })

  // Initial first fetch of ERP internal results on page load
  const { results, totalCount, status } = await getInternalResults({
    apiUrl,
    apiKey,
    params,
  })

  const shouldDisplayViewMoreButton = totalCount > PAGINATION_SIZE

  // currentCount initialised with first fetch of ERPs count
  // it is used later on to check whether or not to display/remove "View more" button
  currentCount = results.length

  // If there are any results, fill in the results list with cards
  populateInternalResults({ resultsContainer, results })

  if (totalCount > 0) {
    const resultsTranslation = totalCount === 1 ? gettext('résultat') : gettext('résultats')
    const headingNode = document.createElement('h2')
    const resultNode = document.createElement('p')

    headingNode.classList.add('mt-3', 'fr-mb-0', 'fr-h3')
    resultNode.classList.add('fr-text--xl')

    headingNode.textContent = gettext('Établissements enregistrés sur AccesLibre')
    resultNode.textContent = `${totalCount} ${resultsTranslation}`

    // List display with title
    resultsCountContainer.appendChild(headingNode)
    resultsCountContainer.appendChild(resultNode)

    currentPage++
  } else {
    const textNode = document.createElement('p')

    textNode.classList.add('fr-text--xl')
    textNode.textContent = gettext(`Aucun établissement n'a pu être trouvé`)

    // Display with no results
    resultsCountContainer.replaceChildren()
    resultsCountContainer.appendChild(textNode)
  }

  if (shouldDisplayViewMoreButton) {
    // Create and attach the View more button when there are more than PAGINATION_SIZE results
    const viewMoreButton = createViewMoreButton({ callback: onViewMoreCallback })

    viewMoreButtonContainer.appendChild(viewMoreButton)
  }

  async function onViewMoreCallback() {
    const params = getParams({ root, currentPage, paginationSize: PAGINATION_SIZE })

    try {
      const { results, status } = await getInternalResults({ apiKey, apiUrl, params })
      const shouldDeleteViewMoreButton = currentCount >= totalCount

      // If there are results, continue filling in the list of ERP cards
      if (results?.length > 0) {
        currentCount += results.length
        populateInternalResults({ resultsContainer, results })
      }

      if (status === 200) {
        if (results.length >= PAGINATION_SIZE) {
          currentPage++
        }
      }

      if (shouldDeleteViewMoreButton) {
        viewMoreButtonContainer.remove()
      }
    } catch (err) {
      // TODO: To do later
      // Error handling, maybe display an Alert notification from DSFR ?
    }
  }
}

function populateInternalResults({ resultsContainer, results }) {
  const cards = results
    .map(({ properties }) => {
      if (!properties) {
        return undefined
      }

      const { activite, adresse, nom, web_url } = properties

      return createCard({
        title: nom ?? '',
        tag: activite?.nom ?? '',
        description: adresse ?? '',
        link: web_url ?? '',
      })
    })
    .filter(Boolean)

  cards.forEach((card) => {
    resultsContainer.appendChild(card)
  })
}

/**
 * Get URLSearchParams for subsequent API call
 * @param root - Root container, used to get the activity slug from the hidden input
 * @param currentPage - Current page for the pagination
 * @param paginationSize - Number of results per page
 */
function getParams({ root, currentPage, paginationSize }) {
  // Get query parameters from URL
  // URL example: what=test&new_activity=&activite=Tennis&where=Ch%C3%A9cy+%2845%29&lat=47.9019&lon=2.0223&code=45089&ban_id=&postcode=45430&search_type=&street_name=&municipality=
  const url = new URL(window.location.href)
  const params = new URLSearchParams(url.search)
  const q = params.get('what')
  const activitySlug = root.querySelector('input[type="hidden"][name="activity_slug"]')?.value

  if (!q) {
    return null
  }

  const paramsForApiCall = new URLSearchParams()

  paramsForApiCall.append('q', q)
  paramsForApiCall.append('around', `${params.get('lat')},${params.get('lon')}`)
  paramsForApiCall.append('activite', activitySlug || params.get('activite'))
  paramsForApiCall.append('page_size', paginationSize)
  paramsForApiCall.append('page', currentPage)

  return paramsForApiCall
}

async function getInternalResults({ apiKey, apiUrl, params }) {
  const request = await fetch(`${apiUrl}?${params.toString()}`, {
    timeout: 10000,
    headers: {
      Accept: 'application/geo+json',
      Authorization: `Api-Key ${apiKey}`,
    },
  })

  const response = await request.json()

  return { results: response?.features || [], totalCount: response?.count || 0, status: request.status }
}

function createViewMoreButton({ callback }) {
  const button = document.createElement('button')

  button.classList.add('fr-btn', 'fr-btn--secondary', 'fr-btn--lg', 'fr-mt-6w')
  button.textContent = gettext(`Afficher plus d’établissements`)
  button.addEventListener('click', callback)

  return button
}

/**
 * Function to create a card DOM element, for internal search result
 * @param tag - Tag that will contain the activity name
 * @param description - Description that will contain the address of the ERP
 * @param title - Name of the ERP
 * @param url - URL of the ERP
 * @returns {HTMLDivElement}
 */
function createCard({ link = '', tag = '', description = '', title = '', url = '' }) {
  const card = document.createElement('div')
  const cardMainContent = document.createElement('div')
  const cardBody = document.createElement('div')
  const cardBodyContent = document.createElement('div')
  const cardBodyContentTitle = document.createElement('h3')
  const cardBodyContentTitleLink = document.createElement('a')
  const cardBodyContentDescription = document.createElement('p')
  const cardBodyContentStart = document.createElement('div')
  const cardBodyContentStartTag = document.createElement('p')

  // Add classes to all nodes
  card.classList.add('fr-col-12', 'fr-col-sm-6', 'fr-col-lg-4')
  cardMainContent.classList.add('fr-card', 'fr-enlarge-link')
  cardBody.classList.add('fr-card__body')
  cardBodyContent.classList.add('fr-card__content')
  cardBodyContentTitle.classList.add('fr-card__title', 'fr-h6')
  cardBodyContentDescription.classList.add('fr-card__desc')
  cardBodyContentStart.classList.add('fr-card__start')
  cardBodyContentStartTag.classList.add('fr-tag', 'fr-mb-1w')

  // Add child to appropriates nodes
  card.appendChild(cardMainContent)
  cardMainContent.appendChild(cardBody)

  // Body
  cardBody.appendChild(cardBodyContent)
  cardBodyContent.appendChild(cardBodyContentTitle)
  cardBodyContentTitle.appendChild(cardBodyContentTitleLink)
  cardBodyContent.appendChild(cardBodyContentDescription)
  cardBodyContent.appendChild(cardBodyContentStart)
  cardBodyContentStart.appendChild(cardBodyContentStartTag)

  // Inner content
  cardBodyContentStartTag.textContent = tag
  cardBodyContentTitleLink.textContent = title
  cardBodyContentTitleLink.setAttribute('href', /^https?:\/\//.test(link) ? new URL(link).href : '#')
  cardBodyContentDescription.textContent = description

  return card
}

export default ContribPagination
