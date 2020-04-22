window.addEventListener("DOMContentLoaded", function () {
  // leave if we're not in an Erp admin form page
  if (!document.querySelector("form#erp_form")) {
    return;
  }

  const rules = {
    // stationnement
    stationnement_pmr: {
      dependsOn: ["stationnement_presence"],
      when: true,
      indent: 1,
    },
    stationnement_ext_pmr: {
      dependsOn: ["stationnement_ext_presence"],
      when: true,
      indent: 1,
    },
    // presence d'un extérieur et cheminement
    cheminement_ext_plain_pied: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    cheminement_ext_nombre_marches: {
      dependsOn: ["cheminement_ext_plain_pied"],
      when: false,
      indent: 2,
    },
    cheminement_ext_reperage_marches: {
      dependsOn: ["cheminement_ext_plain_pied"],
      when: false,
      indent: 2,
    },
    cheminement_ext_main_courante: {
      dependsOn: ["cheminement_ext_plain_pied"],
      when: false,
      indent: 2,
    },
    cheminement_ext_rampe: {
      dependsOn: ["cheminement_ext_plain_pied"],
      when: false,
      indent: 2,
    },
    cheminement_ext_ascenseur: {
      dependsOn: ["cheminement_ext_plain_pied"],
      when: false,
      indent: 2,
    },
    cheminement_ext_pente: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    cheminement_ext_devers: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    cheminement_ext_bande_guidage: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    cheminement_ext_guidage_sonore: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    cheminement_ext_retrecissement: {
      dependsOn: ["cheminement_ext_presence"],
      when: true,
      indent: 1,
    },
    // entrée
    entree_vitree_vitrophanie: {
      dependsOn: ["entree_vitree"],
      when: true,
      indent: 1,
    },
    entree_marches: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_marches_reperage: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_marches_main_courante: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_marches_rampe: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_dispositif_appel: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_aide_humaine: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_ascenseur: {
      dependsOn: ["entree_plain_pied"],
      when: false,
      indent: 1,
    },
    entree_pmr_informations: {
      dependsOn: ["entree_pmr"],
      when: true,
      indent: 1,
    },
    // accueil
    accueil_cheminement_nombre_marches: {
      dependsOn: ["accueil_cheminement_plain_pied"],
      when: false,
      indent: 1,
    },
    accueil_cheminement_reperage_marches: {
      dependsOn: ["accueil_cheminement_plain_pied"],
      when: false,
      indent: 1,
    },
    accueil_cheminement_main_courante: {
      dependsOn: ["accueil_cheminement_plain_pied"],
      when: false,
      indent: 1,
    },
    accueil_cheminement_rampe: {
      dependsOn: ["accueil_cheminement_plain_pied"],
      when: false,
      indent: 1,
    },
    accueil_cheminement_ascenseur: {
      dependsOn: ["accueil_cheminement_plain_pied"],
      when: false,
      indent: 1,
    },
    // sanitaires
    sanitaires_adaptes: {
      dependsOn: ["sanitaires_presence"],
      when: true,
      indent: 1,
    },
  };

  function getFieldInputs(field) {
    const sourceSelector = "input[name=accessibilite-0-" + field + "]";
    return [].slice.call(document.querySelectorAll(sourceSelector));
  }

  function handleClick(field, style) {
    return function () {
      // reinit value for custom boolean radio choices
      const radioNone = field.querySelector("input[type=radio][value='']");
      if (radioNone) {
        radioNone.click();
      }
      // reinit value for textareas
      const textarea = field.querySelector("textarea");
      if (textarea) {
        textarea.value = "";
      }
      // reinit value for number inputs
      const numberInput = field.querySelector("input[type=number]");
      if (numberInput) {
        numberInput.value = "";
      }
      // apply style
      field.style.display = style;
    };
  }

  function condition(when, inputs, target) {
    if (when) {
      inputs[0].addEventListener("click", handleClick(target, "block"));
      inputs[1].addEventListener("click", handleClick(target, "none"));
      inputs[2].addEventListener("click", handleClick(target, "none"));
    } else {
      inputs[0].addEventListener("click", handleClick(target, "none"));
      inputs[1].addEventListener("click", handleClick(target, "block"));
      inputs[2].addEventListener("click", handleClick(target, "none"));
    }
  }

  function getValue(field) {
    const fieldInput = getFieldInputs(field).filter(function (input) {
      return input.checked;
    })[0];
    if (fieldInput.length === 0) {
      throw new Error("Couldn't find source input element for field: " + field);
    }
    return fieldInput.value;
  }

  function processRules() {
    // const triggers = {};
    for (let field in rules) {
      const { dependsOn, when, indent } = rules[field];
      const fieldElement = document.querySelector(".form-row.field-" + field);
      dependsOn.forEach(function (trigger) {
        // events
        const triggerInputs = getFieldInputs(trigger);
        condition(when, triggerInputs, fieldElement);
        // rendering
        const classes = fieldElement.classList;
        if (when && getValue(trigger) !== "True") {
          classes.add("hidden");
        } else if (!when && getValue(trigger) !== "False") {
          classes.add("hidden");
        }
        classes.add("indented" + indent);
      });
    }
  }

  processRules();
});
