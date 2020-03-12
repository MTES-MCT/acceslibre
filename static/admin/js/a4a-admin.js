window.addEventListener("DOMContentLoaded", function() {
  function handleClick(targets, style) {
    return function() {
      targets.forEach(function(target) {
        const field = document.querySelector(target);
        const radioNone = field.querySelector("input[type=radio][value='']");
        if (radioNone) {
          radioNone.click();
        }
        const textarea = field.querySelector("textarea");
        if (textarea) {
          textarea.value = "";
        }
        field.style.display = style;
      });
    };
  }
  function conditionals(source, targets) {
    const inputs = document.querySelectorAll(source);
    inputs[0].addEventListener("click", handleClick(targets, "block"));
    inputs[1].addEventListener("click", handleClick(targets, "none"));
    inputs[2].addEventListener("click", handleClick(targets, "none"));
  }

  conditionals("input[name=accessibilite-0-stationnement_presence]", [
    ".form-row.field-stationnement_pmr"
  ]);
  conditionals("input[name=accessibilite-0-stationnement_ext_presence]", [
    ".form-row.field-stationnement_ext_pmr"
  ]);

  conditionals("input[name=accessibilite-0-entree_pmr]", [
    ".form-row.field-entree_pmr_informations"
  ]);
});
