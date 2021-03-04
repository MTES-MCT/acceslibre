function improveRequiredFieldsA11y() {
  // Django crispy forms asterisk a11y improvements
  $(".asteriskField").each((i, elem) => {
    $(elem).replaceWith('&nbsp;<small>(requis)</small><abbr class="asteriskField" title="(obligatoire)">*</abbr>');
  });
}

export default {
  improveRequiredFieldsA11y,
};
