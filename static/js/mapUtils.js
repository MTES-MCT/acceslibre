function generateHTMLForResult(result) {
    return `
    <div class="list-group-item d-flex justify-content-between align-items-center pt-2 pr-2 pb-1 pl-0">
    <div>
        <div class="d-flex w-100 justify-content-between">
            <a href="${ result.properties.web_url }">
                <h3 class="h6 font-weight-bold w-100 mb-0 pb-0">
                    <img alt="" class="act-icon act-icon-20 mb-1" src="/static/img/mapicons.svg#${ result.properties.activite.vector_icon || 'building' }">
                   ${ result.properties.nom }
                    <span class="sr-only">
                        ${ result.properties.activite.nom }
                        {% translate "à l'adresse" %} ${ result.properties.adresse }
                    </span>
                </h3>
            </a>
        </div>
        <div aria-hidden="true">
            <small class="font-weight-bold text-muted">${ result.properties.activite.nom }</small>
            <address class="d-inline mb-0">
                <small>${ result.properties.adresse }</small>
            </address>
        </div>
    </div>
    <button class="btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link ml-2"
            title="${gettext('Localiser sur la carte')}"
            data-erp-id="{{ erp.pk }}">
        ${gettext("Localiser")}
        <br>
        <i aria-hidden="true" class="icon icon-target"></i>
    </button>
</div>`;
}

export default {
  generateHTMLForResult
}
