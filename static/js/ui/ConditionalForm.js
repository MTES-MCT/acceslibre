const rules = [
  // Transport
  {
    source: 'transport_station_presence',
    values: ['True'],
    targets: ['transport_information'],
  },
  // Stationnement
  {
    source: 'stationnement_presence',
    values: ['True'],
    targets: ['stationnement_pmr'],
  },
  {
    source: 'stationnement_ext_presence',
    values: ['True'],
    targets: ['stationnement_ext_pmr'],
  },
  // Presence d'un extérieur et cheminement
  {
    source: 'cheminement_ext_presence',
    values: ['True'],
    targets: [
      'cheminement_ext_signaletique_exterieure',
      'cheminement_ext_terrain_stable',
      'cheminement_ext_plain_pied',
      'cheminement_ext_devers',
      'cheminement_ext_bande_guidage',
      'cheminement_ext_retrecissement',
      'cheminement_ext_pente_presence',
    ],
  },
  {
    source: 'cheminement_ext_plain_pied',
    values: ['False'],
    targets: [
      'cheminement_ext_nombre_marches',
      'cheminement_ext_sens_marches',
      'cheminement_ext_reperage_marches',
      'cheminement_ext_main_courante',
      'cheminement_ext_rampe',
      'cheminement_ext_ascenseur',
    ],
  },
  {
    source: 'cheminement_ext_ascenseur',
    values: ['True'],
    targets: ['cheminement_ext_ascenseur_pmr'],
  },
  {
    source: 'cheminement_ext_pente_presence',
    values: ['True'],
    targets: ['cheminement_ext_pente_degre_difficulte', 'cheminement_ext_pente_longueur'],
  },
  // Entrée
  {
    source: 'entree_porte_presence',
    values: ['True'],
    targets: ['entree_porte_manoeuvre', 'entree_porte_type', 'entree_vitree'],
  },
  {
    source: 'entree_vitree',
    values: ['True'],
    targets: ['entree_vitree_vitrophanie'],
  },
  {
    source: 'entree_dispositif_appel',
    values: ['True'],
    targets: ['entree_dispositif_appel_type'],
  },
  {
    source: 'entree_plain_pied',
    values: ['False'],
    targets: [
      'entree_marches',
      'entree_marches_sens',
      'entree_marches_reperage',
      'entree_marches_main_courante',
      'entree_marches_rampe',
      'entree_ascenseur',
    ],
  },
  {
    source: 'entree_ascenseur',
    values: ['True'],
    targets: ['entree_ascenseur_pmr'],
  },
  {
    source: 'entree_pmr',
    values: ['True'],
    targets: ['entree_pmr_informations'],
  },
  // Accueil
  {
    source: 'accueil_audiodescription_presence',
    values: ['True'],
    targets: ['accueil_audiodescription'],
  },
  {
    source: 'accueil_equipements_malentendants_presence',
    values: ['True'],
    targets: ['accueil_equipements_malentendants'],
  },
  {
    source: 'accueil_cheminement_plain_pied',
    values: ['False'],
    targets: [
      'accueil_cheminement_nombre_marches',
      'accueil_cheminement_sens_marches',
      'accueil_cheminement_reperage_marches',
      'accueil_cheminement_main_courante',
      'accueil_cheminement_rampe',
      'accueil_cheminement_ascenseur',
    ],
  },
  {
    source: 'accueil_cheminement_ascenseur',
    values: ['True'],
    targets: ['accueil_cheminement_ascenseur_pmr'],
  },
  {
    source: 'accueil_ascenseur_etage',
    values: ['True'],
    targets: ['accueil_ascenseur_etage_pmr'],
  },
  {
    source: 'accueil_soignant',
    values: ['True'],
    targets: ['accueil_soignant_experience'],
  },
  {
    source: 'accueil_tribunes_places',
    minValue: 1,
    targets: ['accueil_tribunes_localisation_places', 'accueil_tribunes_places_avec_accompagnants'],
  },
  {
    source: 'accueil_vestiaires',
    values: ['True'],
    targets: ['accueil_vestiaires_largeur_passage'],
  },
  {
    source: 'accueil_douches_collectives',
    values: ['True'],
    targets: ['accueil_douches_collectives_adaptees'],
  },
  {
    source: 'accueil_douches_individuelles',
    values: ['True'],
    targets: ['accueil_douches_individuelles_adaptees'],
  },
  {
    source: 'accueil_casiers',
    values: ['True'],
    targets: ['accueil_casiers_adaptes', 'accueil_casiers_fermeture'],
  },
  // Sanitaires
  {
    source: 'sanitaires_presence',
    values: ['True'],
    targets: ['sanitaires_adaptes', 'sanitaires_urinoirs'],
  },
  {
    source: 'sanitaires_adaptes',
    values: ['True'],
    targets: ['sanitaires_largeur_porte', 'sanitaires_sens_transfert'],
  },
  // Chambres accessibles
  {
    source: 'accueil_chambre_nombre_accessibles',
    minValue: 1,
    targets: [
      'accueil_chambre_douche_plain_pied',
      'accueil_chambre_douche_siege',
      'accueil_chambre_douche_barre_appui',
      'accueil_chambre_sanitaires_barre_appui',
      'accueil_chambre_sanitaires_espace_usage',
    ],
  },
  // Labels
  // TODO
  // Publication: registre et conformité
  // a. afficher registre si gestionnaire
  {
    source: 'user_type',
    values: ['gestionnaire', 'admin'],
    targets: ['registre_url'],
  },
  // b. afficher conformité si administration
  {
    source: 'user_type',
    values: ['admin'],
    targets: ['conformite'],
  },
  {
    source: 'user_type',
    values: ['gestionnaire'],
    targets: ['rpa_exemption'],
  },
]

