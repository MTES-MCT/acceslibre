function generateHTMLForResult(result) {
  // let icon = 'building'
  let activity_name = ''
  let link = ''
  if (result.properties.activite__vector_icon) {
    // Data from template context
    // icon = result.properties.activite__vector_icon
    activity_name = result.properties.activite__nom
    link = result.properties.absolute_url
  } else if (result.properties.activite) {
    // Data from API
    // icon = result.properties.activite.vector_icon
    activity_name = result.properties.activite.nom
    link = result.properties.web_url
  }

  const completion_rate = result.properties.completion_rate

  return `
    <li class="list-style-type--none">
      <div class="fr-card fr-card--sm a4a-geo-link" data-erp-identifier="${result.properties.uuid}">
        <div class="fr-card__body">
            <div class="fr-card__content">
                <h3 class="fr-card__title fr-h5">${result.properties.nom}</h3>
                <div class="fr-card__desc">
                    <p class="fr-tag fr-mb-1w">${activity_name}</p>
                    <address class="fr-mb-0">${result.properties.adresse}</address>
                </div>
                <div class="fr-card__start">
                    <ul class="fr-badges-group gap-1w align-self--center justify-content--end fr-mb-1v">
                        <li>
                            <p class="fr-badge fr-badge--info fr-badge--no-icon fr-badge--sm fr-mb-0">
                            ${gettext('Remplissage')} ${completion_rate ?? '0'}%
                            </p>
                        </li>
                    </ul>
                </div>
            </div>
            <div class="fr-card__footer">
                <ul class="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
                    <li>
                        <a href="${link}" class="fr-btn" rel="noopener">${gettext('Voir')}</a>
                        <span class="fr-sr-only">${gettext('Les détails de l’établissement')} ${result.properties.nom}</span>
                    </li>
                    <li>
                        <button class="fr-btn fr-btn--secondary locate-btn">${gettext('Localiser')}</button>
                        <span class="fr-sr-only">${gettext('Recentre la carte sur l’établissement')} ${result.properties.nom}</span>
                    </li>
                </ul>
            </div>
        </div>
      </div>
    </li>
  `
}

export default {
  generateHTMLForResult,
}
