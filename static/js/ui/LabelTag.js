function LabelTag(root) {
  root.addEventListener('click', function (event) {
    let checkbox = document.getElementById(root.getAttribute('data-for-input'))
    checkbox.checked = !checkbox.checked
  })
}

export default LabelTag
