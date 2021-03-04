let _config = {
  fieldSelectorPrefix: ".form-row.field-",
  inputNamePrefix: "accessibilite-0-",
};

const rules = [
  // Transport
  {
    source: "transport_station_presence",
    values: ["True"],
    targets: ["transport_information"],
    indent: 1,
  },

  // Stationnement
  {
    source: "stationnement_presence",
    values: ["True"],
    targets: ["stationnement_pmr"],
    indent: 1,
  },
  {
    source: "stationnement_ext_presence",
    values: ["True"],
    targets: ["stationnement_ext_pmr"],
    indent: 1,
  },

  // Presence d'un extérieur et cheminement
  {
    source: "cheminement_ext_presence",
    values: ["True"],
    targets: [
      "cheminement_ext_terrain_accidente",
      "cheminement_ext_plain_pied",
      "cheminement_ext_nombre_marches",
      "cheminement_ext_reperage_marches",
      "cheminement_ext_main_courante",
      "cheminement_ext_rampe",
      "cheminement_ext_ascenseur",
      "cheminement_ext_pente",
      "cheminement_ext_devers",
      "cheminement_ext_bande_guidage",
      "cheminement_ext_retrecissement",
    ],
    indent: 1,
  },
  {
    source: "cheminement_ext_plain_pied",
    values: ["False"],
    targets: [
      "cheminement_ext_nombre_marches",
      "cheminement_ext_reperage_marches",
      "cheminement_ext_main_courante",
      "cheminement_ext_rampe",
      "cheminement_ext_ascenseur",
    ],
    indent: 2,
  },

  // Entrée
  {
    source: "entree_vitree",
    values: ["True"],
    targets: ["entree_vitree_vitrophanie"],
    indent: 1,
  },
  {
    source: "entree_dispositif_appel",
    values: ["True"],
    targets: ["entree_dispositif_appel_type"],
    indent: 1,
  },
  {
    source: "entree_plain_pied",
    values: ["False"],
    targets: [
      "entree_marches",
      "entree_marches_reperage",
      "entree_marches_main_courante",
      "entree_marches_rampe",
      "entree_ascenseur",
    ],
    indent: 1,
  },
  {
    source: "entree_pmr",
    values: ["True"],
    targets: ["entree_pmr_informations"],
    indent: 1,
  },

  // Accueil
  {
    source: "accueil_equipements_malentendants_presence",
    values: ["True"],
    targets: ["accueil_equipements_malentendants"],
    indent: 1,
  },
  {
    source: "accueil_cheminement_plain_pied",
    values: ["False"],
    targets: [
      "accueil_cheminement_nombre_marches",
      "accueil_cheminement_reperage_marches",
      "accueil_cheminement_main_courante",
      "accueil_cheminement_rampe",
      "accueil_cheminement_ascenseur",
    ],
    indent: 1,
  },

  // Sanitaires
  {
    source: "sanitaires_presence",
    values: ["True"],
    targets: ["sanitaires_adaptes"],
    indent: 1,
  },

  // Labels
  // TODO

  // Publication: registre et conformité
  // a. afficher registre si gestionnaire
  {
    source: "user_type",
    values: ["gestionnaire", "admin"],
    targets: ["registre_url"],
    indent: 1,
  },
  // b. afficher conformité si administration
  {
    source: "user_type",
    values: ["admin"],
    targets: ["conformite"],
    indent: 1,
  },
];

function getFieldInputs(field) {
  const sourceSelector = "input[name=" + _config.inputNamePrefix + field + "]";
  return [].slice.call(document.querySelectorAll(sourceSelector));
}

function getValue(field) {
  const inputs = getFieldInputs(field);
  if (inputs.length === 0) {
    // field has not been found in the page, skipping
    return;
  }
  const selectedInput = inputs.filter(function (input) {
    return input.checked;
  })[0];
  if (!selectedInput) {
    return;
  }
  return selectedInput.value;
}

function resetField(field) {
  const radioNone = field.querySelector("input[type=radio][value='']");
  if (radioNone) {
    radioNone.click();
  }
  const textarea = field.querySelector("textarea");
  if (textarea) {
    textarea.value = "";
  }
  const textField = field.querySelector("input[type=text]");
  if (textField) {
    textField.value = "";
  }
  const urlField = field.querySelector("input[type=url]");
  if (urlField) {
    urlField.value = "";
  }
  const dateField = field.querySelector("input[type=date]");
  if (dateField) {
    dateField.value = "";
  }
  const numberInput = field.querySelector("input[type=number]");
  if (numberInput) {
    numberInput.value = "";
  }
}

function processTargets(rule, value) {
  rule.targets.forEach(function (target) {
    const el = document.querySelector((_config.fieldSelectorPrefix || "") + target);
    if (!el) {
      return;
    }
    if (rule.values.indexOf(value) !== -1) {
      el.classList.add("indented" + rule.indent);
      el.classList.remove("hidden");
    } else {
      el.classList.add("hidden");
      resetField(el);
    }
  });
}

function processRule(rule) {
  // grab the source field input elements
  const inputs = getFieldInputs(rule.source);
  if (inputs.length === 0) {
    // field has not been found in the page, skipping
    return;
  }

  inputs.forEach(function (input) {
    input.addEventListener("change", function (event) {
      processTargets(rule, event.target.value);
      rule.targets.forEach(function (child) {
        childRule = rules.filter((r) => r.source === child)[0];
        if (childRule) {
          processTargets(childRule, getValue(child));
        }
      });
    });
  });

  processTargets(rule, getValue(rule.source));
}

function run(config) {
  // XXX: check if this should be ran at all (check presence of form or fields in the page)
  for (let key in config || {}) {
    _config[key] = config[key];
  }

  rules.forEach(function (rule) {
    processRule(rule);
  });
}

export default { run };
