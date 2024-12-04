function ContribPagination(root) {
  let currentPage = 2
  const PAGINATION_SIZE = 6
  const viewMoreButton = root.querySelector('#contrib-view-more-button')
  const resultsContainer = root.querySelector('#internal-results-container')

  if (!root || !viewMoreButton || !resultsContainer) return

  const apiKey = root.querySelector('[data-api-key]')?.dataset?.apiKey
  const apiUrl = root.querySelector('[data-api-url]')?.dataset?.apiUrl

  viewMoreButton.addEventListener('click', viewMore)

  if (!apiKey || !apiUrl) return

  async function viewMore() {
    // Get query parameters from URL
    // URL example: what=test&new_activity=&activite=Tennis&where=Ch%C3%A9cy+%2845%29&lat=47.9019&lon=2.0223&code=45089&ban_id=&postcode=45430&search_type=&street_name=&municipality=
    const url = new URL(window.location.href)
    const params = new URLSearchParams(url.search)

    const q = params.get('what')
    const activitySlug = root.querySelector('input[type="hidden"][name="activity_slug"]')?.value
    const commune = root.querySelector('[data-commune]')?.dataset?.commune

    console.log({ q, activitySlug, commune })
    // All fields are mandatory
    if (!q || !activitySlug) {
      return
    }
    const paramsForApiCall = new URLSearchParams()

    paramsForApiCall.append('q', q)
    paramsForApiCall.append('commune', params.get('municipality'))
    paramsForApiCall.append('activite', activitySlug)
    paramsForApiCall.append('page_size', PAGINATION_SIZE)
    paramsForApiCall.append('page', currentPage++)

    const request = await fetch(`${apiUrl}?${paramsForApiCall.toString()}`, {
      timeout: 10000,
      headers: {
        Accept: 'application/geo+json',
        Authorization: `Api-Key ${apiKey}`,
      },
    })

    const response = await request.json()
    const features = response?.features

    if (features?.length > 0) {
      const cards = response.features
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
  }
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
