function ContentToggle(root) {
  const childrenContent = root.querySelector('.children-content')
  const btnToOpen = root.querySelector('.toggle-open')
  const btnToClose = root.querySelector('.toggle-close')

  if (!root || !childrenContent || !btnToOpen || !btnToClose) {
    return
  }

  btnToOpen.addEventListener('click', () => {
    childrenContent.classList.remove('fr-hidden')
    btnToOpen.classList.add('fr-hidden')
  })

  btnToClose.addEventListener('click', () => {
    childrenContent.classList.add('fr-hidden')
    btnToOpen.classList.remove('fr-hidden')
  })
}

export default ContentToggle
