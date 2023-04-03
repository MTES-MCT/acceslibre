export default function AsteriskField(root) {
  root.outerHTML = `
    &nbsp;
    <small>(` + gettext("requis") + `)</small>`;
}
