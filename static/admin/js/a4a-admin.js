window.addEventListener("DOMContentLoaded", function () {
  // leave if we're not in an Erp admin form page
  if (!document.querySelector("form#erp_form")) {
    return;
  }

  window.a4aForms.run();
});
