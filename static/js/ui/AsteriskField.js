export default function AsteriskField(root) {
  root.outerHTML = `
    &nbsp;
    <small>(requis)</small>
    <abbr class="asteriskField" title="(obligatoire)">*</abbr>`;
}
