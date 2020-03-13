window.addEventListener("DOMContentLoaded", function() {
  const rules = {
    // Stationnement
    stationnement_presence: {
      condition: true,
      targets: ["stationnement_pmr"]
    },
    stationnement_ext_presence: {
      condition: true,
      targets: ["stationnement_ext_pmr"]
    },
    // Cheminement extérieur
    cheminement_ext_plain_pied: {
      condition: false,
      targets: [
        "cheminement_ext_nombre_marches",
        "cheminement_ext_reperage_marches",
        "cheminement_ext_main_courante",
        "cheminement_ext_rampe",
        "cheminement_ext_ascenseur"
      ]
    },
    // Entrée
    entree_vitree: {
      condition: true,
      targets: ["entree_vitree_vitrophanie"]
    },
    entree_plain_pied: {
      condition: false,
      targets: [
        "entree_marches",
        "entree_marches_reperage",
        "entree_marches_main_courante",
        "entree_marches_rampe",
        "entree_dispositif_appel",
        "entree_aide_humaine",
        "entree_ascenseur"
      ]
    },
    entree_pmr: {
      condition: true,
      targets: ["entree_pmr_informations"]
    },
    // Accueil
    accueil_cheminement_plain_pied: {
      condition: false,
      targets: [
        "accueil_cheminement_nombre_marches",
        "accueil_cheminement_reperage_marches",
        "accueil_cheminement_main_courante",
        "accueil_cheminement_rampe",
        "accueil_cheminement_ascenseur"
      ]
    },
    // Sanitaires
    sanitaires_presence: {
      condition: true,
      targets: ["sanitaires_adaptes"]
    }
  };

  function processRules() {
    for (let source in rules) {
      const rule = rules[source];
      const sourceSelector = "input[name=accessibilite-0-" + source + "]";
      const selectedSource = [].filter.call(
        document.querySelectorAll(sourceSelector),
        function(input) {
          return input.checked;
        }
      )[0];
      const targets = rule.targets.map(function(target) {
        return ".form-row.field-" + target;
      });
      // show/hide target fields
      targets.forEach(function(target) {
        const classes = document.querySelector(target).classList;
        classes.add("indented");
        if (rule.condition && selectedSource.value !== "True") {
          classes.add("hidden");
        }
      });
      // register conditional behaviors
      condition(rule.condition, sourceSelector, targets);
    }
  }

  processRules();

  function handleClick(targets, style) {
    return function() {
      targets.forEach(function(target) {
        const field = document.querySelector(target);
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
      });
    };
  }

  function condition(bool, source, targets) {
    const inputs = document.querySelectorAll(source);
    if (bool) {
      inputs[0].addEventListener("click", handleClick(targets, "block"));
      inputs[1].addEventListener("click", handleClick(targets, "none"));
      inputs[2].addEventListener("click", handleClick(targets, "none"));
    } else {
      inputs[0].addEventListener("click", handleClick(targets, "none"));
      inputs[1].addEventListener("click", handleClick(targets, "block"));
      inputs[2].addEventListener("click", handleClick(targets, "none"));
    }
  }
});