function getFieldInputs(root, field) {
  return Array.from(root.querySelectorAll(`input[name=${field}]`))
}

function getValue(root, field) {
  const inputs = getFieldInputs(root, field)
  if (inputs.length === 0) {
    // field has not been found in the page, skipping
    return
  }
  const selectedInput = inputs.filter((input) => input.checked || input.type == 'number')[0]
  return selectedInput?.value
}

function resetField(field) {
  const radioNone = field.querySelector("input[type=radio][value='']")

  if (radioNone) {
    radioNone.click()
  }

  const inputTypes = ['textarea', 'input[type=text]', 'input[type=url]', 'input[type=date]', 'input[type=number]']

  inputTypes.forEach((inputType) => {
    const element = field.querySelector(inputType)

    if (element) {
      element.value = ''
    }
  })
}

function processTargets(root, rule, value) {
  const SECTION_SELECTOR = '.contrib-inputs-section'

  rule.targets.forEach((target) => {
    const el = root.querySelector(`.field-${target}`)

    if (!el) return

    if (
      (typeof rule.minValue !== 'undefined' && value && parseInt(value) >= rule.minValue) ||
      (typeof rule.values !== 'undefined' && rule.values.indexOf(value) !== -1)
    ) {
      el.closest(SECTION_SELECTOR).classList.remove('hidden')
    } else {
      el.closest(SECTION_SELECTOR).classList.add('hidden')
      el.innerHTML.trim()

      resetField(el)
    }
  })
}

function processRule(root, rule) {
  // grab the source field input elements
  const inputs = getFieldInputs(root, rule.source)

  if (inputs.length === 0) {
    // field has not been found in the page, skipping
    return
  }

  inputs.forEach((input) => {
    input.addEventListener('change', function ({ target: { value } }) {
      processTargets(root, rule, value)

      rule.targets.forEach((child) => {
        const childRule = rules.filter((rule) => rule.source === child)[0]

        if (childRule) {
          processTargets(root, childRule, getValue(root, child))
        }
      })
    })
  })

  processTargets(root, rule, getValue(root, rule.source))
}

export default function ConditionalForm(root) {
  rules.forEach(function (rule) {
    processRule(root, rule)
  })
}
