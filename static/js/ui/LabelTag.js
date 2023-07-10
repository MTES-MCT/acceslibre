function LabelTag(root) {
  root.addEventListener('click', function () {
    let checkbox = document.getElementById(root.getAttribute('data-for-input'))
    checkbox.checked = !checkbox.checked

    const event = new Event('labelClicked')
    document.dispatchEvent(event)
  })
}

export default LabelTag
