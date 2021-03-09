import dom from "../dom";

function improveRequiredFieldsA11y() {
  // Django crispy forms asterisk a11y improvements
  dom.findAll(".asteriskField").forEach((elem) => {
    elem.outerHTML = '&nbsp;<small>(requis)</small><abbr class="asteriskField" title="(obligatoire)">*</abbr>';
  });
}

export default {
  improveRequiredFieldsA11y,
};
