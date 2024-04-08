const rules = [
  // Transport
  {
    source: 'transport_station_presence',
    values: ['True'],
    targets: ['transport_information'],
    indent: 1,
  },

  // Stationnement
  {
    source: 'stationnement_presence',
    values: ['True'],
    targets: ['stationnement_pmr'],
    indent: 1,
  },
  {
    source: 'stationnement_ext_presence',
    values: ['True'],
    targets: ['stationnement_ext_pmr'],
    indent: 1,
  },

  // Presence d'un extérieur et cheminement
  {
    source: 'cheminement_ext_presence',
    values: ['True'],
    targets: [
      'cheminement_ext_terrain_stable',
      'cheminement_ext_plain_pied',
      'cheminement_ext_nombre_marches',
      'cheminement_ext_reperage_marches',
      'cheminement_ext_main_courante',
      'cheminement_ext_rampe',
      'cheminement_ext_ascenseur',
      'cheminement_ext_pente_presence',
      'cheminement_ext_devers',
      'cheminement_ext_bande_guidage',
      'cheminement_ext_retrecissement',
    ],
    indent: 1,
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
    indent: 2,
  },

  {
    source: 'cheminement_ext_pente_presence',
    values: ['True'],
    targets: ['cheminement_ext_pente_degre_difficulte', 'cheminement_ext_pente_longueur'],
    indent: 2,
  },

  // Entrée
  {
    source: 'entree_porte_presence',
    values: ['True'],
    targets: ['entree_porte_manoeuvre', 'entree_porte_type', 'entree_vitree'],
    indent: 1,
  },
  {
    source: 'entree_vitree',
    values: ['True'],
    targets: ['entree_vitree_vitrophanie'],
    indent: 2,
  },
  {
    source: 'entree_dispositif_appel',
    values: ['True'],
    targets: ['entree_dispositif_appel_type'],
    indent: 1,
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
    indent: 1,
  },
  {
    source: 'entree_pmr',
    values: ['True'],
    targets: ['entree_pmr_informations'],
    indent: 1,
  },

  // Accueil
  {
    source: 'accueil_audiodescription_presence',
    values: ['True'],
    targets: ['accueil_audiodescription'],
    indent: 1,
  },
  {
    source: 'accueil_equipements_malentendants_presence',
    values: ['True'],
    targets: ['accueil_equipements_malentendants'],
    indent: 1,
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
    indent: 1,
  },

  // Sanitaires
  {
    source: 'sanitaires_presence',
    values: ['True'],
    targets: ['sanitaires_adaptes'],
    indent: 1,
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
    indent: 1,
  },

  // Labels
  // TODO

  // Publication: registre et conformité
  // a. afficher registre si gestionnaire
  {
    source: 'user_type',
    values: ['gestionnaire', 'admin'],
    targets: ['registre_url'],
    indent: 1,
  },
  // b. afficher conformité si administration
  {
    source: 'user_type',
    values: ['admin'],
    targets: ['conformite'],
    indent: 1,
  },
]

function getFieldInputs(root, field) {
  return [].slice.call(root.querySelectorAll(`input[name=${field}]`))
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
  const textarea = field.querySelector('textarea')
  if (textarea) {
    textarea.value = ''
  }
  const textField = field.querySelector('input[type=text]')
  if (textField) {
    textField.value = ''
  }
  const urlField = field.querySelector('input[type=url]')
  if (urlField) {
    urlField.value = ''
  }
  const dateField = field.querySelector('input[type=date]')
  if (dateField) {
    dateField.value = ''
  }
  const numberInput = field.querySelector('input[type=number]')
  if (numberInput) {
    numberInput.value = ''
  }
}

function processTargets(root, rule, value) {
  rule.targets.forEach((target) => {
    const el = root.querySelector(`.field-${target}`)
    if (!el) {
      return
    }

    if (
      (typeof rule.minValue !== 'undefined' && value && parseInt(value) >= rule.minValue) ||
      (typeof rule.values !== 'undefined' && rule.values.indexOf(value) !== -1)
    ) {
      el.classList.add('indented' + rule.indent)
      el.setAttribute('aria-label', el.children[0].children[0].innerHTML)
      el.classList.remove('hidden')
    } else {
      el.classList.add('hidden')
      el.removeAttribute('aria-label')
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
        const childRule = rules.filter((r) => r.source === child)[0]
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
