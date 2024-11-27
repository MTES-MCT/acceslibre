function generateHTMLForResult(result) {
  let icon = 'building'
  let activity_name = ''
  let link = ''
  if (result.properties.activite__vector_icon) {
    // Data from template context
    icon = result.properties.activite__vector_icon
    activity_name = result.properties.activite__nom
    link = result.properties.absolute_url
  } else if (result.properties.activite) {
    // Data from API
    icon = result.properties.activite.vector_icon
    activity_name = result.properties.activite.nom
    link = result.properties.web_url
  }

  return `
    <div class="list-group-item d-flex justify-content-between align-items-center fr-pt-2v fr-pr-2v fr-pb-1v fr-pl-0 map-results">
    <div>
        <div>
          <h3 class="h6 font-weight-bold w-100 fr-mb-0 fr-pb-0">
            <img alt="" class="act-icon act-icon-20 fr-mb-1v" src="/static/img/mapicons.svg#${icon}">
            
            <a class="fr-link" href="${link}">
               ${result.properties.nom}
                <span class="fr-sr-only">
                    ${activity_name}
                    ${result.properties.adresse}
                </span>
            </a>
          </h3>
        </div>
        <div aria-hidden="true">
            <small class="font-weight-bold">${activity_name}</small>
            <address class="d-inline mb-0">
                <small>${result.properties.adresse}</small>
            </address>
        </div>
    </div>
    <button class="btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link fr-ml-2w"
            title="${gettext('Localiser sur la carte')}"
            data-erp-identifier="${result.properties.uuid}">
        ${gettext('Localiser')}
        <br>
        <i aria-hidden="true" class="icon icon-target"></i>
    </button>
</div>`
}

export default {
  generateHTMLForResult,
}
