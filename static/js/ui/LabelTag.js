function LabelTag(root) {
  root.addEventListener('click', function (event) {
    let checkbox = document.getElementById(root.getAttribute('for'))
    checkbox.checked = !checkbox.checked
  })
}

export default LabelTag
